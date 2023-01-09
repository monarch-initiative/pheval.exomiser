import os
import subprocess
from pathlib import Path

from pheval_exomiser.prepare.create_batch_commands import create_batch_file
from pheval_exomiser.prepare.prepare import read_config


def prepare_batch_files(config_path: Path):
    print("...preparing batch files...")
    config = read_config(config_path)
    output_opt_file = (
        None
        if config["RUN001"]["PathToOutputOptionFile"] == ""
        else config["RUN001"]["PathToOutputOptionFile"]
    )
    output_opt_dir = (
        None
        if config["RUN001"]["PathToOutputOptionFileDirectory"] == ""
        else config["RUN001"]["PathToOutputOptionFileDirectory"]
    )
    create_batch_file(
        config["RUN001"]["PathToPresetAnalysisYml"],
        Path(config["RUN001"]["PathToInputPhenopacketData"]),
        Path(config["RUN001"]["PathToInputVcfs"]),
        config["RUN001"]["BatchPrefix"],
        int(config["RUN"]["NumberOfJobs"]),
        output_opt_file,
        output_opt_dir,
    )


def run_exomiser(config_path: Path):
    print("...running exomiser...")
    config = read_config(config_path)
    prefixed_batch_files = [
        filename
        for filename in os.listdir(".")
        if filename.startswith(config["RUN001"]["BatchPrefix"])
    ]
    exomiser_config_path = Path(config["RUN001"]["PathToExomiserSoftwareDirectory"]).joinpath(
        "application.properties"
    )
    exomiser_jar_file = [
        filename
        for filename in os.listdir(Path(config["RUN001"]["PathToExomiserSoftwareDirectory"]))
        if filename.endswith(".jar")
    ][0]
    exomiser_jar_file_path = Path(config["RUN001"]["PathToExomiserSoftwareDirectory"]).joinpath(
        exomiser_jar_file
    )
    for file in prefixed_batch_files:
        subprocess.run(
            [
                "java",
                "-Xmx4g",
                "-jar",
                exomiser_jar_file_path,
                "--batch",
                file,
                f"--spring.config.location={exomiser_config_path}",
            ],
            shell=False,
        )
