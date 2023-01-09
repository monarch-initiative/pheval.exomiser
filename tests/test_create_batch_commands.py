import unittest
from pathlib import Path

from phenopackets import (
    Diagnosis,
    File,
    GeneDescriptor,
    GenomicInterpretation,
    Individual,
    Interpretation,
    MetaData,
    OntologyClass,
    Phenopacket,
    PhenotypicFeature,
    Resource,
    VariantInterpretation,
    VariationDescriptor,
    VcfRecord,
)

from pheval_exomiser.prepare.create_batch_commands import (
    CommandCreator,
    ExomiserCommandLineArguments,
)

interpretations = [
    Interpretation(
        id="test-subject-1-int",
        progress_status="SOLVED",
        diagnosis=Diagnosis(
            genomic_interpretations=[
                GenomicInterpretation(
                    subject_or_biosample_id="test-subject-1",
                    interpretation_status=4,
                    variant_interpretation=VariantInterpretation(
                        acmg_pathogenicity_classification="NOT_PROVIDED",
                        therapeutic_actionability="UNKNOWN_ACTIONABILITY",
                        variation_descriptor=VariationDescriptor(
                            gene_context=GeneDescriptor(value_id="NCBIGene:2245", symbol="FGD1"),
                            vcf_record=VcfRecord(
                                genome_assembly="GRCh37",
                                chrom="X",
                                pos=54492285,
                                ref="C",
                                alt="T",
                            ),
                            allelic_state=OntologyClass(
                                id="GENO:0000134",
                                label="hemizygous",
                            ),
                        ),
                    ),
                ),
                GenomicInterpretation(
                    subject_or_biosample_id="test-subject-1",
                    interpretation_status=4,
                    variant_interpretation=VariantInterpretation(
                        acmg_pathogenicity_classification="NOT_PROVIDED",
                        therapeutic_actionability="UNKNOWN_ACTIONABILITY",
                        variation_descriptor=VariationDescriptor(
                            gene_context=GeneDescriptor(value_id="HGNC:18654", symbol="RTTN"),
                            vcf_record=VcfRecord(
                                genome_assembly="GRCh37",
                                chrom="18",
                                pos=67691994,
                                ref="G",
                                alt="A",
                            ),
                            allelic_state=OntologyClass(
                                id="GENO:0000402", label="compound heterozygous"
                            ),
                        ),
                    ),
                ),
            ]
        ),
    )
]
phenotypic_features_with_excluded = [
    PhenotypicFeature(type=OntologyClass(id="HP:0000256", label="Macrocephaly")),
    PhenotypicFeature(type=OntologyClass(id="HP:0002059", label="Cerebral atrophy")),
    PhenotypicFeature(type=OntologyClass(id="HP:0100309", label="Subdural hemorrhage")),
    PhenotypicFeature(type=OntologyClass(id="HP:0003150", label="Glutaric aciduria")),
    PhenotypicFeature(type=OntologyClass(id="HP:0001332", label="Dystonia")),
    PhenotypicFeature(
        type=OntologyClass(id="HP:0008494", label="Inferior lens subluxation"), excluded=True
    ),
]
phenopacket_files = [
    File(
        uri="test/path/to/test_1.vcf",
        file_attributes={"fileFormat": "VCF", "genomeAssembly": "GRCh37"},
    ),
    File(
        uri="test_1.ped",
        file_attributes={"fileFormat": "PED", "genomeAssembly": "GRCh37"},
    ),
]
phenopacket_metadata = MetaData(
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

phenopacket = Phenopacket(
    id="test-subject",
    subject=Individual(id="test-subject-1", sex=1),
    phenotypic_features=phenotypic_features_with_excluded,
    interpretations=interpretations,
    files=phenopacket_files,
    meta_data=phenopacket_metadata,
)

output_options_files = [
    Path("/full/path/to/some/alternate/output_options/phenopacket-output-options.json"),
    Path("/full/path/to/some/alternate/output_options/phenopacket2-output-options.json"),
    Path("/full/path/to/some/alternate/output_options/phenopacket3-output-options.json"),
    Path("/full/path/to/some/alternate/output_options/randomised_phenopacket-output-options.json"),
]


class TestCommandCreator(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.no_output_options = CommandCreator(
            Path("/full/path/to/phenopacket.json"), phenopacket, None, None
        )
        cls.output_options_file = CommandCreator(
            Path("/full/path/to/phenopacket.json"),
            phenopacket,
            None,
            Path("/full/path/to/output/option/file.json"),
        )
        cls.output_options_dir = CommandCreator(
            Path("/full/path/to/phenopacket.json"),
            phenopacket,
            output_options_files,
            None,
        )

    # def test_find_output_options_file_from_dir(self):
    #     self.assertEqual(
    #         self.output_options_dir.find_output_options_file_from_dir(output_options_files),
    #         Path("/full/path/to/some/alternate/output_options/phenopacket-output-options.json"),
    #     )

    def test_assign_output_options_file_none_specified(self):
        self.assertEqual(self.no_output_options.assign_output_options_file(), None)

    def test_assign_output_options_file_file_specified(self):
        self.assertEqual(
            self.output_options_file.assign_output_options_file(),
            Path("/full/path/to/output/option/file.json"),
        )

    def test_assign_output_options_file_directory_specified(self):
        self.assertEqual(
            self.output_options_dir.assign_output_options_file(),
            Path("/full/path/to/some/alternate/output_options/phenopacket-output-options.json"),
        )

    def test_add_command_line_arguments_no_output_options(self):
        self.assertEqual(
            self.no_output_options.add_command_line_arguments(Path("/full/path/to/vcf_dir")),
            ExomiserCommandLineArguments(
                sample=Path("/full/path/to/phenopacket.json"),
                vcf_file=Path("/full/path/to/vcf_dir/test_1.vcf"),
                vcf_assembly="GRCh37",
                output_options_file=None,
            ),
        )

    def test_add_command_line_arguments_output_options_file(self):
        self.assertEqual(
            self.output_options_file.add_command_line_arguments(Path("/full/path/to/vcf_dir")),
            ExomiserCommandLineArguments(
                sample=Path("/full/path/to/phenopacket.json"),
                vcf_file=Path("/full/path/to/vcf_dir/test_1.vcf"),
                vcf_assembly="GRCh37",
                output_options_file=Path("/full/path/to/output/option/file.json"),
            ),
        )

    def test_add_command_line_arguments_output_options_dir(self):
        self.assertEqual(
            self.output_options_dir.add_command_line_arguments(Path("/full/path/to/vcf_dir")),
            ExomiserCommandLineArguments(
                sample=Path("/full/path/to/phenopacket.json"),
                vcf_file=Path("/full/path/to/vcf_dir/test_1.vcf"),
                vcf_assembly="GRCh37",
                output_options_file=Path(
                    "/full/path/to/some/alternate/output_options/phenopacket-output-options.json"
                ),
            ),
        )
