#!/usr/bin/python
import itertools
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
from pheval.utils.phenopacket_utils import (
    PhenopacketUtil,
    ProbandCausativeGene,
    VariantData,
    phenopacket_reader,
)


@dataclass
class CorrespondingExomiserInput:
    """Tracks the corresponding input data for Exomiser and its corresponding result directory."""

    phenopacket_dir: Path
    results_dir: Path


@dataclass
class ExomiserSummaryStatsForRuns:
    """Tracks the summary statistics recorded for each Exomiser results from a run."""

    phenopacket_dir: Path
    gene_rank_stats: RankStats
    variant_rank_stats: RankStats


@dataclass
class SimplifiedExomiserGeneResult:
    """Dataclass for creating a simplified gene result from the Exomiser json."""

    exomiser_result: dict
    simplified_exomiser_gene_result: list
    ranking_method: str

    def add_gene_record(self) -> dict:
        """Adds the gene and gene identifier record to simplified result format."""
        return {
            "gene_symbol": self.exomiser_result["geneSymbol"],
            "gene_identifier": self.exomiser_result["geneIdentifier"]["geneId"],
        }

    def add_ranking_score(self, simplified_result_entry: dict) -> dict:
        """Adds the ranking score to simplified result format."""
        simplified_result_entry[self.ranking_method] = round(
            self.exomiser_result[self.ranking_method], 4
        )
        return simplified_result_entry

    def create_simplified_gene_result(self) -> [dict]:
        """Creates the simplified Exomiser Gene result."""
        self.simplified_exomiser_gene_result.append(self.add_ranking_score(self.add_gene_record()))
        return self.simplified_exomiser_gene_result


@dataclass
class SimplifiedExomiserVariantResult:
    """Dataclass for creating a simplified Exomiser variant result."""

    exomiser_result: dict
    simplified_exomiser_variant_result: list
    ranking_method: str
    ranking_score: float

    def create_simplified_variant_result(self) -> [dict]:
        """Adds data for contributing variants to simplified result format."""
        for cv in self.exomiser_result["contributingVariants"]:
            self.simplified_exomiser_variant_result.append(
                {
                    "variant": VariantData(
                        cv["contigName"],
                        cv["start"],
                        cv["ref"],
                        cv["alt"],
                        self.exomiser_result["geneIdentifier"]["geneSymbol"],
                    ),
                    self.ranking_method: self.ranking_score,
                }
            )
        return self.simplified_exomiser_variant_result


class RankExomiserResult:
    """Adds rank to simplified Exomiser gene/variant results - taking care of ex-aequo scores."""

    def __init__(self, simplified_exomiser_result: [dict], ranking_method: str):
        self.simplified_exomiser_result = simplified_exomiser_result
        self.ranking_method = ranking_method

    def sort_exomiser_result(self) -> [dict]:
        """Sorts simplified Exomiser result by ranking method in decreasing order."""
        return sorted(
            self.simplified_exomiser_result,
            key=lambda d: d[self.ranking_method],
            reverse=True,
        )

    def sort_exomiser_result_pvalue(self) -> [dict]:
        """Sorts simplified Exomiser result by pvalue, most significant value first."""
        return sorted(
            self.simplified_exomiser_result,
            key=lambda d: d[self.ranking_method],
            reverse=False,
        )

    def rank_results(self) -> [dict]:
        """Adds ranks to the Exomiser results, equal scores are given the same rank e.g., 1,1,3."""
        sorted_exomiser_result = (
            self.sort_exomiser_result_pvalue()
            if self.ranking_method == "pValue"
            else self.sort_exomiser_result()
        )
        rank, count, previous = 0, 0, None
        for exomiser_result in sorted_exomiser_result:
            count += 1
            if exomiser_result[self.ranking_method] != previous:
                rank += count
                previous = exomiser_result[self.ranking_method]
                count = 0
            exomiser_result["rank"] = rank
        return sorted_exomiser_result


def read_exomiser_json_result(exomiser_result_path: Path) -> dict:
    """Loads Exomiser json result."""
    with open(exomiser_result_path) as exomiser_json_result:
        exomiser_result = json.load(exomiser_json_result)
    exomiser_json_result.close()
    return exomiser_result


