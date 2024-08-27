import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import docker
from packaging import version
from pheval.utils.file_utils import all_files

from pheval_exomiser.constants import (
    EXOMISER_CONFIG_TARGET_DIRECTORY_DOCKER,
    EXOMISER_DATA_DIRECTORY_TARGET_DOCKER,
    EXOMISER_YAML_TARGET_DIRECTORY_DOCKER,
    INPUT_COMMANDS_TARGET_DIRECTORY_DOCKER,
    PHENOPACKET_TARGET_DIRECTORY_DOCKER,
    RAW_RESULTS_TARGET_DIRECTORY_DOCKER,
    VCF_TARGET_DIRECTORY_DOCKER,
)
from pheval_exomiser.prepare.create_batch_commands import create_batch_file
from pheval_exomiser.prepare.tool_specific_configuration_options import ExomiserConfigurations


def prepare_batch_files(
    input_dir: Path,
    testdata_dir: Path,
    config: ExomiserConfigurations,
    tool_input_commands_dir: Path,
    raw_results_dir: Path,
    variant_analysis: bool,
) -> None:
    """Prepare the exomiser batch files"""
    print("...preparing batch files...")
    vcf_dir_name = Path(testdata_dir).joinpath("vcf")
    output_formats = (
        config.output_formats + ["JSON"]
        if config.output_formats and "JSON" not in config.output_formats
        else config.output_formats
    )
    create_batch_file(
        environment=config.environment,
        analysis=input_dir.joinpath(config.analysis_configuration_file),
        phenopacket_dir=Path(testdata_dir).joinpath("phenopackets"),
        vcf_dir=vcf_dir_name if variant_analysis else None,
        output_dir=tool_input_commands_dir,
        batch_prefix=Path(testdata_dir).name,
        max_jobs=config.max_jobs,
        output_options_file=None,
        output_options_dir=None,
        results_dir=raw_results_dir,
        variant_analysis=variant_analysis,
        output_formats=output_formats,
    )


@dataclass
class BasicDockerMountsForExomiser:
    """Paths to mount for running Exomiser with docker."""

    phenopacket_test_data: str
    vcf_test_data: str
    exomiser_yaml: str
    tool_input_commands_path: str
    exomiser_data_dir: str
    raw_results_dir: Path
    exomiser_application_properties: Path


def mount_docker(
    input_dir: Path,
    testdata_dir: Path,
    tool_input_commands_dir: Path,
    raw_results_dir: Path,
    variant_analysis: bool,
) -> BasicDockerMountsForExomiser:
    """Create docker mounts for paths required for running Exomiser."""
    phenopacket_test_data = (
        f"{Path(testdata_dir).joinpath('phenopackets')}"
        f"{os.sep}:{PHENOPACKET_TARGET_DIRECTORY_DOCKER}"
    )
    vcf_test_data = (
        (f"{Path(testdata_dir).joinpath('vcf')}" f"{os.sep}:{VCF_TARGET_DIRECTORY_DOCKER}")
        if variant_analysis
        else None
    )
    exomiser_yaml = f"{input_dir}:{EXOMISER_YAML_TARGET_DIRECTORY_DOCKER}"
    batch_file_path = f"{tool_input_commands_dir}/:{INPUT_COMMANDS_TARGET_DIRECTORY_DOCKER}"
    exomiser_data_dir = f"{input_dir}{os.sep}:{EXOMISER_DATA_DIRECTORY_TARGET_DOCKER}"
    results_dir = f"{raw_results_dir}/:{RAW_RESULTS_TARGET_DIRECTORY_DOCKER}"
    exomiser_config = f"{input_dir}{os.sep}" f":{EXOMISER_CONFIG_TARGET_DIRECTORY_DOCKER}"
    return BasicDockerMountsForExomiser(
        phenopacket_test_data=phenopacket_test_data,
        vcf_test_data=vcf_test_data,
        exomiser_yaml=exomiser_yaml,
        tool_input_commands_path=batch_file_path,
        exomiser_data_dir=exomiser_data_dir,
        exomiser_application_properties=exomiser_config,
        raw_results_dir=results_dir,
    )


def run_exomiser_local(
    input_dir: Path,
    testdata_dir: Path,
    config: ExomiserConfigurations,
    output_dir: Path,
    tool_input_commands_dir: Path,
    exomiser_version: str,
) -> None:
    """Run Exomiser locally."""
    print("...running exomiser...")
    os.chdir(output_dir)
    batch_files = [
        file
        for file in all_files(tool_input_commands_dir)
        if file.name.startswith(Path(testdata_dir).name)
    ]
    exomiser_jar_file = [
        filename
        for filename in all_files(input_dir.joinpath(config.exomiser_software_directory))
        if filename.name.endswith(".jar")
    ][0]
    exomiser_jar_file_path = config.exomiser_software_directory.joinpath(exomiser_jar_file)
    for file in batch_files:
        subprocess.run(
            [
                "java",
                "-Xmx4g",
                "-jar",
                exomiser_jar_file_path,
                "--batch",
                file,
                f"--spring.config.location={Path(input_dir).joinpath('application.properties')}",
            ],
            shell=False,
        )
    if version.parse(exomiser_version) < version.parse("13.1.0"):
        os.rename(
            f"{output_dir}/results",
            output_dir.joinpath("raw_results"),
        )


def create_docker_run_command(batch_file: Path) -> [str]:
    """Creates docker run command."""
    return [
        "--batch",
        f"{INPUT_COMMANDS_TARGET_DIRECTORY_DOCKER}" + batch_file.name,
        f"--spring.config.location={EXOMISER_CONFIG_TARGET_DIRECTORY_DOCKER}application.properties",
    ]


def run_exomiser_docker(
    input_dir: Path,
    testdata_dir: Path,
    tool_input_commands_dir: Path,
    raw_results_dir: Path,
    exomiser_version: str,
    variant_analysis: bool,
):
    """Run Exomiser with docker."""
    print("...running exomiser...")
    client = docker.from_env()
    batch_files = [
        file
        for file in all_files(tool_input_commands_dir)
        if file.name.startswith(Path(testdata_dir).name)
    ]
    for file in batch_files:
        docker_command = create_docker_run_command(file)
        docker_mounts = mount_docker(
            input_dir, testdata_dir, tool_input_commands_dir, raw_results_dir, variant_analysis
        )
        vol = [
            docker_mounts.vcf_test_data,
            docker_mounts.phenopacket_test_data,
            docker_mounts.exomiser_data_dir,
            docker_mounts.exomiser_yaml,
            docker_mounts.tool_input_commands_path,
            docker_mounts.exomiser_application_properties,
            docker_mounts.raw_results_dir,
        ]
        container = client.containers.run(
            f"exomiser/exomiser-cli:{exomiser_version}",
            " ".join(docker_command),
            volumes=[x for x in vol if x is not None],
            detach=True,
        )
        for line in container.logs(stream=True):
            print(line.strip())
        break


def run_exomiser(
    input_dir: Path,
    testdata_dir,
    config: ExomiserConfigurations,
    output_dir: Path,
    tool_input_commands_dir: Path,
    raw_results_dir: Path,
    exomiser_version: str,
    variant_analysis: bool,
):
    """Run Exomiser with specified environment."""
    (
        run_exomiser_local(
            input_dir, testdata_dir, config, output_dir, tool_input_commands_dir, exomiser_version
        )
        if config.environment == "local"
        else run_exomiser_docker(
            input_dir,
            testdata_dir,
            tool_input_commands_dir,
            raw_results_dir,
            exomiser_version,
            variant_analysis,
        )
    )
