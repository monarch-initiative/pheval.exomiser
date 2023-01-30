"""Exomiser Runner"""
from dataclasses import dataclass
from pathlib import Path

from pheval.runners.runner import PhEvalRunner

from pheval_exomiser.config_parser import parse_exomiser_config
from pheval_exomiser.post_process.post_process import post_process_result_format
from pheval_exomiser.run.run import prepare_batch_files, run_exomiser


@dataclass
class ExomiserPhEvalRunner(PhEvalRunner):
    """_summary_"""

    input_dir: Path
    testdata_dir: Path
    tmp_dir: Path
    output_dir: Path
    config_file: Path

    def prepare(self):
        """prepare"""
        print("preparing")
        # config = parse_exomiser_config(self.config_file)
        # try:
        #     Path(self.input_dir).mkdir()
        # except FileExistsError:
        #     pass
        # prepare_updated_phenopackets(
        #     input_dir=Path(self.input_dir).joinpath("phenopackets"),
        #     testdata_dir=Path(self.testdata_dir),
        #     config=config,
        # )
        # prepare_scrambled_phenopackets(
        #     input_dir=Path(self.input_dir), testdata_dir=Path(self.testdata_dir), config=config
        # )
        # prepare_spiked_vcfs(
        #     input_dir=Path(self.input_dir), testdata_dir=Path(self.testdata_dir), config=config
        # )

    def run(self):
        """run"""
        print("running with exomiser")
        config = parse_exomiser_config(self.config_file)
        prepare_batch_files(
            input_dir=self.input_dir,
            output_dir=Path(self.output_dir),
            config=config,
            testdata_dir=self.testdata_dir,
        )
        run_exomiser(
            input_dir=self.input_dir,
            testdata_dir=self.testdata_dir,
            output_dir=self.output_dir,
            config=config,
        )

    def post_process(self):
        """post_process"""
        print("post processing")
        config = parse_exomiser_config(self.config_file)
        post_process_result_format(
            testdata_dir=Path(self.testdata_dir),
            input_dir=Path(self.input_dir),
            output_dir=Path(self.output_dir),
            config=config,
        )