class StandardiseExomiserResult:
    """Standardises Exomiser output into simplified gene and variant results for analysis."""

    def __init__(self, exomiser_json_result: [dict], ranking_method: str):
        self.exomiser_json_result = exomiser_json_result
        self.ranking_method = ranking_method

    def simplify_gene_result(self) -> [dict]:
        """Simplifies Exomiser json output into gene results."""
        simplified_exomiser_result = []
        for result in self.exomiser_json_result:
            if self.ranking_method in result:
                simplified_exomiser_result = SimplifiedExomiserGeneResult(
                    result, simplified_exomiser_result, self.ranking_method
                ).create_simplified_gene_result()
        return simplified_exomiser_result

    def simplify_variant_result(self) -> [dict]:
        """Simplifies Exomiser json output into variant results."""
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
        """Standardises Exomiser json to gene results for analysis."""
        simplified_exomiser_result = self.simplify_gene_result()
        return RankExomiserResult(simplified_exomiser_result, self.ranking_method).rank_results()

    def standardise_variant_result(self) -> [dict]:
        """Standardises Exomiser json to gene results for analysis."""
        simplified_exomiser_result = self.simplify_variant_result()
        return RankExomiserResult(simplified_exomiser_result, self.ranking_method).rank_results()


class AssessExomiserGenePrioritisation:
    """Class for assessing Exomiser gene prioritisation."""

    def __init__(
        self,
        phenopacket_path: Path,
        results_dir: Path,
        standardised_exomiser_gene_result: [dict],
        threshold: float,
        ranking_method: str,
        proband_causative_genes: [ProbandCausativeGene],
    ):
        self.phenopacket_path = phenopacket_path
        self.results_dir = results_dir
        self.standardised_exomiser_gene_result = standardised_exomiser_gene_result
        self.threshold = threshold
        self.ranking_method = ranking_method
        self.proband_causative_genes = proband_causative_genes

    def record_gene_prioritisation_match(
        self, gene: ProbandCausativeGene, result_entry: dict, rank_stats: RankStats
    ) -> GenePrioritisationResultData:
        """Records the gene prioritisation rank if found within results."""
        rank = result_entry["rank"]
        rank_stats.add_rank(rank)
        gene_match = GenePrioritisationResultData(self.phenopacket_path, gene.gene_symbol, rank)
        return gene_match

    def assess_gene_with_pvalue_threshold(
        self, result_entry: dict, gene: ProbandCausativeGene, rank_stats: RankStats
    ) -> GenePrioritisationResultData:
        """Records the gene prioritisation rank if it meets the pvalue threshold."""
        if float(self.threshold) > float(result_entry[self.ranking_method]):
            return self.record_gene_prioritisation_match(gene, result_entry, rank_stats)

    def assess_gene_with_threshold(
        self, result_entry: dict, gene: ProbandCausativeGene, rank_stats: RankStats
    ) -> GenePrioritisationResultData:
        """Records the gene prioritisation rank if it meets the score threshold."""
        if float(self.threshold) < float(result_entry[self.ranking_method]):
            return self.record_gene_prioritisation_match(gene, result_entry, rank_stats)

    def assess_gene_prioritisation(self, rank_stats: RankStats, rank_records: defaultdict):
        """Assesses Exomiser gene prioritisation."""
        for gene in self.proband_causative_genes:
            rank_stats.total += 1
            gene_match = GenePrioritisationResultData(self.phenopacket_path, gene.gene_symbol)
            for exomiser_result in self.standardised_exomiser_gene_result:
                if (
                    gene.gene_identifier == exomiser_result["gene_identifier"]
                    and float(self.threshold) != 0.0
                ):
                    gene_match = (
                        self.assess_gene_with_threshold(exomiser_result, gene, rank_stats)
                        if self.ranking_method != "pValue"
                        else self.assess_gene_with_pvalue_threshold(
                            exomiser_result, gene, rank_stats
                        )
                    )
                    break
                if (
                    gene.gene_identifier == exomiser_result["gene_identifier"]
                    and float(self.threshold) == 0.0
                ):
                    gene_match = self.record_gene_prioritisation_match(
                        gene, exomiser_result, rank_stats
                    )
                    break
            PrioritisationRankRecorder(
                rank_stats.total,
                self.results_dir,
                GenePrioritisationResultData(self.phenopacket_path, gene.gene_symbol)
                if gene_match is None
                else gene_match,
                rank_records,
            ).record_rank()


