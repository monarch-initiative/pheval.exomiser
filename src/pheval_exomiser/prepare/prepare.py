import configparser
from pathlib import Path

from pheval.prepare.create_noisy_phenopackets import create_scrambled_phenopackets
from pheval.prepare.create_spiked_vcf import create_spiked_vcfs_for_phenopackets
from pheval.prepare.update_phenopacket import update_phenopackets_causative_genes


def read_config(config_path: Path):
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def prepare_updated_phenopackets(testdatadir: Path, config_path: Path):
    config = read_config(config_path)
    print("...updating phenopacket causative gene data...") if config["PREPARE"][
        "UpdatePhenopacketGeneData"
    ] == "yes" else print("")
    update_phenopackets_causative_genes(
        phenopacket_dir=testdatadir.joinpath("phenopackets"),
        gene_identifier=config["PREPARE"]["GeneIdentifierToUpdate"],
    ) if config["PREPARE"]["UpdatePhenopacketGeneData"] == "yes" else None


def prepare_scrambled_phenopackets(testdatadir: Path, config_path: Path):
    config = read_config(config_path)
    print("...scrambling phenopackets...") if config["PREPARE"][
        "ScramblePhenopacket"
    ] == "yes" else print("")
    create_scrambled_phenopackets(
        output_dir=testdatadir.joinpath("scrambled_phenopackets"),
        output_file_suffix="scrambled",
        phenopacket_dir=testdatadir.joinpath("phenopackets"),
        scramble_factor=float(config["PREPARE"]["ScramblePhenopacketScrambleFactor"]),
    ) if config["PREPARE"]["ScramblePhenopacket"] == "yes" else None


def prepare_spiked_vcfs(testdatadir: Path, config_path: Path):
    config = read_config(config_path)
    print("...spiking vcfs...") if config["PREPARE"]["CreateSpikedVcf"] == "yes" else print("")
    vcf_dir = (
        None
        if config["PREPARE"]["PathToTemplateVcfDirectory"] == ""
        else Path(config["PREPARE"]["PathToTemplateVcfDirectory"])
    )
    template_vcf = (
        None
        if config["PREPARE"]["PathToTemplateVcf"] == ""
        else Path(config["PREPARE"]["PathToTemplateVcf"])
    )
    create_spiked_vcfs_for_phenopackets(
        output_dir=testdatadir.joinpath("vcfs"),
        phenopacket_dir=testdatadir.joinpath("phenopackets"),
        template_vcf_path=template_vcf,
        vcf_dir=vcf_dir,
    ) if config["PREPARE"]["CreateSpikedVcf"] == "yes" else None
