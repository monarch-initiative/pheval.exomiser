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
    vcf_file: Path
    vcf_assembly: str
    output_options_file: Optional[Path] = None


def get_all_files_from_output_opt_directory(output_options_dir: Path) -> list[Path] or None:
    """Obtain all output options files if directory is specified - otherwise returns none."""
    return None if output_options_dir is None else all_files(output_options_dir)


# def edit_output_options_file_output_prefix(output_options_file: Path, phenopacket_path: Path) -> Path:
#     with open(output_options_file) as output_options:
#         output_opt = yaml.safe_load(output_options)
#     output_options.close()
#     output_opt['outputPrefix'] = output_options_file.absolute().parents[0].joinpath(phenopacket_path.stem)
#     with open
#     (output_options_file.absolute().parents[0].joinpath(phenopacket_path.stem + "-" + str(output_options_file.name)),
#               'w') as correct_prefixed:
#         yaml.dump(output_opt, correct_prefixed)
#     correct_prefixed.close()
#     return
#     output_options_file.absolute().parents[0].joinpath(phenopacket_path.stem + "-" + str(output_options_file.name))


class CommandCreator:
    """Create a command for a phenopacket."""

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

    def add_command_line_arguments(self, vcf_dir: Path) -> ExomiserCommandLineArguments:
        """Return a dataclass of all the command line arguments corresponding to phenopacket sample."""
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
    """Return a list of Exomiser command line arguments for a directory of phenopackets."""
    phenopacket_paths = files_with_suffix(phenopacket_dir, ".json")
    commands = []
    output_option_dir_files = get_all_files_from_output_opt_directory(output_options_dir)
    for phenopacket_path in phenopacket_paths:
        phenopacket = phenopacket_reader(phenopacket_path)
        # output_options_file = edit_output_options_file_output_prefix(output_options_file,
        #                                                              phenopacket_path) if output_options_file \
        #                                                                                   is not None else None
        commands.append(
            CommandCreator(
                phenopacket_path, phenopacket, output_option_dir_files, output_options_file
            ).add_command_line_arguments(vcf_dir)
        )
    return commands


