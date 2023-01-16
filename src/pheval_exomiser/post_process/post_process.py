import os
from pathlib import Path

from pheval_exomiser.config_parser import ExomiserConfig
from pheval_exomiser.post_process.assess_prioritisation import (
    CorrespondingExomiserInput,
    benchmark_directories_for_pairwise_comparison,
    benchmark_directory,
    benchmark_several_directories,
)


def post_process_exomiser_results(output_dir: Path, config: ExomiserConfig):
    os.chdir(Path(output_dir))
    try:
        Path("benchmarking_results").mkdir()
        print("...created benchmarking results directory...")
    except FileExistsError:
        pass
    os.chdir(Path(output_dir).joinpath("benchmarking_results"))
    print("...benchmarking exomiser results...")
    print("...writing benchmarking results...")
    if len(config.run.runs) == 1:
        benchmark_directory(
            results_dir_and_input=CorrespondingExomiserInput(
                phenopacket_dir=config.run.runs[0].path_to_input_phenopacket_data,
                results_dir=Path(output_dir).joinpath(
                    config.run.runs[0].run_identifier + "_results"
                ),
            ),
            ranking_method=config.post_processing.ranking_method,
            output_prefix=config.post_processing.output_prefix,
            threshold=config.post_processing.threshold,
            gene_analysis=config.post_processing.benchmark_gene_prioritisation,
            variant_analysis=config.post_processing.benchmark_variant_prioritisation,
        )
    elif len(config.run.runs) == 2:
        benchmark_directories_for_pairwise_comparison(
            results_directories=[
                CorrespondingExomiserInput(
                    phenopacket_dir=config.run.runs[0].path_to_input_phenopacket_data,
                    results_dir=Path(output_dir).joinpath(
                        config.run.runs[0].run_identifier + "_results"
                    ),
                ),
                CorrespondingExomiserInput(
                    phenopacket_dir=config.run.runs[1].path_to_input_phenopacket_data,
                    results_dir=Path(output_dir).joinpath(
                        config.run.runs[1].run_identifier + "_results"
                    ),
                ),
            ],
            ranking_method=config.post_processing.ranking_method,
            output_prefix=config.post_processing.output_prefix,
            threshold=config.post_processing.threshold,
            gene_analysis=config.post_processing.benchmark_gene_prioritisation,
            variant_analysis=config.post_processing.benchmark_variant_prioritisation,
        )
    else:
        runs = [
            CorrespondingExomiserInput(
                phenopacket_dir=run.path_to_input_phenopacket_data,
                results_dir=Path(output_dir).joinpath(run.run_identifier + "_results"),
            )
            for run in config.run.runs
        ]
        benchmark_several_directories(
            results_directories=runs,
            ranking_method=config.post_processing.ranking_method,
            output_prefix=config.post_processing.output_prefix,
            threshold=config.post_processing.threshold,
            gene_analysis=config.post_processing.benchmark_gene_prioritisation,
            variant_analysis=config.post_processing.benchmark_variant_prioritisation,
        )
    print("done")
