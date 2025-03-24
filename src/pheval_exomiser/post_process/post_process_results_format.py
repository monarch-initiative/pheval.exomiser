import uuid
from enum import Enum
from pathlib import Path

import click
import polars as pl
from pheval.post_processing.post_processing import (
    SortOrder,
    generate_disease_result,
    generate_gene_result,
    generate_variant_result,
)
from pheval.utils.file_utils import files_with_suffix


class ModeOfInheritance(Enum):
    AUTOSOMAL_DOMINANT = 1
    AUTOSOMAL_RECESSIVE = 2
    X_DOMINANT = 1
    X_RECESSIVE = 2
    MITOCHONDRIAL = 3


def trim_exomiser_result_filename(exomiser_result_path: Path) -> Path:
    """Trim suffix appended to Exomiser JSON result path."""
    return Path(str(exomiser_result_path.name).replace("-exomiser", ""))


def extract_gene_results_from_json(
    exomiser_json_result: pl.DataFrame, score_name: str
) -> pl.DataFrame:
    return exomiser_json_result.select(
        [
            pl.col("geneSymbol").alias("gene_symbol"),
            pl.col("geneIdentifier").struct.field("geneId").alias("gene_identifier"),
            pl.col(score_name).fill_null(0).round(4).alias("score"),
        ]
    ).drop_nulls()


def extract_disease_results_from_json(exomiser_json_result: pl.DataFrame) -> pl.DataFrame:
    return (
        exomiser_json_result.select(
            [
                pl.col("priorityResults")
                .struct.field("HIPHIVE_PRIORITY")
                .struct.field("diseaseMatches")
            ]
        )
        .explode("diseaseMatches")
        .unnest("diseaseMatches")
        .unnest("model")
        .select([pl.col("diseaseId").alias("disease_identifier"), pl.col("score").round(4)])
        .drop_nulls()
    )


def extract_variant_results_from_json(
    exomiser_json_result: pl.DataFrame, score_name: str
) -> pl.DataFrame:
    return (
        exomiser_json_result.filter(pl.col("geneScores").is_not_null())
        .select([pl.col("geneScores"), pl.col(score_name).alias("score"), pl.col("geneSymbol")])
        .explode("geneScores")
        .unnest("geneScores")
        .filter(pl.col("contributingVariants").is_not_null())
        .explode("contributingVariants")
        .with_columns(
            [
                pl.col("contributingVariants").struct.field("contigName").alias("chrom"),
                pl.col("contributingVariants").struct.field("start"),
                pl.col("contributingVariants").struct.field("end"),
                pl.col("contributingVariants").struct.field("ref"),
                pl.col("contributingVariants")
                .struct.field("alt")
                .fill_null("")
                .str.strip_chars("<>")
                .alias("alt"),
                pl.col("modeOfInheritance")
                .map_elements(lambda moi: ModeOfInheritance[moi].value, return_dtype=pl.Int8)
                .alias("moi_enum"),
            ]
        )
        .with_columns(
            [
                (pl.col("moi_enum") == 2).alias("is_recessive"),
                pl.when(pl.col("moi_enum") == 2)
                .then(
                    pl.format(
                        "recessive|{}|{}|{}",
                        pl.col("geneSymbol"),
                        pl.col("score"),
                        pl.col("moi_enum"),
                    )
                )
                .otherwise(
                    pl.format(
                        "dominant|{}|{}|{}|{}|{}|{}",
                        pl.col("chrom"),
                        pl.col("start"),
                        pl.col("end"),
                        pl.col("ref"),
                        pl.col("alt"),
                        pl.col("score"),
                    )
                )
                .alias("group_key"),
            ]
        )
        .with_columns(
            [
                pl.col("group_key")
                .rank("dense")
                .cast(pl.UInt32)
                .map_elements(
                    lambda i: str(uuid.uuid5(uuid.NAMESPACE_DNS, str(i))), return_dtype=pl.String
                )
                .alias("grouping_id")
            ]
        )
        .select(
            ["chrom", "start", "end", "ref", "alt", "score", "modeOfInheritance", "grouping_id"]
        )
    )


