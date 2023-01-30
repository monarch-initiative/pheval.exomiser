import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import docker
from pheval.utils.file_utils import all_files

from pheval_exomiser.config_parser import ExomiserConfig
from pheval_exomiser.prepare.create_batch_commands import create_batch_file

# def write_output_options(input_dir: Path, output_dir: Path, run: ExomiserConfigSingleRun):
#     try:
#         Path(input_dir.joinpath("output_options")).mkdir()
#     except FileExistsError:
#         pass
#     with open(Path(input_dir).joinpath("output_options/output_options.yaml"), "w") as output_options:
#         yaml.dump({'outputPrefix': f'{output_dir.absolute().joinpath(run.run_identifier)}_results/'}, output_options)
#     output_options.close()
#     return Path(input_dir).joinpath("output_options/output_options.yaml")


def prepare_batch_files(
    input_dir: Path, output_dir: Path, testdata_dir: Path, config: ExomiserConfig
) -> None:
    """Prepare the exomiser batch files"""
    results_sub_output_dir = Path(output_dir).joinpath(
        f"exomiser_{config.run.exomiser_configurations.exomiser_version.replace('.', '_')}_"
        f"{os.path.basename(input_dir)}"
    )

    results_sub_output_dir.mkdir(parents=True, exist_ok=True)
    print("...created sub results output directory...")
    print("...preparing batch files...")
    create_batch_file(
        environment=config.run.environment,
        analysis=config.run.path_to_analysis_yaml,
        phenopacket_dir=Path(testdata_dir).joinpath(
            [
                directory
                for directory in os.listdir(str(testdata_dir))
                if "phenopackets" in str(directory)
            ][0]
        ),
        vcf_dir=Path(testdata_dir).joinpath(
            [directory for directory in os.listdir(str(testdata_dir)) if "vcf" in str(directory)][0]
        ),
        output_dir=results_sub_output_dir,
        batch_prefix=os.path.basename(testdata_dir),
        max_jobs=config.run.max_jobs,
        output_options_file=None,
        output_options_dir=None,
    )


@dataclass
class BasicDockerMountsForExomiser:
    """Paths to mount for running Exomiser with docker."""

    phenopacket_test_data: str
    vcf_test_data: str
    exomiser_yaml: str
    batch_file_path: str
    exomiser_data_dir: str
    exomiser_application_properties: Optional[str] = None


@dataclass
class ExomiserConfigParameters:
    """Exomiser configuration arguments."""

    application_properties_path: Path = None
    exomiser_phenotype_version: str = None
    exomiser_hg19_version: str = None
    exomiser_hg38_version: str = None


def read_application_properties(config: ExomiserConfig) -> [str]:
    """Return contents of Exomiser application.properties."""
    with open(
        config.run.exomiser_configurations.path_to_application_properties_config
    ) as exomiser_config:
        exomiser_config_lines = exomiser_config.readlines()
    exomiser_config.close()
    return exomiser_config_lines


class EditExomiserApplicationProperties:
    def __init__(self, config: ExomiserConfig, input_dir: Path, exomiser_config_contents: [str]):
        self.config = config
        self.input_dir = input_dir
        self.exomiser_config_contents = exomiser_config_contents

    def edit_data_path_for_local_run(self):
        """Edit input data path for running locally."""
        return [
            line.replace(line, f"exomiser.data-directory={self.input_dir}\n")
            if line.startswith("exomiser.data-directory=")
            else line
            for line in self.exomiser_config_contents
        ]

    def edit_data_path_for_docker_run(self):
        """Edit input data path for running with docker."""
        return [
            line.replace(line, "exomiser.data-directory=/exomiser-data\n")
            if line.startswith("exomiser.data-directory=")
            else line
            for line in self.exomiser_config_contents
        ]

    def edit_data_path(self) -> [str]:
        """Return edited contents of application.properties."""
        return (
            self.edit_data_path_for_local_run()
            if self.config.run.environment == "local"
            else self.edit_data_path_for_docker_run()
        )


def write_edited_application_properties(
    config: ExomiserConfig, input_dir: Path, exomiser_config_contents: [str]
) -> None:
    """Write application.properties with edited contents."""
    with open(
        config.run.exomiser_configurations.path_to_application_properties_config, "w"
    ) as exomiser_config:
        exomiser_config.writelines(
            EditExomiserApplicationProperties(
                config, input_dir, exomiser_config_contents
            ).edit_data_path()
        )
    exomiser_config.close()


