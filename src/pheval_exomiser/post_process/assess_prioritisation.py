#!/usr/bin/python

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import click
from pheval.post_process.post_processing_analysis import (
    GenePrioritisationResultData,
    PrioritisationRankRecorder,
    RankComparisonGenerator,
    RankStats,
    RankStatsWriter,
    VariantPrioritisationResultData,
)
from pheval.utils.file_utils import all_files, files_with_suffix, obtain_closest_file_name
from pheval.utils.phenopacket_utils import PhenopacketUtil, VariantData, phenopacket_reader


@dataclass
class SimplifiedExomiserResult:
    exomiser_result: dict
    identifier: str
    simplified_exomiser_result: defaultdict
    ranking_method: str

    def add_gene(self) -> None:
        """Adds the gene and gene identifier to simplified result format."""
        self.simplified_exomiser_result[self.identifier]["geneSymbol"] = self.exomiser_result[
            "geneIdentifier"
        ]["geneSymbol"]
        self.simplified_exomiser_result[self.identifier]["geneIdentifier"] = self.exomiser_result[
            "geneIdentifier"
        ]["geneId"]

    def add_ranking_method_val(self) -> None:
        """Adds score for specified ranking method to simplified result format."""
        self.simplified_exomiser_result[self.identifier][self.ranking_method] = round(
            self.exomiser_result[self.ranking_method], 4
        )

    # def add_combined_score(self):
    #     try:
    #         self.output_results[self.identifier]["combinedScore"] = round(self.original_results["combinedScore"], 4)
    #     except KeyError:
    #         self.output_results[self.identifier]["combinedScore"] = "N/A"
    #
    # def add_phenotype_score(self):
    #     try:
    #         self.output_results[self.identifier]["phenotypeScore"] = round(self.original_results["phenotypeScore"], 4)
    #     except KeyError:
    #         self.output_results[self.identifier]["phenotypeScore"] = "N/A"
    #
    # def add_variant_score(self):
    #     try:
    #         self.output_results[self.identifier]["variantScore"] = round(self.original_results["variantScore"], 4)
    #     except KeyError:
    #         self.output_results[self.identifier]["variantScore"] = "N/A"
    #
    # def add_pvalue_score(self):
    #     try:
    #         self.output_results[self.identifier]["pValue"] = round(self.original_results["pValue"], 4)
    #     except KeyError:
    #         self.output_results[self.identifier]["pValue"] = "N/A"

    def add_moi(self) -> None:
        """Adds mode of inheritance to simplified result format."""
        self.simplified_exomiser_result[self.identifier][
            "modeOfInheritance"
        ] = self.exomiser_result["modeOfInheritance"]

    def add_contributing_variants(self) -> None:
        """Adds data for contributing variants to simplified result format."""
        variant = []
        for cv in self.exomiser_result["contributingVariants"]:
            variant.append(
                VariantData(
                    cv["contigName"],
                    cv["start"],
                    cv["ref"],
                    cv["alt"],
                    self.exomiser_result["geneIdentifier"]["geneSymbol"],
                )
            )
        self.simplified_exomiser_result[self.identifier]["contributingVariants"] = variant

    def create_simplified_result(self) -> dict:
        """Creates simplified exomiser json result format."""
        self.add_gene()
        # self.add_combined_score()
        # self.add_phenotype_score()
        # self.add_variant_score()
        # self.add_pvalue_score()
        self.add_ranking_method_val()
        self.add_moi()
        self.add_contributing_variants()
        return self.simplified_exomiser_result


class RankExomiserResult:
    def __init__(self, simplified_exomiser_result: dict, ranking_method: str):
        self.simplified_exomiser_result = simplified_exomiser_result
        self.ranking_method = ranking_method

    def sort_exomiser_result(self) -> list:
        """Sorts simplified Exomiser result by ranking method in decreasing order."""
        return sorted(
            self.simplified_exomiser_result.items(),
            key=lambda x: x[1][self.ranking_method],
            reverse=True,
        )

    def sort_exomiser_result_pvalue(self) -> list:
        """Sorts simplified Exomiser result by pvalue, most significant value first."""
        return sorted(
            self.simplified_exomiser_result.items(),
            key=lambda x: x[1][self.ranking_method],
            reverse=False,
        )

    def rank_results(self) -> dict:
        """Adds ranks to the Exomiser results, equal scores are given the same rank e.g., 1,1,3."""
        sorted_exomiser_result = (
            self.sort_exomiser_result_pvalue()
            if self.ranking_method == "pValue"
            else self.sort_exomiser_result()
        )
        rank, count, previous, result = 0, 0, None, {}
        for key, info in sorted_exomiser_result:
            count += 1
            if info[self.ranking_method] != previous:
                rank += count
                previous = info[self.ranking_method]
                count = 0
            result[key] = rank
        ranked_exomiser_result = dict(sorted_exomiser_result)
        for key, value in result.items():
            ranked_exomiser_result[key]["rank"] = value
        return ranked_exomiser_result