class AssessExomiserVariantPrioritisation:
    """Class for assessing Exomiser variant prioritisation."""

    def __init__(
        self,
        phenopacket_path: Path,
        results_dir: Path,
        standardised_exomiser_variant_result: [dict],
        threshold: float,
        ranking_method: str,
        proband_causative_variants: [VariantData],
    ):
        self.phenopacket_path = phenopacket_path
        self.results_dir = results_dir
        self.standardised_exomiser_variant_result = standardised_exomiser_variant_result
        self.threshold = threshold
        self.ranking_method = ranking_method
        self.proband_causative_variants = proband_causative_variants

    def record_variant_prioritisation_match(
        self,
        result_entry: dict,
        rank_stats: RankStats,
    ) -> VariantPrioritisationResultData:
        """Records the variant prioritisation rank if found within results."""
        rank = result_entry["rank"]
        rank_stats.add_rank(rank)
        variant_match = VariantPrioritisationResultData(
            self.phenopacket_path, result_entry["variant"], rank
        )
        return variant_match

    def assess_variant_with_pvalue_threshold(
        self, result_entry: dict, rank_stats: RankStats
    ) -> VariantPrioritisationResultData:
        """Records the variant prioritisation rank if it meets the pvalue threshold."""
        if float(self.threshold) > float(result_entry[self.ranking_method]):
            return self.record_variant_prioritisation_match(result_entry, rank_stats)

    def assess_variant_with_threshold(
        self, result_entry: dict, rank_stats: RankStats
    ) -> VariantPrioritisationResultData:
        """Records the variant prioritisation rank if it meets the score threshold."""
        if float(self.threshold) < float(result_entry[self.ranking_method]):
            return self.record_variant_prioritisation_match(result_entry, rank_stats)

    def assess_variant_prioritisation(self, rank_stats: RankStats, rank_records: defaultdict):
        """Assesses Exomiser variant prioritisation."""
        for variant in self.proband_causative_variants:
            rank_stats.total += 1
            variant_match = VariantPrioritisationResultData(self.phenopacket_path, variant)
            for result in self.standardised_exomiser_variant_result:
                if (
                    variant.chrom == result["variant"].chrom
                    and result["variant"].pos == variant.pos
                    and result["variant"].ref == variant.ref
                    and result["variant"].alt == variant.alt
                    and float(self.threshold) != 0.0
                ):
                    variant_match = (
                        self.assess_variant_with_threshold(result, rank_stats)
                        if self.ranking_method != "pValue"
                        else self.assess_variant_with_pvalue_threshold(result, rank_stats)
                    )
                    break
                if (
                    variant.chrom == result["variant"].chrom
                    and result["variant"].pos == variant.pos
                    and result["variant"].ref == variant.ref
                    and result["variant"].alt == variant.alt
                    and float(self.threshold) == 0.0
                ):
                    variant_match = self.record_variant_prioritisation_match(result, rank_stats)
                    break
            PrioritisationRankRecorder(
                rank_stats.total,
                self.results_dir,
                VariantPrioritisationResultData(self.phenopacket_path, variant)
                if variant_match is None
                else variant_match,
                rank_records,
            ).record_rank()


def obtain_causative_genes(phenopacket_path):
    """Obtains causative genes from a phenopacket."""
    phenopacket = phenopacket_reader(phenopacket_path)
    phenopacket_util = PhenopacketUtil(phenopacket)
    return phenopacket_util.diagnosed_genes()


def obtain_causative_variants(phenopacket_path):
    """Obtains causative variants from a phenopacket."""
    phenopacket = phenopacket_reader(phenopacket_path)
    phenopacket_util = PhenopacketUtil(phenopacket)
    return phenopacket_util.diagnosed_variants()


