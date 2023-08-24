from pathlib import Path

from pheval_exomiser.post_process.post_process_results_format import create_standardised_results
from pheval_exomiser.prepare.tool_specific_configuration_options import ExomiserConfigurations


def post_process_result_format(
    config: ExomiserConfigurations,
    raw_results_dir: Path,
    output_dir: Path,
    variant_analysis: bool,
    gene_analysis: bool,
    disease_analysis: bool,
):
    """Standardise Exomiser json format to separated gene and variant results."""
    print("...standardising results format...")
    create_standardised_results(
        results_dir=raw_results_dir,
        output_dir=output_dir,
        score_name=config.post_process.score_name,
        sort_order=config.post_process.sort_order,
        variant_analysis=variant_analysis,
        gene_analysis=gene_analysis,
        disease_analysis=disease_analysis,
    )
    print("done")