def read_exomiser_json_result(exomiser_result_path: Path) -> dict:
    """Loads Exomiser json result."""
    with open(exomiser_result_path) as exomiser_json_result:
        exomiser_result = json.load(exomiser_json_result)
    exomiser_json_result.close()
    return exomiser_result


class StandardiseExomiserResult:
    def __init__(self, exomiser_json_result, ranking_method: str):
        self.exomiser_json_result = exomiser_json_result
        self.ranking_method = ranking_method

    def simplify_exomiser_result(self) -> dict:
        """Creates simplified format of Exomiser json result."""
        simplified_exomiser_result = defaultdict(dict)
        for result in self.exomiser_json_result:
            for gene_hit in result["geneScores"]:
                if self.ranking_method in gene_hit:
                    if "contributingVariants" in gene_hit:
                        simplified_exomiser_result = SimplifiedExomiserResult(
                            gene_hit,
                            gene_hit["geneIdentifier"]["geneSymbol"]
                            + "_"
                            + gene_hit["modeOfInheritance"],
                            simplified_exomiser_result,
                            self.ranking_method,
                        ).create_simplified_result()
        return simplified_exomiser_result

    def standardise_result(self) -> dict:
        """Standardises Exomiser Json result for PhEval analysis."""
        simplified_exomiser_result = self.simplify_exomiser_result()
        return RankExomiserResult(simplified_exomiser_result, self.ranking_method).rank_results()


class AssessExomiserPrioritisation:
    # EXOMISER SPECIFIC
    """Class for assessing gene and variant prioritisation from Exomiser."""

    def __init__(
        self,
        phenopacket: Path,
        results_directory: Path,
        standardised_exomiser_result: dict,
        threshold: float,
        ranking_method: str,
        proband_causative_genes: list,
        proband_causative_variants: list,
    ):
        self.phenopacket = phenopacket
        self.results_directory = results_directory
        self.standardised_exomiser_result = standardised_exomiser_result
        self.threshold = threshold
        self.ranking_method = ranking_method
        self.proband_causative_genes = proband_causative_genes
        self.proband_causative_variants = proband_causative_variants

    def record_gene_prioritisation_match(
        self, gene: str, result_data: dict, rank_stats: RankStats
    ) -> GenePrioritisationResultData:
        """Records the gene prioritisation rank if found within results."""
        rank = result_data["rank"]
        rank_stats.add_rank(rank)
        gene_match = GenePrioritisationResultData(self.phenopacket, gene, rank)
        return gene_match

    def record_variant_prioritisation_match(
        self,
        variant: VariantData,
        result_data: dict,
        rank_stats: RankStats,
    ) -> VariantPrioritisationResultData:
        """Records the variant prioritisation rank if found within results."""
        rank = result_data["rank"]
        rank_stats.add_rank(rank)
        variant_match = VariantPrioritisationResultData(self.phenopacket, variant, rank)
        return variant_match

    def assess_gene_with_pvalue_threshold(
        self, result_data: dict, gene: str, rank_stats: RankStats
    ) -> GenePrioritisationResultData:
        """Records the gene prioritisation rank if it meets the pvalue threshold."""
        if float(self.threshold) > float(result_data[self.ranking_method]):
            return self.record_gene_prioritisation_match(gene, result_data, rank_stats)

    def assess_gene_with_threshold(
        self, result_data: dict, gene: str, rank_stats: RankStats
    ) -> GenePrioritisationResultData:
        """Records the gene prioritisation rank if it meets the score threshold."""
        if float(self.threshold) < float(result_data[self.ranking_method]):
            return self.record_gene_prioritisation_match(gene, result_data, rank_stats)

    def assess_variant_with_pvalue_threshold(
        self, result_data: dict, variant: VariantData, rank_stats: RankStats
    ) -> VariantPrioritisationResultData:
        """Records the variant prioritisation rank if it meets the pvalue threshold."""
        if float(self.threshold) > float(result_data[self.ranking_method]):
            return self.record_variant_prioritisation_match(variant, result_data, rank_stats)

    def assess_variant_with_threshold(
        self, result_data: dict, variant: VariantData, rank_stats: RankStats
    ) -> VariantPrioritisationResultData:
        """Records the variant prioritisation rank if it meets the score threshold."""
        if float(self.threshold) < float(result_data[self.ranking_method]):
            return self.record_variant_prioritisation_match(variant, result_data, rank_stats)

    def assess_gene_prioritisation(self, rank_stats: RankStats, rank_records: defaultdict) -> None:
        # TODO change so that it first attempts to match by gene id and if there is no match attempt to match by gene
        for gene in self.proband_causative_genes:
            rank_stats.total += 1
            gene_match = GenePrioritisationResultData(self.phenopacket, gene)
            for _result_identifier, result_data in self.standardised_exomiser_result.items():
                if gene == result_data["geneSymbol"] and float(self.threshold) != 0.0:
                    gene_match = (
                        self.assess_gene_with_threshold(result_data, gene, rank_stats)
                        if self.ranking_method != "pValue"
                        else self.assess_gene_with_pvalue_threshold(result_data, gene, rank_stats)
                    )
                    break
                if gene == result_data["geneSymbol"] and float(self.threshold) == 0.0:
                    gene_match = self.record_gene_prioritisation_match(
                        gene, result_data, rank_stats
                    )
                    break
            PrioritisationRankRecorder(
                rank_stats.total, self.results_directory, gene_match, rank_records
            ).record_rank()

    def assess_variant_prioritisation(self, rank_stats: RankStats, rank_records: defaultdict):
        for variant in self.proband_causative_variants:
            rank_stats.total += 1
            variant_match = VariantPrioritisationResultData(self.phenopacket, variant)
            for _result_identifier, result_data in self.standardised_exomiser_result.items():
                if variant.gene == result_data["geneSymbol"]:
                    for contributing_variant in result_data["contributingVariants"]:
                        if (
                            variant.chrom == contributing_variant.chrom
                            and contributing_variant.pos == variant.pos
                            and contributing_variant.ref == variant.ref
                            and contributing_variant.alt == variant.alt
                            and float(self.threshold) != 0.0
                        ):
                            variant_match = (
                                self.assess_variant_with_threshold(result_data, variant, rank_stats)
                                if self.ranking_method != "pValue"
                                else self.assess_variant_with_pvalue_threshold(
                                    result_data, variant, rank_stats
                                )
                            )
                            break
                        if (
                            variant.chrom == contributing_variant.chrom
                            and contributing_variant.pos == variant.pos
                            and contributing_variant.ref == variant.ref
                            and contributing_variant.alt == variant.alt
                            and float(self.threshold) == 0.0
                        ):
                            variant_match = self.record_variant_prioritisation_match(
                                variant, result_data, rank_stats
                            )
                            break
                    break
            PrioritisationRankRecorder(
                rank_stats.total, self.results_directory, variant_match, rank_records
            ).record_rank()


