#!/usr/bin/python
import json
from pathlib import Path

import click
from pheval.post_processing.post_processing import (
    PhEvalGeneResult,
    PhEvalVariantResult,
    generate_pheval_result,
)
from pheval.runners.runner import PhEvalRunner
from pheval.utils.file_utils import files_with_suffix


def read_exomiser_json_result(exomiser_result_path: Path) -> dict:
    """Load Exomiser json result."""
    with open(exomiser_result_path) as exomiser_json_result:
        exomiser_result = json.load(exomiser_json_result)
    exomiser_json_result.close()
    return exomiser_result


def trim_exomiser_result_filename(exomiser_result_path: Path) -> Path:
    """Trim suffix appended to Exomiser JSON result path."""
    return Path(str(exomiser_result_path).replace("-exomiser", ""))


class PhEvalGeneResultFromExomiserJsonCreator:
    def __init__(self, exomiser_json_result: [dict], score_name: str):
        self.exomiser_json_result = exomiser_json_result
        self.score_name = score_name

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
        return round(result_entry[self.score_name], 4)

    def extract_pheval_gene_requirements(self) -> [PhEvalGeneResult]:
        """Extract data required to produce PhEval gene output."""
        simplified_exomiser_result = []
        for result_entry in self.exomiser_json_result:
            if self.score_name in result_entry:
                simplified_exomiser_result.append(
                    PhEvalGeneResult(
                        gene_symbol=self._find_gene_symbol(result_entry),
                        gene_identifier=self._find_gene_identifier(result_entry),
                        score=self._find_relevant_score(result_entry),
                    )
                )

        return simplified_exomiser_result


class PhEvalVariantResultFromExomiserJsonCreator:
    def __init__(self, exomiser_json_result: [dict], score_name: str):
        self.exomiser_json_result = exomiser_json_result
        self.score_name = score_name

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
        return round(result_entry[self.score_name], 4)

    def extract_pheval_variant_requirements(self) -> [PhEvalVariantResult]:
        """Extract data required to produce PhEval variant output."""
        simplified_exomiser_result = []
        for result_entry in self.exomiser_json_result:
            for gene_hit in result_entry["geneScores"]:
                if self.score_name in result_entry:
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


def create_standardised_results(
        results_dir: Path, runner: PhEvalRunner, score_name: str, sort_order: str, phenotype_only: bool
) -> None:
    """Write standardised gene and variant results from default Exomiser json output."""
    for result in files_with_suffix(results_dir, ".json"):
        exomiser_result = read_exomiser_json_result(result)
        pheval_gene_requirements = PhEvalGeneResultFromExomiserJsonCreator(
            exomiser_result, score_name
        ).extract_pheval_gene_requirements()
        generate_pheval_result(pheval_result=pheval_gene_requirements,
                               sort_order_str=sort_order,
                               output_dir=results_dir,
                               tool_result_path=runner.output_dir)
        if not phenotype_only:
            pheval_variant_requirements = PhEvalVariantResultFromExomiserJsonCreator(
                exomiser_result, score_name
            ).extract_pheval_variant_requirements()
            generate_pheval_result(pheval_result=pheval_variant_requirements,
                                   sort_order_str=sort_order,
                                   output_dir=results_dir,
                                   tool_result_path=runner.output_dir)


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
    "--sort-order",
    "-so",
    required=True,
    help="Ordering of results for ranking.",
    type=click.Choice(["ascending", "descending"]),
    default="descending",
    show_default=True,
)
@click.option(
    "--phenotype-only/--variant-analysis",
    type=bool,
    default=False,
    help="Specify if Exomiser was run with phenotype-only analysis.",
)
def post_process_exomiser_results(
        output_dir: Path, results_dir: Path, score_name: str, sort_order: str, phenotype_only: bool
):
    """Post-process Exomiser json results into PhEval gene and variant outputs."""
    output_dir.joinpath("pheval_gene_results").mkdir(parents=True, exist_ok=True)
    output_dir.joinpath("pheval_variant_results").mkdir(
        parents=True, exist_ok=True
    ) if not phenotype_only else None
    create_standardised_results(results_dir, output_dir, score_name, sort_order, phenotype_only)
