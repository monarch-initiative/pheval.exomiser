import unittest
from pathlib import Path

from pheval_exomiser.config_parser import (
    ExomiserConfig,
    ExomiserConfigPostProcess,
    ExomiserConfigRun,
    ExomiserConfigRunExomiserConfigs,
    ExomiserConfigRunExomiserManualConfigs,
)
from pheval_exomiser.run.run import (
    ExomiserConfigParameters,
    add_exomiser_config_file_for_docker,
    create_docker_run_command,
)

basic_pheval_config = ExomiserConfig(
    run=ExomiserConfigRun(
        environment="local",
        phenotype_only=False,
        path_to_exomiser_software_directory=Path("/opt/exomiser/exomiser-cli-13.1.0"),
        path_to_analysis_yaml=Path("/exomiser/preset-exome-analysis.yml"),
        exomiser_configurations=ExomiserConfigRunExomiserConfigs(
            exomiser_version="13.1.0",
            path_to_application_properties_config=Path(
                "/opt/exomiser/exomiser-cli-13.1.0/application.properties"
            ),
            application_properties_arguments=ExomiserConfigRunExomiserManualConfigs(
                exomiser_phenotype_version=None,
                exomiser_hg19_version=None,
                exomiser_hg38_version=None,
            ),
        ),
        max_jobs=0,
    ),
    post_process=ExomiserConfigPostProcess(score_name="combinedScore", sort_order="descending"),
)


class TestAddExomiserConfigFileForDocker(unittest.TestCase):
    def test_add_exomiser_config_file_for_docker(self):
        self.assertEqual(
            add_exomiser_config_file_for_docker(basic_pheval_config),
            ExomiserConfigParameters(
                application_properties_path=Path("/opt/exomiser/exomiser-cli-13.1.0"),
                exomiser_phenotype_version=None,
                exomiser_hg19_version=None,
                exomiser_hg38_version=None,
            ),
        )


class TestCreateDockerRunCommand(unittest.TestCase):
    def test_create_docker_run_command(self):
        self.assertEqual(
            [
                "--batch",
                "/exomiser-batch-file/file",
                "--spring.config.location=/exomiser-config/application.properties",
            ],
            create_docker_run_command(basic_pheval_config, Path("/path/to/batch/file")),
        )
