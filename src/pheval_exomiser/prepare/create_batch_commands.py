#!/usr/bin/python
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click
from phenopackets import Family, Phenopacket
from pheval.prepare.custom_exceptions import MutuallyExclusiveOptionError
from pheval.utils.file_utils import all_files, files_with_suffix, obtain_closest_file_name
from pheval.utils.phenopacket_utils import PhenopacketUtil, phenopacket_reader


@dataclass
class ExomiserCommandLineArguments:
    """Store command line arguments for each phenopacket to be run with Exomiser."""

    sample: Path
    vcf_file: Path or None = None
    vcf_assembly: str or None = None
    raw_results_dir: Path or None = None
    phenotype_only: bool or None = None
    output_options_file: Optional[Path] = None


def get_all_files_from_output_opt_directory(output_options_dir: Path) -> list[Path] or None:
    """Obtain all output options files if directory is specified - otherwise returns none."""
    return None if output_options_dir is None else all_files(output_options_dir)


class CommandCreator:
    """Create a command for a phenopacket."""

    def __init__(
        self,
        environment: str,
        phenopacket_path: Path,
        phenopacket: Phenopacket or Family,
        phenotype_only: bool,
        output_options_dir_files: list[Path] or None,
        output_options_file: Path or None,
        raw_results_dir: Path or None,
    ):
        self.environment = environment
        self.phenopacket_path = phenopacket_path
        self.phenopacket = phenopacket
        self.phenotype_only = phenotype_only
        self.output_options_dir_files = output_options_dir_files
        self.output_options_file = output_options_file
        self.results_dir = raw_results_dir

    def assign_output_options_file(self) -> Path or None:
        """Return the path of a single output option yaml if specified,
        otherwise return the best match from a directory."""
        if self.output_options_dir_files is None and self.output_options_file is None:
            return None
        else:
            return (
                self.output_options_file
                if self.output_options_dir_files is None
                else obtain_closest_file_name(self.phenopacket_path, self.output_options_dir_files)
            )

    def add_phenotype_only_arguments(self) -> ExomiserCommandLineArguments:
        output_options_file = self.assign_output_options_file()
        if self.environment == "docker":
            return ExomiserCommandLineArguments(
                sample=f"{PHENOPACKET_TARGET_DIRECTORY_DOCKER}{Path(self.phenopacket_path.name)}",
                phenotype_only=self.phenotype_only,
                output_options_file=f"{OUTPUT_OPTIONS_TARGET_DIRECTORY_DOCKER}{Path(output_options_file).name}",
                raw_results_dir=RAW_RESULTS_TARGET_DIRECTORY_DOCKER,
            )
        elif self.environment == "local":
            return ExomiserCommandLineArguments(
                sample=Path(self.phenopacket_path),
                phenotype_only=self.phenotype_only,
                output_options_file=output_options_file,
                raw_results_dir=self.results_dir,
            )

    def add_variant_analysis_arguments(self, vcf_dir: Path) -> ExomiserCommandLineArguments:
        vcf_file_data = PhenopacketUtil(self.phenopacket).vcf_file_data(
            self.phenopacket_path, vcf_dir
        )
        output_options_file = self.assign_output_options_file()
        if self.environment == "local":
            return ExomiserCommandLineArguments(
                sample=Path(self.phenopacket_path),
                vcf_file=Path(vcf_file_data.uri),
                vcf_assembly=vcf_file_data.file_attributes["genomeAssembly"],
                output_options_file=output_options_file,
                phenotype_only=self.phenotype_only,
                raw_results_dir=self.results_dir,
            )
        elif self.environment == "docker":
            return ExomiserCommandLineArguments(
                sample=f"{PHENOPACKET_TARGET_DIRECTORY_DOCKER}{Path(self.phenopacket_path.name)}",
                vcf_file=f"{VCF_TARGET_DIRECTORY_DOCKER}{Path(vcf_file_data.uri).name}",
                vcf_assembly=vcf_file_data.file_attributes["genomeAssembly"],
                output_options_file=f"{OUTPUT_OPTIONS_TARGET_DIRECTORY_DOCKER}{Path(output_options_file).name}",
                phenotype_only=self.phenotype_only,
                raw_results_dir=RAW_RESULTS_TARGET_DIRECTORY_DOCKER,
            )

    def add_command_line_arguments(self, vcf_dir: Path or None) -> ExomiserCommandLineArguments:
        """Return a dataclass of all the command line arguments corresponding to phenopacket sample."""
        return (
            self.add_phenotype_only_arguments()
            if self.phenotype_only
            else self.add_variant_analysis_arguments(vcf_dir)
        )


