from pathlib import Path

from pheval_exomiser.config_parser import ExomiserConfig
from pheval_exomiser.post_process.post_process_results_format import create_standardised_results


def post_process_result_format(output_dir: Path, config: ExomiserConfig):
    """Standardise Exomiser json format to separated gene and variant results."""
    print("...standardising results format...")
    create_standardised_results(
        results_dir=Path(output_dir).joinpath("exomiser_results"),
        output_dir=output_dir, ranking_method=config.post_process.ranking_method)
    print("done")
