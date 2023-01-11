from pathlib import Path

from pheval.prepare.create_noisy_phenopackets import create_scrambled_phenopackets
from pheval.prepare.create_spiked_vcf import create_spiked_vcfs
from pheval.prepare.update_phenopacket import update_phenopackets

from pheval_exomiser.config_parser import ExomiserConfig


def prepare_updated_phenopackets(testdata_dir: Path, config: ExomiserConfig) -> None:
    """Updates the gene data for phenopackets."""
    if config.prepare.update_phenopacket_gene_identifier.update is True:
        print("...updating phenopacket causative gene data...")
        update_phenopackets(
            phenopacket_dir=testdata_dir.joinpath("phenopackets"),
            gene_identifier=config.prepare.update_phenopacket_gene_identifier.gene_identifer_to_update
        )


def prepare_scrambled_phenopackets(testdata_dir: Path, config: ExomiserConfig):
    """Scrambles the phenopacket phenotypic profiles."""
    if config.prepare.scramble.scramble_phenopacket != 0:
        print("...scrambling phenopacket phenotypic profiles...")
        create_scrambled_phenopackets(output_dir=testdata_dir.joinpath(
            f"scrambled_phenopackets_{config.prepare.scramble.scramble_phenopacket}"
        ),
            output_file_suffix=f"scrambled_{config.prepare.scramble.scramble_phenopacket}",
            phenopacket_dir=testdata_dir.joinpath("phenopackets"),
            scramble_factor=config.prepare.scramble.scramble_phenopacket,
        )


def prepare_spiked_vcfs(testdata_dir: Path, config: ExomiserConfig):
    """Creates spiked vcf files with proband variants."""
    if config.prepare.create_spiked_vcf.spike is True:
        print("...spiking vcfs...")
        create_spiked_vcfs(
            output_dir=testdata_dir.joinpath("vcfs"),
            phenopacket_dir=testdata_dir.joinpath("phenopackets"),
            template_vcf_path=config.prepare.create_spiked_vcf.path_to_template_vcf,
            vcf_dir=config.prepare.create_spiked_vcf.path_to_template_vcf_directory,
        )
