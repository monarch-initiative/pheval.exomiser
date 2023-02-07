#!/usr/bin/python
import json
from pathlib import Path

import click
import pandas as pd
from pheval.post_processing.post_processing import (
    PhEvalGeneResult, PhEvalVariantResult, create_pheval_result,
    RankedPhEvalVariantResult, RankedPhEvalGeneResult
)
from pheval.utils.file_utils import files_with_suffix


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


def create_pheval_gene_result_from_exomiser(exomiser_json_result, ranking_method: str):
    pheval_gene_result = PhEvalGeneResultFromExomiserJsonCreator(
        exomiser_json_result, ranking_method
    ).extract_pheval_gene_requirements()
    return create_pheval_result(pheval_gene_result, ranking_method)


def create_variant_gene_result_from_exomiser(exomiser_json_result, ranking_method: str):
    pheval_variant_result = PhEvalVariantResultFromExomiserJsonCreator(
        exomiser_json_result, ranking_method
    ).extract_pheval_variant_requirements()
    return create_pheval_result(pheval_variant_result, ranking_method)


def write_pheval_gene_result(ranked_pheval_result: [RankedPhEvalGeneResult], output_dir: Path,
                             tool_result_path: Path) -> None:
    """Write ranked PhEval gene result to tsv."""
    ranked_result = pd.DataFrame([x.as_dict() for x in ranked_pheval_result])
    pheval_gene_output = ranked_result.loc[:, ["rank", "score", "gene_symbol", "gene_identifier"]]
    pheval_gene_output.to_csv(
        output_dir.joinpath("pheval_gene_results/" + tool_result_path.stem + "-pheval_gene_result.tsv"),
        sep="\t",
        index=False,
    )


def write_pheval_variant_result(ranked_pheval_result: [RankedPhEvalVariantResult],
                                output_dir: Path, tool_result_path: Path) -> None:
    """Write ranked PhEval variant result to tsv."""
    ranked_result = pd.DataFrame([x.as_dict() for x in ranked_pheval_result])
    pheval_variant_output = ranked_result.loc[:, ["rank", "score", "chromosome", "start", "end", "ref", "alt"]]
    pheval_variant_output.to_csv(
        output_dir.joinpath("pheval_variant_results/" + tool_result_path.stem + "-pheval_variant_result.tsv"),
        sep="\t",
        index=False,
    )


def create_standardised_results(results_dir: Path, output_dir: Path, ranking_method: str) -> None:
    """Write standardised gene and variant results from default Exomiser json output."""
    output_dir.joinpath("pheval_gene_results/").mkdir(exist_ok=True)
    output_dir.joinpath("pheval_variant_results/").mkdir(exist_ok=True)
    for result in files_with_suffix(results_dir, ".json"):
        exomiser_result = read_exomiser_json_result(result)
        pheval_gene_result = create_pheval_gene_result_from_exomiser(exomiser_result, ranking_method)
        write_pheval_gene_result(pheval_gene_result, output_dir, result)
        pheval_variant_result = create_variant_gene_result_from_exomiser(exomiser_result, ranking_method)
        write_pheval_variant_result(pheval_variant_result, output_dir, result)


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
    output_dir.mkdir(exist_ok=True, parents=True)
    create_standardised_results(results_dir, output_dir, ranking_method)
