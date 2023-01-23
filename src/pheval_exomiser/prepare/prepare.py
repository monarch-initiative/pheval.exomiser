import shutil
from distutils.dir_util import copy_tree
from pathlib import Path

from pheval.prepare.create_noisy_phenopackets import create_scrambled_phenopackets
from pheval.prepare.create_spiked_vcf import create_spiked_vcfs
from pheval.prepare.update_phenopacket import update_phenopackets

from pheval_exomiser.config_parser import ExomiserConfig


def prepare_updated_phenopackets(
    input_dir: Path, testdata_dir: Path, config: ExomiserConfig
) -> None:
    """Update the gene data for phenopackets."""
    try:
        Path(input_dir).mkdir()
    except FileExistsError:
        pass
    if config.prepare.update_phenopacket_gene_identifier.update is True:
        print("...updating phenopacket causative gene data...")
        update_phenopackets(
            phenopacket_dir=testdata_dir.joinpath("phenopackets"),
            gene_identifier=config.prepare.update_phenopacket_gene_identifier.gene_identifer_to_update,
            output_dir=Path(input_dir),
        )
    else:
        copy_tree(str(testdata_dir.joinpath("phenopackets")), str(input_dir))


def prepare_scrambled_phenopackets(input_dir: Path, testdata_dir: Path, config: ExomiserConfig):
    """Scramble the phenopacket phenotypic profiles."""
    if config.prepare.scramble.scramble_phenopacket != 0:
        print("...scrambling phenopacket phenotypic profiles...")
        create_scrambled_phenopackets(
            output_dir=input_dir.joinpath(
                f"scrambled_phenopackets_{config.prepare.scramble.scramble_phenopacket}"
            ),
            output_file_suffix=f"scrambled_{config.prepare.scramble.scramble_phenopacket}",
            phenopacket_dir=testdata_dir.joinpath("phenopackets"),
            scramble_factor=config.prepare.scramble.scramble_phenopacket,
        )


def prepare_spiked_vcfs(input_dir: Path, testdata_dir: Path, config: ExomiserConfig):
    """Create spiked vcf files with proband variants."""
    if config.prepare.create_spiked_vcf.spike is True:
        print("...spiking vcfs...")
        create_spiked_vcfs(
            output_dir=input_dir.joinpath("vcfs"),
            phenopacket_dir=testdata_dir.joinpath("phenopackets"),
            template_vcf_path=config.prepare.create_spiked_vcf.path_to_template_vcf,
            vcf_dir=config.prepare.create_spiked_vcf.path_to_template_vcf_directory,
        )
    else:
        shutil.copytree(testdata_dir.joinpath("vcfs"), input_dir.joinpath("vcfs"))
