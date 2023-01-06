#!/usr/bin/python
import difflib
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click
from phenopackets import Family, Phenopacket

# TODO once merged into pheval main branch I can import these as seen in the runner.py file instead of having duplicates
from .custom_exceptions import MutuallyExclusiveOptionError
from ..utils.file_utils import all_files, files_with_suffix
from ..utils.phenopacket_utils import PhenopacketUtil, phenopacket_reader


# TODO consider the application.properties and the specification of a PED file
@dataclass
class ExomiserCommandLineArguments:
    """Stores command line arguments for each phenopacket to be run with Exomiser."""

    sample: Path
    vcf_file: Path
    vcf_assembly: str
    output_options_file: Optional[Path] = None


def get_all_files_from_output_opt_directory(output_options_dir: Path) -> list[Path] or None:
    """Obtains all output options files if directory is specified - otherwise returns none."""
    return None if output_options_dir is None else all_files(output_options_dir)


class CommandCreator:
    """Creates a command for a phenopacket."""

    def __init__(
        self,
        phenopacket_path: Path,
        phenopacket: Phenopacket or Family,
        output_options_dir_files: list[Path] or None,
        output_options_file: Path or None,
    ):
        self.phenopacket_path = phenopacket_path
        self.phenopacket = phenopacket
        self.output_options_dir_files = output_options_dir_files
        self.output_options_file = output_options_file

    def find_output_options_file_from_dir(self, output_option_file_paths: list[Path]) -> Path:
        """If a directory for output options corresponding to phenopackets is specified - selects the closest file name
        match for output argument."""
        closest_file_match = Path(
            str(
                difflib.get_close_matches(
                    str(self.phenopacket_path.name),
                    [
                        str(output_option_path.name)
                        for output_option_path in output_option_file_paths
                    ],
                )[0]
            )
        )
        return [
            output_option_path
            for output_option_path in output_option_file_paths
            if Path(closest_file_match) == Path(output_option_path.name)
        ][0]

    def assign_output_options_file(self) -> Path or None:
        """If a single output option file is to specified to all phenopackets, returns its path,
        otherwise finds the best match from the directory."""
        if self.output_options_dir_files is None and self.output_options_file is None:
            return None
        else:
            return (
                self.output_options_file
                if self.output_options_dir_files is None
                else self.find_output_options_file_from_dir(self.output_options_dir_files)
            )

    def add_command_line_arguments(self, vcf_dir: Path) -> ExomiserCommandLineArguments:
        """Returns a dataclass of all the command line arguments corresponding to phenopacket sample."""
        vcf_file_data = PhenopacketUtil(self.phenopacket).vcf_file_data(
            self.phenopacket_path, vcf_dir
        )
        output_options_file = self.assign_output_options_file()
        if output_options_file is None:
            return ExomiserCommandLineArguments(
                sample=Path(self.phenopacket_path),
                vcf_file=Path(vcf_file_data.uri),
                vcf_assembly=vcf_file_data.file_attributes["genomeAssembly"],
            )
        if output_options_file is not None:
            return ExomiserCommandLineArguments(
                sample=Path(self.phenopacket_path),
                vcf_file=Path(vcf_file_data.uri),
                vcf_assembly=vcf_file_data.file_attributes["genomeAssembly"],
                output_options_file=output_options_file,
            )


def create_command_arguments(
    phenopacket_dir: Path,
    vcf_dir: Path,
    output_options_dir: Path or None = None,
    output_options_file: Path or None = None,
) -> list[ExomiserCommandLineArguments]:
    """Returns a list of Exomiser command line arguments for a directory of phenopackets."""
    phenopacket_paths = files_with_suffix(phenopacket_dir, ".json")
    commands = []
    output_option_dir_files = get_all_files_from_output_opt_directory(output_options_dir)
    for phenopacket_path in phenopacket_paths:
        phenopacket = phenopacket_reader(phenopacket_path)
        commands.append(
            CommandCreator(
                phenopacket_path, phenopacket, output_option_dir_files, output_options_file
            ).add_command_line_arguments(vcf_dir)
        )
    return commands


