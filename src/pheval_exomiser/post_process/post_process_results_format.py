#!/usr/bin/python
import json
from pathlib import Path

import click
from pheval.post_processing.post_processing import (
    PhEvalGeneResult,
    PhEvalVariantResult,
    RankedPhEvalGeneResult,
    RankedPhEvalVariantResult,
    create_pheval_result,
    write_pheval_gene_result,
    write_pheval_variant_result,
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
    def _find_gene_symbol(result_entry: dict) -> str:
        """Return gene symbol from Exomiser result entry."""
        return result_entry["geneSymbol"]

    @staticmethod
    def _find_gene_identifier(result_entry: dict) -> str:
        """Return ensembl gene identifier from Exomiser result entry."""
        return result_entry["geneIdentifier"]["geneId"]

    def _find_relevant_score(self, result_entry: dict):
        """Return score from Exomiser result entry."""
        return round(result_entry[self.ranking_method], 4)

    def extract_pheval_gene_requirements(self) -> [PhEvalGeneResult]:
        """Extract data required to produce PhEval gene output."""
        simplified_exomiser_result = []
        for result_entry in self.exomiser_json_result:
            if self.ranking_method in result_entry:
                simplified_exomiser_result.append(
                    PhEvalGeneResult(
                        gene_symbol=self._find_gene_symbol(result_entry),
                        gene_identifier=self._find_gene_identifier(result_entry),
                        score=self._find_relevant_score(result_entry),
                    )
                )

        return simplified_exomiser_result


class PhEvalVariantResultFromExomiserJsonCreator:
    def __init__(self, exomiser_json_result: [dict], ranking_method: str):
        self.exomiser_json_result = exomiser_json_result
        self.ranking_method = ranking_method

    @staticmethod
    def _find_chromosome(result_entry: dict) -> str:
        """Return chromosome from Exomiser result entry."""
        return result_entry["contigName"]

    @staticmethod
    def _find_start_pos(result_entry: dict) -> int:
        """Return start position from Exomiser result entry."""
        return result_entry["start"]

    @staticmethod
    def _find_end_pos(result_entry: dict) -> int:
        """Return end position from Exomiser result entry."""
        return result_entry["end"]

    @staticmethod
    def _find_ref(result_entry: dict) -> str:
        """Return reference allele from Exomiser result entry."""
        return result_entry["ref"]

    @staticmethod
    def _find_alt(result_entry: dict) -> str:
        """Return alternate allele from Exomiser result entry."""
        return result_entry["alt"]

    def _find_relevant_score(self, result_entry) -> float:
        """Return score from Exomiser result entry."""
        return round(result_entry[self.ranking_method], 4)

    def extract_pheval_variant_requirements(self) -> [PhEvalVariantResult]:
        """Extract data required to produce PhEval variant output."""
        simplified_exomiser_result = []
        for result_entry in self.exomiser_json_result:
            for gene_hit in result_entry["geneScores"]:
                if self.ranking_method in result_entry:
                    if "contributingVariants" in gene_hit:
                        score = self._find_relevant_score(result_entry)
                        for cv in gene_hit["contributingVariants"]:
                            simplified_exomiser_result.append(
                                PhEvalVariantResult(
                                    chromosome=self._find_chromosome(cv),
                                    start=self._find_start_pos(cv),
                                    end=self._find_end_pos(cv),
                                    ref=self._find_ref(cv),
                                    alt=self._find_alt(cv),
                                    score=score,
                                )
                            )
        return simplified_exomiser_result


def create_pheval_gene_result_from_exomiser(
    exomiser_json_result: [dict], score_name: str, score_order: str,
) -> [RankedPhEvalGeneResult]:
    """Create ranked PhEval gene result from Exomiser json."""
    pheval_gene_result = PhEvalGeneResultFromExomiserJsonCreator(
        exomiser_json_result, score_name
    ).extract_pheval_gene_requirements()
    return create_pheval_result(pheval_gene_result, score_order)


def create_variant_gene_result_from_exomiser(
    exomiser_json_result: [dict], score_name: str, score_order: str,
) -> [RankedPhEvalVariantResult]:
    """Create ranked PhEval variant result from Exomiser json."""
    pheval_variant_result = PhEvalVariantResultFromExomiserJsonCreator(
        exomiser_json_result, score_name
    ).extract_pheval_variant_requirements()
    return create_pheval_result(pheval_variant_result, score_order)


def create_standardised_results(results_dir: Path, output_dir: Path, score_name: str, score_order: str) -> None:
    """Write standardised gene and variant results from default Exomiser json output."""
    output_dir.joinpath("pheval_gene_results/").mkdir(exist_ok=True, parents=True)
    output_dir.joinpath("pheval_variant_results/").mkdir(exist_ok=True, parents=True)
    for result in files_with_suffix(results_dir, ".json"):
        exomiser_result = read_exomiser_json_result(result)
        pheval_gene_result = create_pheval_gene_result_from_exomiser(
            exomiser_result, score_name, score_order
        )
        write_pheval_gene_result(pheval_gene_result, output_dir, result)
        pheval_variant_result = create_variant_gene_result_from_exomiser(
            exomiser_result, score_name, score_order
        )
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
    "--score-name",
    "-s",
    required=True,
    help="Score name to extract from results.",
    type=click.Choice(["combinedScore", "priorityScore", "variantScore", "pValue"]),
    default="combinedScore",
    show_default=True,
)
@click.option(
    "--score-order",
    "-so",
    required=True,
    help="Ordering of results for ranking.",
    type=click.Choice(["ascending", "descending"]),
    default="descending",
    show_default=True,
)
def post_process_exomiser_results(output_dir: Path, results_dir: Path, score_name: str, score_order: str):
    """Post-process Exomiser json results into PhEval gene and variant outputs."""
    output_dir.mkdir(exist_ok=True, parents=True)
    create_standardised_results(results_dir, output_dir, score_name, score_order)