def assess_phenopacket_gene_prioritisation(
    exomiser_result: Path,
    ranking_method: str,
    results_dir_and_input: CorrespondingExomiserInput,
    threshold: float,
    gene_rank_stats: RankStats,
    gene_rank_comparison: defaultdict,
):
    """Assesses Exomiser gene prioritisation for a phenopacket."""
    phenopacket_path = obtain_closest_file_name(
        exomiser_result, all_files(results_dir_and_input.phenopacket_dir)
    )
    proband_causative_genes = obtain_causative_genes(phenopacket_path)
    standardised_exomiser_gene_result = StandardiseExomiserResult(
        read_exomiser_json_result(exomiser_result), ranking_method
    ).standardise_gene_result()
    AssessExomiserGenePrioritisation(
        phenopacket_path,
        results_dir_and_input.results_dir,
        standardised_exomiser_gene_result,
        threshold,
        ranking_method,
        proband_causative_genes,
    ).assess_gene_prioritisation(gene_rank_stats, gene_rank_comparison)


def assess_phenopacket_variant_prioritisation(
    exomiser_result: Path,
    ranking_method: str,
    results_dir_and_input: CorrespondingExomiserInput,
    threshold: float,
    variant_rank_stats: RankStats,
    variant_rank_comparison: defaultdict,
):
    """Assesses Exomiser variant prioritisation for a phenopacket"""
    phenopacket_path = obtain_closest_file_name(
        exomiser_result, all_files(results_dir_and_input.phenopacket_dir)
    )
    proband_causative_variants = obtain_causative_variants(phenopacket_path)
    standardised_exomiser_variant_result = StandardiseExomiserResult(
        read_exomiser_json_result(exomiser_result), ranking_method
    ).standardise_variant_result()
    AssessExomiserVariantPrioritisation(
        phenopacket_path,
        results_dir_and_input.results_dir,
        standardised_exomiser_variant_result,
        threshold,
        ranking_method,
        proband_causative_variants,
    ).assess_variant_prioritisation(variant_rank_stats, variant_rank_comparison)


def assess_prioritisation_for_results_directory(
    results_directory_and_input: CorrespondingExomiserInput,
    ranking_method: str,
    threshold: float,
    gene_rank_comparison: defaultdict,
    variant_rank_comparison: defaultdict,
    gene_stats_writer: RankStatsWriter,
    variants_stats_writer: RankStatsWriter,
    gene_analysis: bool,
    variant_analysis: bool,
):
    """Assesses Exomiser prioritisation for a single results directory."""
    gene_rank_stats, variant_rank_stats = RankStats(), RankStats()
    exomiser_json_results = files_with_suffix(results_directory_and_input.results_dir, ".json")
    for exomiser_result in exomiser_json_results:
        if gene_analysis and not variant_analysis:
            assess_phenopacket_gene_prioritisation(
                exomiser_result,
                ranking_method,
                results_directory_and_input,
                threshold,
                gene_rank_stats,
                gene_rank_comparison,
            )
        elif variant_analysis and not gene_analysis:
            assess_phenopacket_variant_prioritisation(
                exomiser_result,
                ranking_method,
                results_directory_and_input,
                threshold,
                variant_rank_stats,
                variant_rank_comparison,
            )
        elif variant_analysis and gene_analysis:
            assess_phenopacket_gene_prioritisation(
                exomiser_result,
                ranking_method,
                results_directory_and_input,
                threshold,
                gene_rank_stats,
                gene_rank_comparison,
            )
            assess_phenopacket_variant_prioritisation(
                exomiser_result,
                ranking_method,
                results_directory_and_input,
                threshold,
                variant_rank_stats,
                variant_rank_comparison,
            )
    gene_stats_writer.write_row(
        results_directory_and_input.results_dir, gene_rank_stats
    ) if gene_analysis else None
    variants_stats_writer.write_row(
        results_directory_and_input.results_dir, variant_rank_stats
    ) if variant_analysis else None
    return gene_rank_comparison, variant_rank_comparison