def create_standardised_results(
    result_dir: Path,
    output_dir: Path,
    phenopacket_dir: Path,
    score_name: str,
    sort_order: str,
    gene_analysis: bool,
    disease_analysis: bool,
    variant_analysis: bool,
):
    sort_order = SortOrder.ASCENDING if sort_order.lower() == "ascending" else SortOrder.DESCENDING
    for exomiser_json_result_path in files_with_suffix(result_dir, ".json"):
        exomiser_json_result = pl.read_json(exomiser_json_result_path)
        if gene_analysis:
            gene_results = extract_gene_results_from_json(exomiser_json_result, score_name)
            generate_gene_result(
                results=gene_results,
                sort_order=sort_order,
                output_dir=output_dir,
                result_path=trim_exomiser_result_filename(exomiser_json_result_path),
                phenopacket_dir=phenopacket_dir,
            )
        if disease_analysis:
            disease_results = extract_disease_results_from_json(exomiser_json_result)
            generate_disease_result(
                results=disease_results,
                sort_order=sort_order,
                output_dir=output_dir,
                result_path=trim_exomiser_result_filename(exomiser_json_result_path),
                phenopacket_dir=phenopacket_dir,
            )

        if variant_analysis:
            variant_results = extract_variant_results_from_json(exomiser_json_result, score_name)
            generate_variant_result(
                results=variant_results,
                sort_order=sort_order,
                output_dir=output_dir,
                result_path=trim_exomiser_result_filename(exomiser_json_result_path),
                phenopacket_dir=phenopacket_dir,
            )


@click.command()
@click.option(
    "--output-dir",
    "-o",
    required=True,
    metavar="PATH",
    help="Output directory for standardised results.",
    type=Path,
)
@click.option(
    "--results-dir",
    "-R",
    required=True,
    metavar="DIRECTORY",
    help="Full path to Exomiser results directory to be standardised.",
    type=Path,
)
@click.option(
    "--phenopacket-dir",
    "-p",
    required=True,
    metavar="DIRECTORY",
    help="Full path to phenopacket dir used to generate the raw results.",
    type=Path,
)
@click.option(
    "--score-name",
    "-s",
    required=True,
    help="Score name to extract from results.",
    type=click.Choice(["combinedScore", "priorityScore", "variantScore", "pValue"]),
    default="combinedScore",
    show_default=True,
)
@click.option(
    "--sort-order",
    "-so",
    required=True,
    help="Ordering of results for ranking.",
    type=click.Choice(["ascending", "descending"]),
    default="descending",
    show_default=True,
)
@click.option(
    "--gene-analysis/--no-gene-analysis",
    type=bool,
    default=False,
    help="Specify whether to create PhEval gene results.",
)
@click.option(
    "--variant-analysis/--no-variant-analysis",
    type=bool,
    default=False,
    help="Specify whether to create PhEval variant results.",
)
@click.option(
    "--disease-analysis/--no-disease-analysis",
    type=bool,
    default=False,
    help="Specify whether to create PhEval disease results.",
)
def post_process_exomiser_results(
    output_dir: Path,
    results_dir: Path,
    phenopacket_dir: Path,
    score_name: str,
    sort_order: str,
    gene_analysis: bool,
    variant_analysis: bool,
    disease_analysis: bool,
):
    """Post-process Exomiser json results into PhEval gene and variant outputs."""
    (
        output_dir.joinpath("pheval_gene_results").mkdir(parents=True, exist_ok=True)
        if gene_analysis
        else None
    )
    (
        output_dir.joinpath("pheval_variant_results").mkdir(parents=True, exist_ok=True)
        if variant_analysis
        else None
    )
    (
        output_dir.joinpath("pheval_disease_results").mkdir(parents=True, exist_ok=True)
        if disease_analysis
        else None
    )
    create_standardised_results(
        result_dir=results_dir,
        output_dir=output_dir,
        phenopacket_dir=phenopacket_dir,
        score_name=score_name,
        sort_order=sort_order,
        variant_analysis=variant_analysis,
        gene_analysis=gene_analysis,
        disease_analysis=disease_analysis,
    )