def mount_docker(
    input_dir: Path, testdata_dir: Path, output_dir: Path, config: ExomiserConfig
) -> BasicDockerMountsForExomiser:
    """Create docker mounts for paths required for running Exomiser."""
    test_data = os.listdir(str(testdata_dir))
    phenopacket_test_data = (
        f"{Path(testdata_dir).joinpath([sub_dir for sub_dir in test_data if 'phenopackets' in str(sub_dir)][0])}"
        f"{os.sep}:/exomiser-testdata-phenopacket"
    )
    vcf_test_data = (
        f"{Path(testdata_dir).joinpath([sub_dir for sub_dir in test_data if 'vcf' in str(sub_dir)][0])}"
        f"{os.sep}:/exomiser-testdata-vcf"
    )
    exomiser_yaml = f"{config.run.path_to_analysis_yaml.parents[0]}{os.sep}:/exomiser-yaml-template"
    batch_file_path = str(
        Path(output_dir).joinpath(
            f"exomiser_{config.run.exomiser_configurations.exomiser_version.replace('.', '_')}"
            f"_{os.path.basename(input_dir)}{os.sep}exomiser_batch_files{os.sep}:/exomiser-batch-file"
        )
    )
    exomiser_data_dir = f"{input_dir}{os.sep}:/exomiser-data"
    if config.run.exomiser_configurations.path_to_application_properties_config is None:
        # TODO add mount for results directory to be specified in the output-options
        return BasicDockerMountsForExomiser(
            phenopacket_test_data=phenopacket_test_data,
            vcf_test_data=vcf_test_data,
            exomiser_yaml=exomiser_yaml,
            batch_file_path=batch_file_path,
            exomiser_data_dir=exomiser_data_dir,
        )
    else:
        exomiser_config = (
            f"{config.run.exomiser_configurations.path_to_application_properties_config.parents[0]}{os.sep}"
            f":/exomiser-config"
        )
        return BasicDockerMountsForExomiser(
            phenopacket_test_data=phenopacket_test_data,
            vcf_test_data=vcf_test_data,
            exomiser_yaml=exomiser_yaml,
            batch_file_path=batch_file_path,
            exomiser_data_dir=exomiser_data_dir,
            exomiser_application_properties=exomiser_config,
        )


def add_exomiser_config_file_for_docker(config: ExomiserConfig) -> ExomiserConfigParameters:
    """Add application.properties path to config parameters."""
    return ExomiserConfigParameters(
        application_properties_path=config.run.exomiser_configurations.path_to_application_properties_config.parents[
            0
        ]
    )


def add_exomiser_config_parameters_for_docker(
    config: ExomiserConfig,
) -> ExomiserConfigParameters:
    """Add manual arguments required for application.properties."""
    configs = config.run.exomiser_configurations.application_properties_arguments
    return ExomiserConfigParameters(
        exomiser_hg19_version=configs.exomiser_hg19_version,
        exomiser_hg38_version=configs.exomiser_hg38_version,
        exomiser_phenotype_version=configs.exomiser_phenotype_version,
    )


def exomiser_config_parameters(config: ExomiserConfig) -> ExomiserConfigParameters:
    """Add application.properties path to config arguments if specified, otherwise add manual configurations."""
    return (
        add_exomiser_config_file_for_docker(config)
        if config.run.exomiser_configurations.path_to_application_properties_config is not None
        else add_exomiser_config_parameters_for_docker(config)
    )