def obtain_causative_genes(phenopacket_path):
    phenopacket = phenopacket_reader(phenopacket_path)
    phenopacket_util = PhenopacketUtil(phenopacket)
    return phenopacket_util.diagnosed_genes()


def obtain_causative_variants(phenopacket_path):
    phenopacket = phenopacket_reader(phenopacket_path)
    phenopacket_util = PhenopacketUtil(phenopacket)
    return phenopacket_util.diagnosed_variants()


def assess_prioritisation_for_phenopacket(
    exomiser_result: Path,
    phenopacket_dir: Path,
    ranking_method: str,
    directory: Path,
    threshold: float,
    gene_rank_stats: RankStats,
    gene_rank_comparison: defaultdict,
    variant_rank_stats: RankStats,
    variant_rank_comparison: defaultdict,
):
    phenopacket_path = obtain_closest_file_name(exomiser_result, all_files(phenopacket_dir))
    proband_causative_genes = obtain_causative_genes(phenopacket_path)
    proband_causative_variants = obtain_causative_variants(phenopacket_path)
    standardised_exomiser_result = StandardiseExomiserResult(
        read_exomiser_json_result(exomiser_result), ranking_method
    ).standardise_result()
    assess_exomiser_prioritisation = AssessExomiserPrioritisation(
        phenopacket_path,
        directory,
        standardised_exomiser_result,
        threshold,
        ranking_method,
        proband_causative_genes,
        proband_causative_variants,
    )
    assess_exomiser_prioritisation.assess_gene_prioritisation(gene_rank_stats, gene_rank_comparison)
    assess_exomiser_prioritisation.assess_variant_prioritisation(
        variant_rank_stats, variant_rank_comparison
    )


def assess_prioritisation_for_results_directory(
    directory: Path,
    phenopacket_dir: Path,
    ranking_method: str,
    threshold: float,
    gene_rank_comparison: defaultdict,
    variant_rank_comparison: defaultdict,
    gene_stats_writer: RankStatsWriter,
    variants_stats_writer: RankStatsWriter,
):
    gene_rank_stats, variant_rank_stats = RankStats(), RankStats()
    exomiser_json_results = files_with_suffix(directory, ".json")
    for exomiser_result in exomiser_json_results:
        assess_prioritisation_for_phenopacket(
            exomiser_result,
            phenopacket_dir,
            ranking_method,
            Path(directory),
            threshold,
            gene_rank_stats,
            gene_rank_comparison,
            variant_rank_stats,
            variant_rank_comparison,
        )
    gene_stats_writer.write_row(directory, gene_rank_stats)
    variants_stats_writer.write_row(directory, variant_rank_stats)


