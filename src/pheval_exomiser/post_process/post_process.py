from pathlib import Path

from pheval.runners.runner import PhEvalRunner
from pheval_exomiser.config_parser import ExomiserConfig
from pheval_exomiser.post_process.post_process_results_format import create_standardised_results


def post_process_result_format(
        config: ExomiserConfig, runner_raw_results_dir: Path, runner: PhEvalRunner
):
    """Standardise Exomiser json format to separated gene and variant results."""
    print("...standardising results format...")
    create_standardised_results(
        results_dir=runner_raw_results_dir,
        runner=runner,
        score_name=config.post_process.score_name,
        score_order=config.post_process.score_order,
        phenotype_only=config.run.phenotype_only,
    )
    print("done")
