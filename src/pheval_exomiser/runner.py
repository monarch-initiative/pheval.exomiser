"""Exomiser Runner"""
from dataclasses import dataclass
from pathlib import Path

from pheval.runners.runner import PhEvalRunner

from pheval_exomiser.config_parser import parse_exomiser_config
from pheval_exomiser.post_process.post_process import post_process_result_format
from pheval_exomiser.prepare.tool_specific_configuration_options import ExomiserConfigurations
from pheval_exomiser.prepare.write_application_properties import ExomiserConfigurationFileWriter
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

    def prepare(self):
        """prepare"""
        print("preparing")
        ExomiserConfigurationFileWriter(input_dir=self.input_dir,
                                        configurations=ExomiserConfigurations(
                                            **self.input_dir_config.tool_specific_configuration_options)).write_application_properties()

    def run(self):
        """run"""
        print("running with exomiser")
        config = parse_exomiser_config(self.config_file)
        prepare_batch_files(
            config=config,
            testdata_dir=self.testdata_dir,
            tool_input_commands_dir=self.tool_input_commands_dir,
            raw_results_dir=self.raw_results_dir,
        )
        run_exomiser(
            input_dir=self.input_dir,
            testdata_dir=self.testdata_dir,
            config=config,
            output_dir=self.output_dir,
            tool_input_commands_dir=self.tool_input_commands_dir,
            raw_results_dir=self.raw_results_dir,
        )

    def post_process(self):
        """post_process"""
        print("post processing")
        config = parse_exomiser_config(self.config_file)
        post_process_result_format(config=config, raw_results_dir=self.raw_results_dir, runner=self)