class CommandsWriter:
    """Writes a command out to file."""

    def __init__(self, file: Path):
        self.file = open(file, "a")

    def write_command(
        self, analysis_yaml: Path, command_arguments: ExomiserCommandLineArguments
    ) -> None:
        """Writes a command out for exomiser to run."""
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
                + "\n"
            )
        except IOError:
            print("Error writing ", self.file)

    def write_command_output_options(
        self, analysis_yaml, command_arguments: ExomiserCommandLineArguments
    ) -> None:
        """Writes a command out for exomiser to run - including output option file specified."""
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
                + " --output "
                + str(command_arguments.output_options_file)
                + "\n"
            )
        except IOError:
            print("Error writing ", self.file)

    def close(self) -> None:
        try:
            self.file.close()
        except IOError:
            print("Error closing ", self.file)


class BatchFileWriter:
    """Writes all the commands out to a batch file."""

    def __init__(
        self,
        analysis_yaml: Path,
        command_arguments_list: list[ExomiserCommandLineArguments],
        batch_prefix: str,
    ):
        self.analysis_yaml = analysis_yaml
        self.command_arguments_list = command_arguments_list
        self.batch_prefix = batch_prefix

    def write_commands(self, commands_writer: CommandsWriter) -> None:
        """Writes command arguments to a file."""
        for command_arguments in self.command_arguments_list:
            commands_writer.write_command(
                self.analysis_yaml, command_arguments
            ) if command_arguments.output_options_file is None else commands_writer.write_command_output_options(
                self.analysis_yaml, command_arguments
            )
        commands_writer.close()

    def write_temp_file(self) -> str:
        """Writes commands out to a temporary file."""
        temp = tempfile.NamedTemporaryFile(delete=False)
        commands_writer = CommandsWriter(Path(temp.name))
        self.write_commands(commands_writer)
        return temp.name

    def write_all_commands(self) -> None:
        """Writes all commands out to a single file."""
        commands_writer = CommandsWriter(Path(self.batch_prefix + "-exomiser-batch.txt"))
        self.write_commands(commands_writer)

    def create_split_batch_files(self, max_jobs: int) -> None:
        """Splits temp file into separate batch files, dependent on the number of max jobs allocated to each file."""
        temp_file_name = self.write_temp_file()
        lines_per_file, f_name = max_jobs, 0
        splitfile = None
        with open(temp_file_name) as tmp_file:
            for lineno, line in enumerate(tmp_file):
                if lineno % lines_per_file == 0:
                    f_name += 1
                    if splitfile:
                        splitfile.close()
                    split_filename = self.batch_prefix + "-exomiser-batch-{}.txt".format(f_name)
                    splitfile = open(split_filename, "w")
                splitfile.write(line)
            if splitfile:
                splitfile.close()
        tmp_file.close()
        Path(temp_file_name).unlink()


def create_batch_file(
    analysis: Path,
    phenopacket_dir: Path,
    vcf_dir: Path,
    batch_prefix: str,
    max_jobs: int,
    output_options_dir: Path = None,
    output_options_file: Path = None,
) -> None:
    """Creates Exomiser batch files."""
    command_arguments = create_command_arguments(
        phenopacket_dir, vcf_dir, output_options_dir, output_options_file
    )
    BatchFileWriter(
        analysis, command_arguments, batch_prefix
    ).write_all_commands() if max_jobs == 0 else BatchFileWriter(
        analysis, command_arguments, batch_prefix
    ).create_split_batch_files(
        max_jobs
    )


@click.command()
@click.option(
    "--analysis-yaml",
    "-a",
    required=True,
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
    analysis_yaml: Path,
    phenopacket_dir: Path,
    vcf_dir: Path,
    batch_prefix,
    max_jobs,
    output_options_dir: Path = None,
    output_options_file: Path = None,
):
    """Generate Exomiser batch files."""
    create_batch_file(
        analysis_yaml,
        phenopacket_dir,
        vcf_dir,
        batch_prefix,
        max_jobs,
        output_options_dir,
        output_options_file,
    )
