from copy import copy
from pathlib import Path

import click
import pandas as pd
import yaml
from google.protobuf.timestamp_pb2 import Timestamp
from oaklib.implementations.pronto.pronto_implementation import ProntoImplementation
from oaklib.resource import OntologyResource
from phenopackets import (
    Diagnosis,
    Family,
    File,
    GeneDescriptor,
    GenomicInterpretation,
    Individual,
    Interpretation,
    MetaData,
    OntologyClass,
    Pedigree,
    Phenopacket,
    PhenotypicFeature,
    Resource,
    VariantInterpretation,
    VariationDescriptor,
    VcfRecord,
)
from pheval.prepare.create_noisy_phenopackets import load_ontology
from pheval.utils.file_utils import files_with_suffix
from pheval.utils.phenopacket_utils import create_hgnc_dict, write_phenopacket


def load_genotype_ontology():
    """Load genotype ontology"""
    genotype_resource = OntologyResource(slug="geno.owl", local=False)
    return ProntoImplementation(genotype_resource)


def exomiser_analysis_yml_reader(yaml_job_file_path: Path) -> dict:
    """Read an exomiser analysis yaml file."""
    with open(yaml_job_file_path) as yaml_job_file:
        yaml_job = yaml.safe_load(yaml_job_file)
    yaml_job_file.close()
    return yaml_job


def read_diagnoses_file(diagnoses_file_path: Path) -> pd.DataFrame:
    """Read a diagnoses file."""
    return pd.read_csv(diagnoses_file_path, delimiter="t")


def read_pedigree_file(pedigree_path: Path) -> list[str]:
    """Return the contents of a pedigree file"""
    return open(pedigree_path).readlines()


