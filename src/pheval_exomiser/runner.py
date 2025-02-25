"""Exomiser Runner"""

import os
import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests
from pheval.runners.runner import PhEvalRunner

from pheval_exomiser.post_process.post_process import post_process_result_format
from pheval_exomiser.prepare.tool_specific_configuration_options import (
    ExomiserConfigurations,
)
from pheval_exomiser.prepare.write_application_properties import (
    ExomiserConfigurationFileWriter,
)
from pheval_exomiser.run.run import prepare_batch_files, run_exomiser


@dataclass
class ExomiserPhEvalRunner(PhEvalRunner):
    """_summary_"""

    input_dir: Path
    testdata_dir: Path
    tmp_dir: Path
    output_dir: Path
    config_file: Path
    version: str

    def install(self, overwrite_existing: bool = False):
        # Parse configuration options
        configuration = ExomiserConfigurations.parse_obj(
            self.input_dir_config.tool_specific_configuration_options
        )
        phenotype_version = configuration.application_properties.phenotype_data_version

        # Define filenames and URLs
        base_url = "https://data.monarchinitiative.org/exomiser"
        filenames = [
            f"{phenotype_version}_hg19.zip",
            f"{phenotype_version}_hg38.zip",
            f"{phenotype_version}_phenotype.zip",
        ]
        urls = [
            f"{base_url}/{self.version}/exomiser-cli-{self.version}-distribution.zip",
            *[f"{base_url}/data/{filename}" for filename in filenames],
        ]

        # Download files
        os.makedirs("./data/tmp/", exist_ok=True)
        for url in urls:
            filename = url.split("/")[-1]
            full_filename = f"./data/tmp/{filename}"

            if os.path.exists(full_filename) and not overwrite_existing:
                continue

            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            with open(full_filename, "wb") as f:
                f.write(response.content)

        # Check if data directory exists
        data_dir = f"exomiser-cli-{self.version}/data"
        if os.path.exists(data_dir) and not overwrite_existing:
            return

        # Unzip distribution file
        with zipfile.ZipFile(
            f"exomiser-cli-{self.version}-distribution.zip", "r"
        ) as zip_ref:
            zip_ref.extractall(".")

        # Unzip data files into the appropriate directory
        os.makedirs(data_dir, exist_ok=True)
        for filename in filenames:
            with zipfile.ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(data_dir)

        # Update application.properties
        properties_path = os.path.join(data_dir, "application.properties")
        with open(properties_path, "a") as prop_file:
            prop_file.writelines(
                [
                    f"exomiser.hg19.data-version={phenotype_version}\n",
                    f"exomiser.hg38.data-version={phenotype_version}\n",
                    f"exomiser.phenotype.data-version={phenotype_version}\n",
                ]
            )

    def prepare(self):
        """prepare"""
        print("preparing")
        ExomiserConfigurationFileWriter(
            input_dir=self.input_dir,
            configurations=ExomiserConfigurations.parse_obj(
                self.input_dir_config.tool_specific_configuration_options
            ),
        ).write_application_properties()

    def run(self):
        """run"""
        print("running with exomiser")
        config = ExomiserConfigurations.parse_obj(
            self.input_dir_config.tool_specific_configuration_options
        )
        prepare_batch_files(
            input_dir=self.input_dir,
            config=config,
            testdata_dir=self.testdata_dir,
            tool_input_commands_dir=self.tool_input_commands_dir,
            raw_results_dir=self.raw_results_dir,
            variant_analysis=self.input_dir_config.variant_analysis,
        )
        run_exomiser(
            input_dir=self.input_dir,
            testdata_dir=self.testdata_dir,
            config=config,
            output_dir=self.output_dir,
            tool_input_commands_dir=self.tool_input_commands_dir,
            raw_results_dir=self.raw_results_dir,
            exomiser_version=self.version,
            variant_analysis=self.input_dir_config.variant_analysis,
        )

    def post_process(self):
        """post_process"""
        print("post processing")
        config = ExomiserConfigurations.parse_obj(
            self.input_dir_config.tool_specific_configuration_options
        )
        post_process_result_format(
            config=config,
            raw_results_dir=self.raw_results_dir,
            output_dir=self.output_dir,
            variant_analysis=self.input_dir_config.variant_analysis,
            gene_analysis=self.input_dir_config.gene_analysis,
            disease_analysis=self.input_dir_config.disease_analysis,
        )
