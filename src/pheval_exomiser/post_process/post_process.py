from pathlib import Path

from pheval_exomiser.config_parser import ExomiserConfig
from pheval_exomiser.post_process.post_process_results_format import create_standardised_results


def post_process_result_format(config: ExomiserConfig, raw_results_dir: Path, output_dir: Path):
    """Standardise Exomiser json format to separated gene and variant results."""
    print("...standardising results format...")
    create_standardised_results(
        results_dir=raw_results_dir,
        output_dir=output_dir,
        score_name=config.post_process.score_name,
        sort_order=config.post_process.sort_order,
        phenotype_only=config.run.phenotype_only,
    )
    print("done")
