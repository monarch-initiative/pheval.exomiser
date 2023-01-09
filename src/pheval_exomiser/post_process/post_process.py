from pathlib import Path

from pheval_exomiser.post_process.assess_prioritisation import benchmark_directory
from pheval_exomiser.prepare.prepare import read_config


def post_process_exomiser_results(config_path: [Path]):
    print("...benchmarking exomiser results...")
    config = read_config(config_path)
    benchmark_directory(
        Path("results"),
        Path(config["RUN001"]["PathToInputPhenopacketData"]),
        config["POSTPROCESSING"]["RankingMethod"],
        config["POSTPROCESSING"]["OutputPrefix"],
        float(config["POSTPROCESSING"]["Threshold"]),
    )