def create_command_arguments(
    environment: str,
    phenopacket_dir: Path,
    phenotype_only: bool,
    vcf_dir: Path,
    results_dir: Path or None,
    output_options_dir: Path or None = None,
    output_options_file: Path or None = None,
) -> list[ExomiserCommandLineArguments]:
    """Return a list of Exomiser command line arguments for a directory of phenopackets."""
    phenopacket_paths = files_with_suffix(phenopacket_dir, ".json")
    commands = []
    output_option_dir_files = get_all_files_from_output_opt_directory(output_options_dir)
    for phenopacket_path in phenopacket_paths:
        phenopacket = phenopacket_reader(phenopacket_path)
        commands.append(
            CommandCreator(
                environment,
                phenopacket_path,
                phenopacket,
                phenotype_only,
                output_option_dir_files,
                output_options_file,
                results_dir,
            ).add_command_line_arguments(vcf_dir)
        )
    return commands


class CommandsWriter:
    """Write a command to file."""

    def __init__(self, file: Path, phenotype_only: bool):
        self.file = open(file, "w")
        self.phenotype_only = phenotype_only

    def write_basic_analysis_command(
        self, analysis_yaml: Path, command_arguments: ExomiserCommandLineArguments
    ):
        """Write basic analysis command for Exomiser"""
        try:
            self.file.write(
                "--analysis "
                + str(analysis_yaml)
                + " --sample "
                + str(command_arguments.sample)
                + " --vcf "
                + str(command_arguments.vcf_file)
                + " --assembly "
                + command_arguments.vcf_assembly
            )
        except IOError:
            print("Error writing ", self.file)

    def write_results_dir(self, command_arguments: ExomiserCommandLineArguments) -> None:
        """Write results directory for exomiser ≥13.2.0 to run."""
        try:
            self.file.write(
                " --output-directory " + str(command_arguments.raw_results_dir)
            ) if command_arguments.raw_results_dir is not None else None
        except IOError:
            print("Error writing ", self.file)

    def write_output_options(self, command_arguments: ExomiserCommandLineArguments) -> None:
        """Write a command out for exomiser ≤13.1.0 to run - including output option file specified."""
        try:
            self.file.write(
                " --output " + str(command_arguments.output_options_file)
            ) if command_arguments.output_options_file is not None else None
        except IOError:
            print("Error writing ", self.file)

    def write_analysis_command(
        self, analysis_yaml: Path, command_arguments: ExomiserCommandLineArguments
    ):
        self.write_basic_analysis_command(analysis_yaml, command_arguments)
        self.write_results_dir(command_arguments)
        self.write_output_options(command_arguments)
        self.file.write("\n")

    def write_basic_phenotype_only_command(
        self, command_arguments: ExomiserCommandLineArguments
    ) -> None:
        """Write a phenotype-only command out for exomiser ≥13.2.0 to run."""
        try:
            self.file.write(
                "--sample "
                + str(command_arguments.sample)
                + " --output-directory "
                + str(command_arguments.raw_results_dir)
                + " --output-filename "
                + f"{command_arguments.sample.stem}-exomiser"
                + " --preset "
                + "phenotype-only"
            )
        except IOError:
            print("Error writing ", self.file)

    def write_phenotype_only_command(self, command_arguments: ExomiserCommandLineArguments):
        self.write_basic_phenotype_only_command(command_arguments)
        self.write_output_options(command_arguments)
        self.file.write("\n")

    def write_local_commands(
        self, analysis_yaml: Path, command_arguments: ExomiserCommandLineArguments
    ):
        self.write_phenotype_only_command(
            command_arguments
        ) if self.phenotype_only else self.write_analysis_command(analysis_yaml, command_arguments)

    def close(self) -> None:
        """Close file."""
        try:
            self.file.close()
        except IOError:
            print("Error closing ", self.file)