def run_exomiser_local(
    input_dir: Path, testdata_dir: Path, output_dir: Path, config: ExomiserConfig
) -> None:
    """Run Exomiser locally."""
    print("...running exomiser...")
    results_sub_output_dir = Path(output_dir).joinpath(
        f"exomiser_{config.run.exomiser_configurations.exomiser_version.replace('.', '_')}"
        f"_{os.path.basename(input_dir)}"
    )
    results_sub_output_dir.joinpath(f"{os.path.basename(testdata_dir)}_results").mkdir(
        exist_ok=True, parents=True
    )
    write_edited_application_properties(config, input_dir, read_application_properties(config))
    os.chdir(results_sub_output_dir.joinpath(f"{os.path.basename(testdata_dir)}_results"))
    batch_files = [
        file
        for file in all_files(Path(results_sub_output_dir).joinpath("exomiser_batch_files"))
        if file.name.startswith(os.path.basename(testdata_dir))
    ]
    exomiser_jar_file = [
        filename
        for filename in all_files(config.run.path_to_exomiser_software_directory)
        if filename.name.endswith(".jar")
    ][0]
    exomiser_jar_file_path = config.run.path_to_exomiser_software_directory.joinpath(
        exomiser_jar_file
    )
    for file in batch_files:
        subprocess.run(
            [
                "/usr/bin/java",
                "-Xmx4g",
                "-jar",
                exomiser_jar_file_path,
                "--batch",
                file,
                f"--spring.config.location={config.run.exomiser_configurations.path_to_application_properties_config}",
            ],
            shell=False,
        )
    os.rename(
        Path(results_sub_output_dir).joinpath(
            f"{os.path.basename(testdata_dir)}_results{os.sep}results"
        ),
        Path(results_sub_output_dir).joinpath(
            f"{os.path.basename(testdata_dir)}_results{os.sep}exomiser_results"
        ),
    )


def create_docker_run_command(config: ExomiserConfig, batch_file: Path) -> [str]:
    """Creates docker run command."""
    exomiser_config_params = exomiser_config_parameters(config)
    if exomiser_config_params.application_properties_path is None:
        return [
            "--batch",
            "/exomiser-batch-file/" + batch_file.name,
            f"--exomiser.data-directory=/exomiser-data"
            f"--exomiser.hg19.data-version={exomiser_config_params.exomiser_hg19_version}",
            f"--exomiser.hg38.data-version={exomiser_config_params.exomiser_hg38_version}",
            f"--exomiser.phenotype.data-version={exomiser_config_params.exomiser_phenotype_version}",
        ]
    else:
        return [
            "--batch",
            "/exomiser-batch-file/" + batch_file.name,
            "--spring.config.location=/exomiser-config/application.properties",
        ]


def run_exomiser_docker(
    input_dir: Path, testdata_dir: Path, output_dir: Path, config: ExomiserConfig
):
    """Run Exomiser with docker."""
    print("...running exomiser...")
    client = docker.from_env()
    results_sub_output_dir = Path(output_dir).joinpath(
        f"exomiser_{config.run.exomiser_configurations.exomiser_version.replace('.', '_')}"
        f"_{os.path.basename(input_dir)}"
    )
    results_sub_output_dir.joinpath(f"{os.path.basename(testdata_dir)}_results").mkdir(
        exist_ok=True, parents=True
    )
    write_edited_application_properties(config, input_dir, read_application_properties(config))
    os.chdir(results_sub_output_dir.joinpath(f"{os.path.basename(testdata_dir)}_results"))
    batch_files = [
        file
        for file in all_files(Path(results_sub_output_dir).joinpath("exomiser_batch_files"))
        if file.name.startswith(os.path.basename(testdata_dir))
    ]
    for file in batch_files:
        docker_command = create_docker_run_command(config, file)
        docker_mounts = mount_docker(input_dir, testdata_dir, output_dir, config)
        vol = [
            docker_mounts.vcf_test_data,
            docker_mounts.phenopacket_test_data,
            docker_mounts.exomiser_data_dir,
            docker_mounts.exomiser_yaml,
            docker_mounts.batch_file_path,
            docker_mounts.exomiser_application_properties,
        ]
        container = client.containers.run(
            f"exomiser/exomiser-cli:{config.run.exomiser_configurations.exomiser_version}",
            " ".join(docker_command),
            volumes=[x for x in vol if x is not None],
            detach=True,
        )
        for line in container.logs(stream=True):
            print(line.strip())
        break


def run_exomiser(input_dir: Path, testdata_dir, output_dir: Path, config: ExomiserConfig):
    """Run Exomiser with specified environment."""
    run_exomiser_local(
        input_dir, testdata_dir, output_dir, config
    ) if config.run.environment == "local" else run_exomiser_docker(
        input_dir, testdata_dir, output_dir, config
    )
