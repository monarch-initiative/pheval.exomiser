import os
from pathlib import Path

from pheval_exomiser.config_parser import ExomiserConfig
from pheval_exomiser.post_process.post_process_results_format import create_standardised_results


def post_process_result_format(
    input_dir: Path, testdata_dir: Path, output_dir: Path, config: ExomiserConfig
):
    """Standardise Exomiser json format to separated gene and variant results."""
    print("...standardising results format...")
    run_output_dir = Path(output_dir).joinpath(
        f"exomiser_{config.run.exomiser_configurations.exomiser_version.replace('.', '_')}"
        f"_{os.path.basename(input_dir)}{os.sep}{os.path.basename(testdata_dir)}_results"
    )
    create_standardised_results(
        results_dir=Path(run_output_dir).joinpath("exomiser_results"),
        output_dir=run_output_dir,
        ranking_method=config.post_process.ranking_method,
    )
    print("done")
