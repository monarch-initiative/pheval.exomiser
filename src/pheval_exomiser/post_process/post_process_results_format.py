#!/usr/bin/python
import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path

import click
import pandas as pd
from pheval.utils.file_utils import files_with_suffix
from pheval.utils.phenopacket_utils import VariantData


@dataclass
class SimplifiedExomiserGeneResult:
    """A simplified gene result format from Exomiser json."""

    exomiser_result: dict
    simplified_exomiser_gene_result: list
    ranking_method: str

    def add_gene_record(self) -> dict:
        """Add the gene and gene identifier record to simplified result format."""
        return {
            "gene_symbol": self.exomiser_result["geneSymbol"],
            "gene_identifier": self.exomiser_result["geneIdentifier"]["geneId"],
        }

    def add_ranking_score(self, simplified_result_entry: dict) -> dict:
        """Add the ranking score to simplified result format."""
        simplified_result_entry["score"] = round(self.exomiser_result[self.ranking_method], 4)
        return simplified_result_entry

    def create_simplified_gene_result(self) -> [dict]:
        """Create a simplified Exomiser Gene result."""
        self.simplified_exomiser_gene_result.append(self.add_ranking_score(self.add_gene_record()))
        return self.simplified_exomiser_gene_result


@dataclass
class SimplifiedExomiserVariantResult:
    """A simplified variant result format from Exomiser json."""

    exomiser_result: dict
    simplified_exomiser_variant_result: list
    ranking_method: str
    ranking_score: float

    def create_simplified_variant_result(self) -> [dict]:
        """Add data for contributing variants to simplified result format."""
        for cv in self.exomiser_result["contributingVariants"]:
            self.simplified_exomiser_variant_result.append(
                {
                    "variant": dataclasses.asdict(
                        VariantData(
                            cv["contigName"],
                            cv["start"],
                            cv["ref"],
                            cv["alt"],
                            self.exomiser_result["geneIdentifier"]["geneSymbol"],
                        )
                    ),
                    "score": self.ranking_score,
                }
            )
        return self.simplified_exomiser_variant_result


class RankExomiserResult:
    """Add ranks to simplified Exomiser gene/variant results - taking care of ex-aequo scores."""

    def __init__(self, simplified_exomiser_result: [dict], ranking_method: str):
        self.simplified_exomiser_result = simplified_exomiser_result
        self.ranking_method = ranking_method

    def sort_exomiser_result(self) -> [dict]:
        """Sorts simplified Exomiser result by ranking method in decreasing order."""
        return sorted(
            self.simplified_exomiser_result,
            key=lambda d: d["score"],
            reverse=True,
        )

    def sort_exomiser_result_pvalue(self) -> [dict]:
        """Sort simplified Exomiser result by pvalue, most significant value first."""
        return sorted(
            self.simplified_exomiser_result,
            key=lambda d: d["score"],
            reverse=False,
        )

    def rank_results(self) -> [dict]:
        """Add ranks to the Exomiser results, equal scores are given the same rank e.g., 1,1,3."""
        sorted_exomiser_result = (
            self.sort_exomiser_result_pvalue()
            if self.ranking_method == "pValue"
            else self.sort_exomiser_result()
        )
        rank, count, previous = 0, 0, None
        for exomiser_result in sorted_exomiser_result:
            count += 1
            if exomiser_result["score"] != previous:
                rank += count
                previous = exomiser_result["score"]
                count = 0
            exomiser_result["rank"] = rank
        return sorted_exomiser_result


def read_exomiser_json_result(exomiser_result_path: Path) -> dict:
    """Load Exomiser json result."""
    with open(exomiser_result_path) as exomiser_json_result:
        exomiser_result = json.load(exomiser_json_result)
    exomiser_json_result.close()
    return exomiser_result


class StandardiseExomiserResult:
    """Standardise Exomiser output into simplified gene and variant results for analysis."""

    def __init__(self, exomiser_json_result: [dict], ranking_method: str):
        self.exomiser_json_result = exomiser_json_result
        self.ranking_method = ranking_method

    def simplify_gene_result(self) -> [dict]:
        """Simplify Exomiser json output into gene results."""
        simplified_exomiser_result = []
        for result in self.exomiser_json_result:
            if self.ranking_method in result:
                simplified_exomiser_result = SimplifiedExomiserGeneResult(
                    result, simplified_exomiser_result, self.ranking_method
                ).create_simplified_gene_result()
        return simplified_exomiser_result

    def simplify_variant_result(self) -> [dict]:
        """Simplify Exomiser json output into variant results."""
        simplified_exomiser_result = []
        for result in self.exomiser_json_result:
            for gene_hit in result["geneScores"]:
                if self.ranking_method in gene_hit:
                    if "contributingVariants" in gene_hit:
                        simplified_exomiser_result = SimplifiedExomiserVariantResult(
                            gene_hit,
                            simplified_exomiser_result,
                            self.ranking_method,
                            round(result[self.ranking_method], 4),
                        ).create_simplified_variant_result()
        return simplified_exomiser_result

    def standardise_gene_result(self) -> [dict]:
        """Standardise Exomiser json to gene results for analysis."""
        simplified_exomiser_result = self.simplify_gene_result()
        return RankExomiserResult(simplified_exomiser_result, self.ranking_method).rank_results()

    def standardise_variant_result(self) -> [dict]:
        """Standardise Exomiser json to gene results for analysis."""
        simplified_exomiser_result = self.simplify_variant_result()
        return RankExomiserResult(simplified_exomiser_result, self.ranking_method).rank_results()


def create_standardised_results(results_dir: Path, output_dir: Path, ranking_method) -> None:
    """Write standardised gene and variant results from default Exomiser json output."""
    try:
        output_dir.joinpath("pheval_gene_results/").mkdir()
        output_dir.joinpath("pheval_variant_results/").mkdir()
    except FileExistsError:
        pass
    for result in files_with_suffix(results_dir, ".json"):
        exomiser_result = read_exomiser_json_result(result)
        standardised_gene_result = StandardiseExomiserResult(
            exomiser_result, ranking_method
        ).standardise_gene_result()
        standardised_variant_result = StandardiseExomiserResult(
            exomiser_result, ranking_method
        ).standardise_variant_result()
        gene_df = pd.DataFrame(standardised_gene_result)
        gene_df = gene_df.loc[:, ["rank", "score", "gene_symbol", "gene_identifier"]]
        gene_df.to_csv(
            output_dir.joinpath("pheval_gene_results/" + result.stem + "-pheval_gene_result.tsv"),
            sep="\t",
            index=False,
        )
        variant_df = pd.DataFrame(standardised_variant_result)
        variant_df = variant_df.drop("variant", axis=1).join(variant_df.variant.apply(pd.Series))
        variant_df = variant_df.loc[:, ["rank", "score", "chrom", "pos", "ref", "alt", "gene"]]
        variant_df.to_csv(
            output_dir.joinpath(
                "pheval_variant_results/" + result.stem + "-pheval_variant_result.tsv"
            ),
            sep="\t",
            index=False,
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
    "--ranking-method",
    "-r",
    required=True,
    help="ranking method",
    type=click.Choice(["combinedScore", "priorityScore", "variantScore", "pValue"]),
    default="combinedScore",
    show_default=True,
)
def post_process_exomiser_results(output_dir: Path, results_dir: Path, ranking_method):
    """Post-process Exomiser json results into standardised gene and variant outputs."""
    try:
        output_dir.mkdir()
    except FileExistsError:
        pass
    create_standardised_results(results_dir, output_dir, ranking_method)
