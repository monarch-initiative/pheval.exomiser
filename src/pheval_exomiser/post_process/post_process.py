import itertools
import os
from pathlib import Path

from pheval_exomiser.config_parser import ExomiserConfig
from pheval_exomiser.post_process.assess_prioritisation import (
    benchmark_directories,
    benchmark_directory,
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
            directory=Path(output_dir).joinpath(config.run.runs[0].run_identifier + "_results"),
            phenopacket_dir=config.run.runs[0].path_to_input_phenopacket_data,
            ranking_method=config.post_processing.ranking_method,
            output_prefix=config.post_processing.output_prefix,
            threshold=config.post_processing.threshold
        )
    else:
        # TODO figure out how to add separate input data for comparison
        total_runs = []
        for run_details in config.run.runs:
            total_runs.append(run_details.run_identifier)
        pairwise_combination_for_comparisons = list(itertools.combinations(total_runs, 2))
        for pair in pairwise_combination_for_comparisons:
            benchmark_directories(
                Path(output_dir).joinpath(pair[0] + "_results"),
                Path(output_dir).joinpath(pair[1] + "_results"),
                phenopacket_dir1=Path(config["RUNS"][pair[0]]["PathToInputPhenopacketData"]),
                phenopacket_dir2=Path(config["RUNS"][pair[1]]["PathToInputPhenopacketData"]),
                ranking_method=config.post_processing.ranking_method,
                output_prefix=pair[0] + "__v__" + pair[1],
                threshold=config.post_processing.threshold,
            )

    print("done")
