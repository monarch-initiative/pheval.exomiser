#!/usr/bin/python
import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path

import click
import pandas as pd
from pheval.post_processing.post_processing import PhEvalGeneResult, PhEvalVariantResult
from pheval.utils.file_utils import files_with_suffix
from pheval.utils.phenopacket_utils import GenomicVariant


def read_exomiser_json_result(exomiser_result_path: Path) -> dict:
    """Load Exomiser json result."""
    with open(exomiser_result_path) as exomiser_json_result:
        exomiser_result = json.load(exomiser_json_result)
    exomiser_json_result.close()
    return exomiser_result


class PhEvalGeneResultFromExomiserJsonCreator:

    def __init__(self, exomiser_json_result: [dict], ranking_method: str):
        self.exomiser_json_result = exomiser_json_result
        self.ranking_method = ranking_method

    @staticmethod
    def find_gene_symbol(result_entry: dict) -> str:
        return result_entry["geneSymbol"]

    @staticmethod
    def find_gene_identifier(result_entry: dict) -> str:
        return result_entry["geneIdentifier"]["geneId"]

    def find_relevant_score(self, result_entry: dict):
        return round(result_entry[self.ranking_method], 4)

    def extract_pheval_gene_requirements(self):
        simplified_exomiser_result = []
        for result_entry in self.exomiser_json_result:
            if self.ranking_method in result_entry:
                simplified_exomiser_result.append(PhEvalGeneResult(gene_symbol=self.find_gene_symbol(result_entry),
                                                                   gene_identifier=self.find_gene_identifier(
                                                                       result_entry),
                                                                   score=self.find_relevant_score(result_entry)))

        return simplified_exomiser_result


class PhEvalVariantResultFromExomiserJsonCreator:
    def __init__(self, exomiser_json_result: [dict], ranking_method: str):
        self.exomiser_json_result = exomiser_json_result
        self.ranking_method = ranking_method

    @staticmethod
    def find_chromosome(result_entry):
        return result_entry["contigName"]

    @staticmethod
    def find_start_pos(result_entry):
        return result_entry["start"]

    @staticmethod
    def find_end_pos(result_entry):
        return result_entry["end"]

    @staticmethod
    def find_ref(result_entry):
        return result_entry["ref"]

    @staticmethod
    def find_alt(result_entry):
        return result_entry["alt"]

    def find_relevant_score(self, result_entry):
        return round(result_entry[self.ranking_method], 4)

    def extract_pheval_variant_requirements(self):
        simplified_exomiser_result = []
        for result_entry in self.exomiser_json_result:
            for gene_hit in result_entry["geneScores"]:
                if self.ranking_method in result_entry:
                    if "contributingVariants" in gene_hit:
                        score = self.find_relevant_score(result_entry)
                        for cv in gene_hit["contributingVariants"]:
                            simplified_exomiser_result.append(PhEvalVariantResult(chromosome=self.find_chromosome(cv),
                                                                                  start=self.find_start_pos(cv),
                                                                                  end=self.find_end_pos(cv),
                                                                                  ref=self.find_ref(cv),
                                                                                  alt=self.find_alt(cv),
                                                                                  score=score))
        return simplified_exomiser_result



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