class CommandsWriter:
    """Write a command to file."""

    def __init__(self, file: Path):
        self.file = open(file, "a")

    def write_command(
        self, analysis_yaml: Path, command_arguments: ExomiserCommandLineArguments
    ) -> None:
        """Write a command out for exomiser to run."""
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

    def write_docker_command(
        self, analysis_yaml: Path, command_arguments: ExomiserCommandLineArguments
    ) -> None:
        """Write a docker command out for exomiser to run."""
        try:
            self.file.write(
                "--analysis "
                + str("/exomiser-yaml-template/" + Path(analysis_yaml).name)
                + " --sample "
                + str("/exomiser-testdata-phenopacket/" + command_arguments.sample.name)
                + " --vcf "
                + str("/exomiser-testdata-vcf/" + command_arguments.vcf_file.name)
                + " --assembly "
                + command_arguments.vcf_assembly
                + "\n"
            )
        except IOError:
            print("Error writing ", self.file)

    def write_command_output_options(
        self, analysis_yaml, command_arguments: ExomiserCommandLineArguments
    ) -> None:
        """Write a command out for exomiser to run - including output option file specified."""
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

    def write_docker_command_output_options(
        self, analysis_yaml, command_arguments: ExomiserCommandLineArguments
    ) -> None:
        """Write a docker command out for exomiser to run - including output option file specified."""
        try:
            self.file.write(
                "--analysis "
                + str("/exomiser-yaml-template/" + analysis_yaml.name)
                + " --sample "
                + str("/exomiser-testdata-phenopacket/" + command_arguments.sample.name)
                + " --vcf "
                + str("/exomiser-testdata-vcf/" + command_arguments.vcf_file.name)
                + " --assembly "
                + command_arguments.vcf_assembly
                + " --output "
                + str(
                    "/exomiser-testdata-output-options/"
                    + command_arguments.output_options_file.name
                )
                + "\n"
            )
        except IOError:
            print("Error writing ", self.file)

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
        output_dir: Path,
        batch_prefix: str,
    ):
        self.analysis_yaml = analysis_yaml
        self.command_arguments_list = command_arguments_list
        self.output_dir = output_dir
        self.batch_prefix = batch_prefix

    def write_commands(self, commands_writer: CommandsWriter) -> None:
        """Write command arguments to a file."""
        for command_arguments in self.command_arguments_list:
            commands_writer.write_command(
                self.analysis_yaml, command_arguments
            ) if command_arguments.output_options_file is None else commands_writer.write_command_output_options(
                self.analysis_yaml, command_arguments
            )
        commands_writer.close()

    def write_docker_commands(self, commands_writer: CommandsWriter) -> None:
        """Write docker command arguments to a file."""
        for command_arguments in self.command_arguments_list:
            commands_writer.write_docker_command(
                self.analysis_yaml, command_arguments
            ) if command_arguments.output_options_file is None else commands_writer.write_docker_command_output_options(
                self.analysis_yaml, command_arguments
            )
        commands_writer.close()

    def write_temp_file(self) -> str:
        """Write commands out to a temporary file."""
        temp = tempfile.NamedTemporaryFile(delete=False)
        commands_writer = CommandsWriter(Path(temp.name))
        self.write_commands(commands_writer)
        return temp.name

    def write_docker_temp_file(self) -> str:
        """Write docker commands out to a temporary file."""
        temp = tempfile.NamedTemporaryFile(delete=False)
        commands_writer = CommandsWriter(Path(temp.name))
        self.write_docker_commands(commands_writer)
        return temp.name

    def write_all_commands(self) -> None:
        """Write all commands out to a single file."""
        commands_writer = CommandsWriter(
            Path(self.output_dir).joinpath(self.batch_prefix + "-exomiser-batch.txt")
        )
        self.write_commands(commands_writer)

    def write_all_docker_commands(self) -> None:
        """Write all docker commands out to a single file."""
        commands_writer = CommandsWriter(
            Path(self.output_dir).joinpath(self.batch_prefix + "-exomiser-batch.txt")
        )
        self.write_docker_commands(commands_writer)

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

    def create_docker_split_batch_files(self, max_jobs: int) -> None:
        """Split temp file into separate batch files, dependent on the number of max jobs allocated to each file."""
        temp_file_name = self.write_docker_temp_file()
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
    output_options_dir: Path = None,
    output_options_file: Path = None,
) -> None:
    """Create Exomiser batch files."""
    try:
        Path(output_dir).joinpath("exomiser_batch_files").mkdir()
    except FileExistsError:
        pass
    command_arguments = create_command_arguments(
        phenopacket_dir, vcf_dir, output_options_dir, output_options_file
    )
    if environment == "local":
        BatchFileWriter(
            analysis, command_arguments, output_dir.joinpath("exomiser_batch_files/"), batch_prefix
        ).write_all_commands() if max_jobs == 0 else BatchFileWriter(
            analysis, command_arguments, output_dir.joinpath("exomiser_batch_files/"), batch_prefix
        ).create_split_batch_files(
            max_jobs
        )
    elif environment == "docker":
        BatchFileWriter(
            analysis, command_arguments, output_dir.joinpath("exomiser_batch_files/"), batch_prefix
        ).write_all_docker_commands() if max_jobs == 0 else BatchFileWriter(
            analysis, command_arguments, output_dir.joinpath("exomiser_batch_files/"), batch_prefix
        ).create_docker_split_batch_files(
            max_jobs
        )
    else:
        raise EnvironmentError


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
    environment: str,
    analysis_yaml: Path,
    phenopacket_dir: Path,
    vcf_dir: Path,
    output_dir: Path,
    batch_prefix,
    max_jobs,
    output_options_dir: Path = None,
    output_options_file: Path = None,
):
    """Generate Exomiser batch files."""
    create_batch_file(
        environment,
        analysis_yaml,
        phenopacket_dir,
        vcf_dir,
        output_dir,
        batch_prefix,
        max_jobs,
        output_options_dir,
        output_options_file,
    )