class ExomiserYamlToPhenopacketConverter:
    def __init__(self, genotype_ontology, human_phenotype_ontology, hgnc_data):
        self.genotype_ontology = genotype_ontology
        self.human_phenotype_ontology = human_phenotype_ontology
        self.hgnc_data = hgnc_data

    @staticmethod
    def construct_individual(yaml_job: dict, diagnoses: pd.DataFrame) -> Individual:
        """Construct individual for phenopacket."""
        return Individual(
            id=yaml_job["analysis"]["proband"],
            sex=diagnoses[diagnoses.ProbandId == yaml_job["analysis"]["proband"]]
            .iloc[0]["Sex"]
            .upper(),
        )

    @staticmethod
    def get_diagnoses_for_proband(yaml_job: dict, diagnoses: pd.DataFrame):
        """Get all diagnoses for proband."""
        return diagnoses.loc[diagnoses["ProbandId"] == yaml_job["analysis"]["proband"]]

    def construct_phenotypic_interpretations(self, yaml_job: dict) -> list[PhenotypicFeature]:
        """Construct the phenotypic features for the proband."""
        hpo_ids = yaml_job["analysis"]["hpoIds"]
        phenotypic_features = []
        for hpo_id in hpo_ids:
            try:
                rels = self.human_phenotype_ontology.entity_alias_map(hpo_id)
                hpo_term = "".join(rels[(list(rels.keys())[0])])
                hpo = PhenotypicFeature(type=OntologyClass(id=hpo_id, label=hpo_term))
                phenotypic_features.append(hpo)
            except AttributeError:
                hpo = PhenotypicFeature(type=OntologyClass(id=hpo_id))
                phenotypic_features.append(hpo)
        return phenotypic_features

    @staticmethod
    def construct_vcf_record(yaml_job: dict, diagnosis: pd.DataFrame) -> VcfRecord:
        """Construct the VCF record for a diagnosis."""
        return VcfRecord(
            genome_assembly=yaml_job["analysis"]["genomeAssembly"],
            chrom=diagnosis["Chr"],
            pos=int(diagnosis["Start"]),
            ref=str(diagnosis["Ref/Alt"]).split("/")[0],
            alt=str(diagnosis["Ref/Alt"]).split("/")[1],
        )

    def construct_allelic_state(self, diagnosis: pd.DataFrame) -> OntologyClass:
        """Construct the allelic state for a diagnosis."""
        return OntologyClass(
            id=list(self.genotype_ontology.basic_search(diagnosis["Genotype"].lower()))[0],
            label=diagnosis["Genotype"].lower(),
        )

    def construct_gene_descriptor(self, diagnosis: pd.DataFrame) -> GeneDescriptor:
        """Construct the Gene Descriptor for a diagnosis."""
        try:
            return GeneDescriptor(
                value_id=self.hgnc_data[diagnosis["Gene"]]["ensembl_id"],
                symbol=diagnosis["Gene"],
            )
        except KeyError:
            for _gene, gene_info in self.hgnc_data.items():
                for previous_name in gene_info["previous_names"]:
                    if diagnosis["Gene"] == previous_name:
                        return GeneDescriptor(
                            value_id=self.hgnc_data[gene_info["ensembl_id"]],
                            symbol=diagnosis["Gene"],
                        )

    def construct_variation_descriptor(
        self, yaml_job: dict, diagnosis: pd.DataFrame
    ) -> VariationDescriptor:
        """Construct a variation descriptor for a diagnosis."""
        return VariationDescriptor(
            id=yaml_job["analysis"]["proband"]
            + ":"
            + diagnosis["Chr"]
            + ":"
            + diagnosis["Start"]
            + ":"
            + diagnosis["Ref/Alt"],
            gene_context=self.construct_gene_descriptor(diagnosis),
            vcf_record=self.construct_vcf_record(yaml_job, diagnosis),
            allelic_state=self.construct_allelic_state(diagnosis),
        )

    def construct_variant_interpretation(
        self, yaml_job: dict, diagnosis: pd.DataFrame
    ) -> VariantInterpretation:
        """Construct the variant interpretation for a diagnosis."""
        return VariantInterpretation(
            variation_descriptor=self.construct_variation_descriptor(yaml_job, diagnosis),
        )

    def construct_genomic_interpretations(
        self, yaml_job: dict, diagnoses: pd.DataFrame
    ) -> list[GenomicInterpretation]:
        """Construct a list of genomic interpretations for a proband."""
        genomic_interpretations = []
        for _index, row in self.get_diagnoses_for_proband(yaml_job, diagnoses).iterrows():
            genomic_interpretation = GenomicInterpretation(
                subject_or_biosample_id=yaml_job["analysis"]["proband"],
                variant_interpretation=self.construct_variant_interpretation(
                    yaml_job=yaml_job, diagnosis=row
                ),
            )
            genomic_interpretations.append(genomic_interpretation)
        return genomic_interpretations

    def construct_diagnosis(self, yaml_job: dict, diagnoses: pd.DataFrame) -> Diagnosis:
        """Construct the diagnosis for a proband."""
        return Diagnosis(
            genomic_interpretations=self.construct_genomic_interpretations(yaml_job, diagnoses)
        )

    def construct_interpretations(
        self, yaml_job: dict, diagnoses: pd.DataFrame
    ) -> list[Interpretation]:
        """Construct interpretations for a proband."""
        return [
            Interpretation(
                id=yaml_job["analysis"]["proband"] + "-interpretation",
                diagnosis=self.construct_diagnosis(yaml_job, diagnoses),
            )
        ]

    @staticmethod
    def construct_meta_data() -> MetaData:
        """Construct the meta-data."""
        timestamp = Timestamp()
        timestamp.GetCurrentTime()
        return MetaData(
            created=timestamp,
            created_by="pheval-converter",
            resources=[
                Resource(
                    id="hp",
                    name="human phenotype ontology",
                    url="http://purl.obolibrary.org/obo/hp.owl",
                    version="hp/releases/2019-11-08",
                    namespace_prefix="HP",
                    iri_prefix="http://purl.obolibrary.org/obo/HP_",
                )
            ],
            phenopacket_schema_version="2.0",
        )

    @staticmethod
    def construct_files(yaml_job_file: dict) -> list[File]:
        """Construct the files."""
        return [
            File(
                uri=yaml_job_file["analysis"]["vcf"],
                file_attributes={
                    "fileFormat": "VCF",
                    "genomeAssembly": yaml_job_file["analysis"]["genomeAssembly"],
                },
            )
        ]


def construct_pedigree(pedigree: list[str]) -> tuple[str, Pedigree]:
    """Construct the pedigree message from a ped file."""
    persons = []
    family_id = None
    for individual in pedigree:
        entry = individual.split("\t")
        family_id = entry[0]
        sex = "."
        if (
            int(entry[4]) == 1
        ):  # until this is fixed with the phenopackets package, sex has to be reassigned
            sex = 2
        if int(entry[4]) == 2:
            sex = 1
        if str(entry[3]) == "0" and str(entry[2]) == "0":
            person = Pedigree.Person(
                family_id=family_id, individual_id=entry[1], sex=sex, affected_status=int(entry[5])
            )
            persons.append(person)
        if str(entry[3]) == "0" and str(entry[2]) != "0":
            person = Pedigree.Person(
                family_id=family_id,
                individual_id=entry[1],
                paternal_id=entry[2],
                sex=sex,
                affected_status=int(entry[5]),
            )
            persons.append(person)
        if str(entry[2]) == "0" and str(entry[3]) != "0":
            person = Pedigree.Person(
                family_id=family_id,
                individual_id=entry[1],
                maternal_id=entry[3],
                sex=sex,
                affected_status=int(entry[5]),
            )
            persons.append(person)
        if str(entry[2]) != "0" and str(entry[3] != "0"):
            person = Pedigree.Person(
                family_id=family_id,
                individual_id=entry[1],
                paternal_id=entry[2],
                maternal_id=entry[3],
                sex=sex,
                affected_status=int(entry[5]),
            )
            persons.append(person)
    return family_id, Pedigree(persons=persons)