def benchmark_directory(
    results_dir_and_input: CorrespondingExomiserInput,
    ranking_method: str,
    output_prefix: str,
    threshold: float,
    gene_analysis: bool,
    variant_analysis: bool,
):
    """Benchmarks Exomiser prioritisation performance for a single directory."""
    gene_stats_writer = (
        RankStatsWriter(Path(output_prefix + "-gene_summary.tsv")) if gene_analysis else None
    )
    variants_stats_writer = (
        RankStatsWriter(Path(output_prefix + "-variant_summary.tsv")) if variant_analysis else None
    )
    gene_rank_comparison, variant_rank_comparison = defaultdict(dict), defaultdict(dict)
    assess_prioritisation_for_results_directory(
        results_dir_and_input,
        ranking_method,
        threshold,
        gene_rank_comparison,
        variant_rank_comparison,
        gene_stats_writer,
        variants_stats_writer,
        gene_analysis,
        variant_analysis,
    )
    RankComparisonGenerator(gene_rank_comparison).generate_gene_output(
        f"{results_dir_and_input.results_dir.name}"
    ) if gene_analysis else None
    RankComparisonGenerator(variant_rank_comparison).generate_variant_output(
        f"{results_dir_and_input.results_dir.name}"
    ) if variant_analysis else None
    gene_stats_writer.close() if gene_analysis else None
    variants_stats_writer.close() if variant_analysis else None


def benchmark_directories_for_pairwise_comparison(
    results_directories: [CorrespondingExomiserInput],
    ranking_method: str,
    output_prefix: str,
    threshold: float,
    gene_analysis: bool,
    variant_analysis: bool,
):
    """Benchmarks Exomiser prioritisation performance generating a comparison."""
    gene_stats_writer = (
        RankStatsWriter(Path(output_prefix + "-gene_summary.tsv")) if gene_analysis else None
    )
    variants_stats_writer = (
        RankStatsWriter(Path(output_prefix + "-variant_summary.tsv")) if variant_analysis else None
    )
    gene_rank_comparison, variant_rank_comparison = defaultdict(dict), defaultdict(dict)
    for results_dir_and_input in results_directories:
        assess_prioritisation_for_results_directory(
            results_dir_and_input,
            ranking_method,
            threshold,
            gene_rank_comparison,
            variant_rank_comparison,
            gene_stats_writer,
            variants_stats_writer,
            gene_analysis,
            variant_analysis,
        )
    RankComparisonGenerator(gene_rank_comparison).generate_gene_comparison_output(
        f"{results_directories[0].results_dir.name}__v__{results_directories[1].results_dir.name}"
    ) if gene_analysis else None
    RankComparisonGenerator(variant_rank_comparison).generate_variant_comparison_output(
        f"{results_directories[0].results_dir.name}__v__{results_directories[1].results_dir.name}"
    ) if variant_analysis else None
    gene_stats_writer.close() if gene_analysis else None
    variants_stats_writer.close() if variant_analysis else None


def merge_dict(dict1, dict2):
    """Merges two nested dictionaries on commonalities."""
    for key, val in dict1.items():
        if type(val) == dict:
            if key in dict2 and type(dict2[key] == dict):
                merge_dict(dict1[key], dict2[key])
        else:
            if key in dict2:
                dict1[key] = dict2[key]

    for key, val in dict2.items():
        if key not in dict1:
            dict1[key] = val

    return dict1


@dataclass
class TrackGeneComparisons:
    """Tracks the gene ranks for each result in a result directory."""

    directory: Path
    gene_results: dict


@dataclass
class TrackVariantComparisons:
    """Tracks the variant ranks for each result in a result directory."""

    directory: Path
    variant_results: dict


def generate_gene_rank_comparisons(comparison_ranks: [tuple]) -> None:
    """Generates the gene rank comparison of two result directories."""
    for pair in comparison_ranks:
        merged_results = merge_dict(pair[0].gene_results, pair[1].gene_results)
        RankComparisonGenerator(merged_results).generate_gene_comparison_output(
            f"{pair[0].directory.name}__v__{pair[1].directory.name}"
        )