def benchmark_directory(
    directory: Path,
    phenopacket_dir: Path,
    ranking_method: str,
    output_prefix: str,
    threshold: float,
):
    gene_stats_writer = RankStatsWriter(Path(output_prefix + "-gene_summary.tsv"))
    variants_stats_writer = RankStatsWriter(Path(output_prefix + "-variant_summary.tsv"))
    gene_rank_comparison, variant_rank_comparison = defaultdict(dict), defaultdict(dict)
    assess_prioritisation_for_results_directory(
        directory,
        phenopacket_dir,
        ranking_method,
        threshold,
        gene_rank_comparison,
        variant_rank_comparison,
        gene_stats_writer,
        variants_stats_writer,
    )
    RankComparisonGenerator(gene_rank_comparison).generate_gene_output(output_prefix)
    RankComparisonGenerator(variant_rank_comparison).generate_variant_output(output_prefix)
    gene_stats_writer.close()
    variants_stats_writer.close()


def benchmark_directories(
    directory_list: list[Path],
    phenopacket_dir: Path,
    ranking_method: str,
    output_prefix: str,
    threshold: float,
):
    gene_stats_writer = RankStatsWriter(Path(output_prefix + "-gene_summary.tsv"))
    variants_stats_writer = RankStatsWriter(Path(output_prefix + "-variant_summary.tsv"))
    gene_rank_comparison, variant_rank_comparison = defaultdict(dict), defaultdict(dict)
    for directory in directory_list:
        assess_prioritisation_for_results_directory(
            directory,
            phenopacket_dir,
            ranking_method,
            threshold,
            gene_rank_comparison,
            variant_rank_comparison,
            gene_stats_writer,
            variants_stats_writer,
        )
    RankComparisonGenerator(gene_rank_comparison).generate_gene_comparison_output(output_prefix)
    RankComparisonGenerator(variant_rank_comparison).generate_variant_comparison_output(
        output_prefix
    )
    gene_stats_writer.close()
    variants_stats_writer.close()


@click.command()
@click.option(
    "--directory",
    "-d",
    required=True,
    metavar="DIRECTORY",
    help="Exomiser results directory to be benchmarked",
    type=Path,
)
@click.option(
    "--phenopacket-dir",
    "-p",
    required=True,
    metavar="PATH",
    help="Full path to directory containing phenopackets.",
    type=Path,
)
@click.option(
    "--output-prefix",
    "-o",
    metavar="<str>",
    required=True,
    help=" Output file prefix. ",
)
@click.option(
    "--ranking-method",
    "-r",
    type=click.Choice(["combinedScore", "phenotypeScore", "variantScore", "pValue"]),
    default="combinedScore",
    show_default=True,
    help="Ranking method for gene prioritisation.",
)
@click.option(
    "--threshold",
    "-t",
    metavar="<float>",
    default=float(0.0),
    required=False,
    help="Score threshold.",
    type=float,
)
def benchmark(directory: Path, phenopacket_dir: Path, ranking_method, output_prefix, threshold):
    benchmark_directory(directory, phenopacket_dir, ranking_method, output_prefix, threshold)


@click.command()
@click.option(
    "--directory1",
    "-d1",
    required=True,
    metavar="DIRECTORY",
    help="Baseline Exomiser results directory for benchmarking",
    type=Path,
)
@click.option(
    "--directory2",
    "-d2",
    required=True,
    metavar="DIRECTORY",
    help="Comparison Exomiser results directory for benchmarking",
    type=Path,
)
@click.option(
    "--phenopacket-dir",
    "-p",
    required=True,
    metavar="PATH",
    help="Full path to directory containing phenopackets.",
    type=Path,
)
@click.option(
    "--output-prefix",
    "-o",
    metavar="<str>",
    required=True,
    help=" Output file prefix. ",
)
@click.option(
    "--ranking-method",
    "-r",
    type=click.Choice(["combinedScore", "phenotypeScore", "variantScore", "pValue"]),
    default="combinedScore",
    show_default=True,
    help="Ranking method for gene prioritisation.",
)
@click.option(
    "--threshold",
    "-t",
    metavar="<float>",
    default=float(0.0),
    required=False,
    help="Score threshold.",
    type=float,
)
def benchmark_comparison(
    directory1: Path,
    directory2: Path,
    phenopacket_dir: Path,
    ranking_method,
    output_prefix,
    threshold,
):
    benchmark_directories(
        [directory1, directory2], phenopacket_dir, ranking_method, output_prefix, threshold
    )