def construct_phenopacket(
    yaml_job_file: dict,
    diagnoses: pd.DataFrame,
    exomiser_yaml_to_phenopacket_converter: ExomiserYamlToPhenopacketConverter,
) -> Phenopacket:
    """Construct a phenopacket."""
    return Phenopacket(
        id=yaml_job_file["analysis"]["proband"],
        subject=exomiser_yaml_to_phenopacket_converter.construct_individual(
            yaml_job=yaml_job_file, diagnoses=diagnoses
        ),
        phenotypic_features=exomiser_yaml_to_phenopacket_converter.construct_phenotypic_interpretations(
            yaml_job=yaml_job_file
        ),
        interpretations=exomiser_yaml_to_phenopacket_converter.construct_interpretations(
            yaml_job=yaml_job_file, diagnoses=diagnoses
        ),
        files=exomiser_yaml_to_phenopacket_converter.construct_files(yaml_job_file),
        meta_data=exomiser_yaml_to_phenopacket_converter.construct_meta_data(),
    )


def construct_family(
    yaml_job_file: dict,
    diagnoses: pd.DataFrame,
    exomiser_yaml_to_phenopacket_converter: ExomiserYamlToPhenopacketConverter,
    pedigree: list[str],
) -> Family:
    """Construct a Family"""
    phenopacket = construct_phenopacket(
        yaml_job_file, diagnoses, exomiser_yaml_to_phenopacket_converter
    )
    proband = copy(phenopacket)
    del proband.files[:]
    del proband.meta_data[:]
    family_id, ped = construct_pedigree(pedigree)
    return Family(
        id=family_id,
        proband=proband,
        pedigree=ped,
        files=phenopacket.files,
        meta_data=phenopacket.meta_data,
    )


def create_phenopacket(
    yaml_job_file: Path,
    diagnoses: pd.DataFrame,
    exomiser_converter: ExomiserYamlToPhenopacketConverter,
) -> Phenopacket or Family:
    """Construct either a family or phenopacket from an analysis yaml."""
    yaml_job = exomiser_analysis_yml_reader(yaml_job_file)
    phenopacket = (
        construct_phenopacket(yaml_job, diagnoses, exomiser_converter)
        if yaml_job["analysis"]["ped"] == ""
        else construct_family(
            yaml_job,
            diagnoses,
            exomiser_converter,
            read_pedigree_file(yaml_job["analysis"]["ped"]),
        )
    )
    return phenopacket


@click.command()
@click.option(
    "--directory",
    "-d",
    required=True,
    help="Directory for Exomiser yaml job files to be converted.",
    type=Path,
)
@click.option("--diagnoses-file", "-d", required=True, help="Diagnoses file", type=Path)
@click.option(
    "--output-dir", "-o", required=True, help="Output directory to write phenopackets", type=Path
)
def convert_exomiser_analysis_yamls_to_phenopacket(
    output_dir: Path, directory: Path, diagnoses_file: Path
):
    """Convert an Exomiser YAML file to a phenopacket schema given a .tsv diagnoses file containing the following
    required fields: ..."""
    try:
        output_dir.mkdir()
    except FileExistsError:
        pass
    diagnoses = read_diagnoses_file(diagnoses_file)
    exomiser_converter = ExomiserYamlToPhenopacketConverter(
        load_genotype_ontology(), load_ontology(), create_hgnc_dict()
    )
    for yaml_job_file in files_with_suffix(directory, ".yml"):
        phenopacket = create_phenopacket(yaml_job_file, diagnoses, exomiser_converter)
        write_phenopacket(
            phenopacket, output_dir.joinpath(yaml_job_file.name.replace(".yml", ".json"))
        )


@click.command()
@click.option(
    "--yaml-file",
    "-y",
    required=True,
    help="Path to Exomiser analysis yaml file for phenopacket conversion.",
    type=Path,
)
@click.option("--diagnoses-file", "-d", required=True, help="Diagnoses file", type=Path)
@click.option(
    "--output-dir", "-o", required=True, help="Output directory to write phenopackets", type=Path
)
def convert_exomiser_analysis_yaml_to_phenopacket(
    output_dir: Path, yaml_file: Path, diagnoses_file: Path
):
    """Convert Exomiser YAML files to the phenopacket schema given a .tsv diagnoses file containing the following
    required fields: ..."""
    try:
        output_dir.mkdir()
    except FileExistsError:
        pass
    diagnoses = read_diagnoses_file(diagnoses_file)
    exomiser_converter = ExomiserYamlToPhenopacketConverter(
        load_genotype_ontology(), load_ontology(), create_hgnc_dict()
    )
    phenopacket = create_phenopacket(yaml_file, diagnoses, exomiser_converter)
    write_phenopacket(phenopacket, Path(yaml_file.name + ".json"))