def generate_variant_rank_comparisons(comparison_ranks: [tuple]) -> None:
    """Generates the variant rank comparison of two result directories."""
    for pair in comparison_ranks:
        merged_results = merge_dict(pair[0].variant_results, pair[1].variant_results)
        RankComparisonGenerator(merged_results).generate_variant_comparison_output(
            f"{pair[0].directory.name}__v__{pair[1].directory.name}"
        )


def benchmark_several_directories(
    results_directories: [CorrespondingExomiserInput],
    ranking_method: str,
    output_prefix: str,
    threshold: float,
    gene_analysis: bool,
    variant_analysis: bool,
):
    """Benchmarks several result directories."""
    gene_stats_writer = (
        RankStatsWriter(Path(output_prefix + "-gene_summary.tsv")) if gene_analysis else None
    )
    variants_stats_writer = (
        RankStatsWriter(Path(output_prefix + "-variant_summary.tsv")) if variant_analysis else None
    )
    gene_ranks_for_directories = []
    variant_ranks_for_directories = []
    for results_dir_and_input in results_directories:
        gene_rank_comparison, variant_rank_comparison = defaultdict(dict), defaultdict(dict)
        gene_ranks, variant_ranks = assess_prioritisation_for_results_directory(
            results_dir_and_input,
            ranking_method,
            threshold,
            gene_rank_comparison,
            variant_rank_comparison,
            gene_stats_writer,
            variants_stats_writer,
            gene_analysis,
            variant_analysis,
        )
        gene_ranks_for_directories.append(
            TrackGeneComparisons(results_dir_and_input.results_dir, gene_ranks)
        )
        variant_ranks_for_directories.append(
            TrackVariantComparisons(results_dir_and_input.results_dir, variant_ranks)
        )
    generate_gene_rank_comparisons(
        list(itertools.combinations(gene_ranks_for_directories, 2))
    ) if gene_analysis else None
    generate_variant_rank_comparisons(
        list(itertools.combinations(variant_ranks_for_directories, 2))
    ) if variant_analysis else None


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
@click.option(
    "--gene-analysis/--no-gene-analysis",
    default=True,
    required=False,
    type=bool,
    show_default=True,
    help="Analyse gene prioritisation",
)
@click.option(
    "--variant-analysis/--no-variant-analysis",
    default=True,
    required=False,
    type=bool,
    show_default=True,
    help="Analyse variant prioritisation",
)
def benchmark(
    directory: Path,
    phenopacket_dir: Path,
    ranking_method: str,
    output_prefix: str,
    threshold: float,
    gene_analysis: bool,
    variant_analysis: bool,
):
    benchmark_directory(
        CorrespondingExomiserInput(results_dir=directory, phenopacket_dir=phenopacket_dir),
        ranking_method,
        output_prefix,
        threshold,
        gene_analysis,
        variant_analysis,
    )


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
    "--phenopacket-dir1",
    "-p",
    required=True,
    metavar="PATH",
    help="Full path to directory containing phenopackets for input for baseline directory.",
    type=Path,
)
@click.option(
    "--phenopacket-dir2",
    "-p",
    required=True,
    metavar="PATH",
    help="Full path to directory containing phenopackets for input for compariosn directory.",
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
@click.option(
    "--gene-analysis/--no-gene-analysis",
    default=True,
    required=False,
    type=bool,
    show_default=True,
    help="Analyse gene prioritisation",
)
@click.option(
    "--variant-analysis/--no-variant-analysis",
    default=True,
    required=False,
    type=bool,
    show_default=True,
    help="Analyse variant prioritisation",
)
def benchmark_comparison(
    directory1: Path,
    directory2: Path,
    phenopacket_dir1: Path,
    phenopacket_dir2: Path,
    ranking_method: str,
    output_prefix: str,
    threshold: float,
    gene_analysis: bool,
    variant_analysis: bool,
):
    benchmark_directories_for_pairwise_comparison(
        [
            CorrespondingExomiserInput(results_dir=directory1, phenopacket_dir=phenopacket_dir1),
            CorrespondingExomiserInput(results_dir=directory2, phenopacket_dir=phenopacket_dir2),
        ],
        ranking_method,
        output_prefix,
        threshold,
        gene_analysis,
        variant_analysis,
    )