class BatchFileWriter:
    """Write all the commands out to a batch file."""

    def __init__(
        self,
        analysis_yaml: Path,
        command_arguments_list: list[ExomiserCommandLineArguments],
        phenotype_only: bool,
        output_dir: Path,
        batch_prefix: str,
    ):
        self.analysis_yaml = analysis_yaml
        self.command_arguments_list = command_arguments_list
        self.phenotype_only = phenotype_only
        self.output_dir = output_dir
        self.batch_prefix = batch_prefix

    def write_commands(self, commands_writer: CommandsWriter) -> None:
        """Write command arguments to a file."""
        for command_arguments in self.command_arguments_list:
            commands_writer.write_local_commands(self.analysis_yaml, command_arguments)
        commands_writer.close()

    def write_temp_file(self) -> str:
        """Write commands out to a temporary file."""
        temp = tempfile.NamedTemporaryFile(delete=False)
        commands_writer = CommandsWriter(Path(temp.name), self.phenotype_only)
        self.write_commands(commands_writer)
        return temp.name

    def write_all_commands(self) -> None:
        """Write all commands out to a single file."""
        commands_writer = CommandsWriter(
            Path(self.output_dir).joinpath(self.batch_prefix + "-exomiser-batch.txt"),
            self.phenotype_only,
        )
        self.write_commands(commands_writer)

    def create_split_batch_files(self, max_jobs: int) -> None:
        """Split temp file into separate batch files, dependent on the number of max jobs allocated to each file."""
        temp_file_name = self.write_temp_file()
        lines_per_file, f_name = max_jobs, 0
        splitfile = None
        with open(temp_file_name) as tmp_file:
            for lineno, line in enumerate(tmp_file):
                if lineno % lines_per_file == 0:
                    f_name += 1
                    if splitfile:
                        splitfile.close()
                    split_filename = Path(self.output_dir).joinpath(
                        self.batch_prefix + "-exomiser-batch-{}.txt".format(f_name)
                    )
                    splitfile = open(split_filename, "w")
                splitfile.write(line)
            if splitfile:
                splitfile.close()
        tmp_file.close()
        Path(temp_file_name).unlink()


def create_batch_file(
    environment: str,
    analysis: Path,
    phenopacket_dir: Path,
    vcf_dir: Path,
    output_dir: Path,
    batch_prefix: str,
    max_jobs: int,
    phenotype_only: bool,
    results_dir: Path,
    output_options_dir: Path = None,
    output_options_file: Path = None,
) -> None:
    """Create Exomiser batch files."""
    command_arguments = create_command_arguments(
        environment,
        phenopacket_dir,
        phenotype_only,
        vcf_dir,
        results_dir,
        output_options_dir,
        output_options_file,
    )
    BatchFileWriter(
        analysis,
        command_arguments,
        phenotype_only,
        output_dir,
        batch_prefix,
    ).write_all_commands() if max_jobs == 0 else BatchFileWriter(
        analysis,
        command_arguments,
        phenotype_only,
        output_dir,
        batch_prefix,
    ).create_split_batch_files(
        max_jobs
    )


@click.command()
@click.option(
    "--environment",
    "-e",
    required=False,
    default="local",
    show_default=True,
    help="Environment to run commands.",
    type=click.Choice(["local", "docker"]),
)
@click.option(
    "--analysis-yaml",
    "-a",
    required=False,
    metavar="FILE",
    type=Path,
    help="Path to the analysis .yml file.",
)
@click.option(
    "--phenopacket-dir",
    "-P",
    required=True,
    metavar="PATH",
    type=Path,
    help="Path to phenopackets.",
)
@click.option(
    "--vcf-dir",
    "-v",
    required=True,
    metavar="PATH",
    type=Path,
    help="Path to VCF files.",
)
@click.option(
    "--batch-prefix",
    "-b",
    required=False,
    metavar="TEXT",
    help="Prefix of generated batch files.",
    default="RUN",
    show_default=True,
)
@click.option(
    "--max-jobs",
    "-j",
    required=False,
    metavar="<int>",
    type=int,
    default=0,
    show_default=True,
    help="Number of jobs in each file.",
)
@click.option(
    "--phenotype-only",
    type=bool,
    default=False,
    cls=MutuallyExclusiveOptionError,
    mutually_exclusive=["vcf_dir", "analysis_yaml"],
    help="Run Exomiser with phenotype only preset - strongly recommended to run with versions 13.2.0 onwards.",
)
@click.option(
    "--results-dir",
    type=Path,
    required=False,
    help="Results directory for Exomiser results - compatible with versions 13.2.0 onwards.",
)
@click.option(
    "--output-options-dir",
    "-O",
    cls=MutuallyExclusiveOptionError,
    mutually_exclusive=["output_options_file"],
    required=False,
    metavar="PATH",
    type=Path,
    help="Path to the output options directory. ",
)
@click.option(
    "--output-options-file",
    "-o",
    cls=MutuallyExclusiveOptionError,
    mutually_exclusive=["output_options_dir"],
    required=False,
    metavar="FILE",
    type=Path,
    help="Path to the output options file. ",
)
def prepare_exomiser_batch(
    environment: str,
    analysis_yaml: Path,
    phenopacket_dir: Path,
    vcf_dir: Path,
    output_dir: Path,
    batch_prefix: str,
    max_jobs: int,
    phenotype_only: bool,
    output_options_dir: Path = None,
    output_options_file: Path = None,
):
    """Generate Exomiser batch files."""
    Path(output_dir).joinpath("tool_input_commands").mkdir(exist_ok=True)
    create_batch_file(
        environment,
        analysis_yaml,
        phenopacket_dir,
        vcf_dir,
        output_dir,
        batch_prefix,
        max_jobs,
        phenotype_only,
        output_options_dir,
        output_options_file,
    )
