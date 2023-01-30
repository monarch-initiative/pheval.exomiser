import unittest

import pandas as pd
from oaklib import OntologyResource
from oaklib.implementations import ProntoImplementation
from phenopackets import (  # Pedigree,; Phenopacket,
    Diagnosis,
    File,
    GeneDescriptor,
    GenomicInterpretation,
    Individual,
    Interpretation,
    OntologyClass,
    Pedigree,
    PhenotypicFeature,
    Resource,
    VariantInterpretation,
    VariationDescriptor,
    VcfRecord,
)

from pheval_exomiser.prepare.yaml_to_family_phenopacket import (
    ExomiserYamlToPhenopacketConverter,
    construct_pedigree,
    create_hgnc_dict,
)

yaml_job_file = {
    "analysis": {
        "genomeAssembly": "hg19",
        "vcf": "/full/path/to/vcf",
        "ped": "",
        "proband": "subject-1",
        "hpoIds": ["HP:0001156", "HP:0001363", "HP:0011304", "HP:0010055"],
        "analysisMode": "PASS_ONLY",
        "inheritanceModes": {
            "AUTOSOMAL_DOMINANT": 0.1,
            "AUTOSOMAL_RECESSIVE_COMP_HET": 2.0,
            "AUTOSOMAL_RECESSIVE_HOM_ALT": 0.1,
            "X_RECESSIVE_COMP_HET": 2.0,
            "X_RECESSIVE_HOM_ALT": 0.1,
            "X_DOMINANT": 0.1,
            "MITOCHONDRIAL": 0.2,
        },
        "frequencySources": [
            "THOUSAND_GENOMES",
            "TOPMED",
            "UK10K",
            "ESP_AFRICAN_AMERICAN",
            "ESP_EUROPEAN_AMERICAN",
            "ESP_ALL",
            "EXAC_AFRICAN_INC_AFRICAN_AMERICAN",
            "EXAC_AMERICAN",
            "EXAC_SOUTH_ASIAN",
            "EXAC_EAST_ASIAN",
            "EXAC_FINNISH",
            "EXAC_NON_FINNISH_EUROPEAN",
            "EXAC_OTHER",
            "GNOMAD_E_AFR",
            "GNOMAD_E_AMR",
            "GNOMAD_E_EAS",
            "GNOMAD_E_FIN",
            "GNOMAD_E_NFE",
            "GNOMAD_E_OTH",
            "GNOMAD_E_SAS",
            "GNOMAD_G_AFR",
            "GNOMAD_G_AMR",
            "GNOMAD_G_EAS",
            "GNOMAD_G_FIN",
            "GNOMAD_G_NFE",
            "GNOMAD_G_OTH",
            "GNOMAD_G_SAS",
        ],
        "pathogenicitySources": ["POLYPHEN", "MUTATION_TASTER", "SIFT"],
        "steps": [
            {
                "variantEffectFilter": {
                    "remove": [
                        "FIVE_PRIME_UTR_EXON_VARIANT",
                        "FIVE_PRIME_UTR_INTRON_VARIANT",
                        "THREE_PRIME_UTR_EXON_VARIANT",
                        "THREE_PRIME_UTR_INTRON_VARIANT",
                        "NON_CODING_TRANSCRIPT_EXON_VARIANT",
                        "UPSTREAM_GENE_VARIANT",
                        "INTERGENIC_VARIANT",
                        "REGULATORY_REGION_VARIANT",
                        "CODING_TRANSCRIPT_INTRON_VARIANT",
                        "NON_CODING_TRANSCRIPT_INTRON_VARIANT",
                        "DOWNSTREAM_GENE_VARIANT",
                    ]
                }
            },
            {"frequencyFilter": {"maxFrequency": 2.0}},
            {"pathogenicityFilter": {"keepNonPathogenic": True}},
            {"inheritanceFilter": {}},
            {"omimPrioritiser": {}},
            {"hiPhivePrioritiser": {}},
        ],
    },
    "outputOptions": {
        "outputContributingVariantsOnly": False,
        "numGenes": 0,
        "outputPrefix": "results/Pfeiffer-hiphive-exome",
        "outputFormats": ["HTML", "JSON", "TSV_GENE", "TSV_VARIANT", "VCF"],
    },
}

diagnoses_data = [
    ["subject-1", "Male", "12", "12456342", "A/C", "FGFR2", "homozygous", "Yes"],
    ["subject-1", "Male", "14", "17856324", "T/G", "LARGE1", "heterozygous", "Yes"],
    ["subject-2", "Female", "1", "23446566", "T/A", "NFY", "heterozygous", "No"],
]

diagnoses = pd.DataFrame(
    diagnoses_data,
    columns=["ProbandId", "Sex", "Chr", "Start", "Ref/Alt", "Gene", "Genotype", "Diagnosis"],
)

diagnosis_row = pd.DataFrame(
    [["subject-1", "Male", "12", "12456342", "A/C", "FGFR2", "homozygous", "Yes"]],
    columns=["ProbandId", "Sex", "Chr", "Start", "Ref/Alt", "Gene", "Genotype", "Diagnosis"],
)


class TestConvertExomiserYamlToPhenopacket(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        resource = OntologyResource(slug="hp.obo", local=False)
        oi = ProntoImplementation(resource)
        genotype_resource = OntologyResource(slug="geno.owl", local=False)
        go_oi = ProntoImplementation(genotype_resource)
        hgnc_data = create_hgnc_dict()
        cls.subject_1 = ExomiserYamlToPhenopacketConverter(go_oi, oi, hgnc_data)

    def test_construct_individual_message(self):
        self.assertEqual(
            self.subject_1.construct_individual(yaml_job_file, diagnoses),
            Individual(id="subject-1", sex="MALE"),
        )

    def test_get_diagnoses_for_proband(self):
        self.assertTrue(
            pd.DataFrame(
                [
                    ["subject-1", "Male", "12", "12456342", "A/C", "FGFR2", "homozygous", "Yes"],
                    ["subject-1", "Male", "14", "17856324", "T/G", "LARGE1", "heterozygous", "Yes"],
                ],
                columns=[
                    "ProbandId",
                    "Sex",
                    "Chr",
                    "Start",
                    "Ref/Alt",
                    "Gene",
                    "Genotype",
                    "Diagnosis",
                ],
            ).equals(self.subject_1.get_diagnoses_for_proband(yaml_job_file, diagnoses))
        )

    def test_construct_phenotypic_interpretations(self):
        self.assertEqual(
            self.subject_1.construct_phenotypic_interpretations(yaml_job_file),
            [
                PhenotypicFeature(type=OntologyClass(id="HP:0001156", label="Brachydactyly")),
                PhenotypicFeature(type=OntologyClass(id="HP:0001363", label="Craniosynostosis")),
                PhenotypicFeature(type=OntologyClass(id="HP:0011304", label="Broad thumb")),
                PhenotypicFeature(type=OntologyClass(id="HP:0010055", label="Broad hallux")),
            ],
        )

    def test_construct_vcf_record(self):
        self.assertEqual(
            self.subject_1.construct_vcf_record(yaml_job_file, diagnoses.loc[0]),
            VcfRecord(
                genome_assembly="hg19",
                chrom="12",
                pos=12456342,
                ref="A",
                alt="C",
            ),
        )

    def test_construct_allelic_state(self):
        self.assertEqual(
            self.subject_1.construct_allelic_state(diagnoses.loc[0]),
            OntologyClass(
                id="GENO:0000136",
                label="homozygous",
            ),
        )

    def test_construct_gene_descriptor(self):
        self.assertEqual(
            self.subject_1.construct_gene_descriptor(diagnoses.loc[0]),
            GeneDescriptor(
                value_id="ENSG00000066468",
                symbol="FGFR2",
            ),
        )

    def test_construct_variation_descriptor(self):
        self.assertEqual(
            self.subject_1.construct_variation_descriptor(
                yaml_job=yaml_job_file, diagnosis=diagnoses.loc[0]
            ),
            VariationDescriptor(
                id="subject-1:12:12456342:A/C",
                gene_context=GeneDescriptor(
                    value_id="ENSG00000066468",
                    symbol="FGFR2",
                ),
                vcf_record=VcfRecord(
                    genome_assembly="hg19",
                    chrom="12",
                    pos=12456342,
                    ref="A",
                    alt="C",
                ),
                allelic_state=OntologyClass(
                    id="GENO:0000136",
                    label="homozygous",
                ),
            ),
        )

    def test_construct_variant_interpretation(self):
        self.assertEqual(
            self.subject_1.construct_variant_interpretation(
                yaml_job=yaml_job_file, diagnosis=diagnoses.loc[0]
            ),
            VariantInterpretation(
                variation_descriptor=VariationDescriptor(
                    id="subject-1:12:12456342:A/C",
                    gene_context=GeneDescriptor(
                        value_id="ENSG00000066468",
                        symbol="FGFR2",
                    ),
                    vcf_record=VcfRecord(
                        genome_assembly="hg19",
                        chrom="12",
                        pos=12456342,
                        ref="A",
                        alt="C",
                    ),
                    allelic_state=OntologyClass(
                        id="GENO:0000136",
                        label="homozygous",
                    ),
                ),
            ),
        )

    def test_construct_genomic_interpretation(self):
        self.assertEqual(
            self.subject_1.construct_genomic_interpretations(yaml_job_file, diagnoses),
            [
                GenomicInterpretation(
                    subject_or_biosample_id="subject-1",
                    variant_interpretation=VariantInterpretation(
                        variation_descriptor=VariationDescriptor(
                            id="subject-1:12:12456342:A/C",
                            gene_context=GeneDescriptor(
                                value_id="ENSG00000066468",
                                symbol="FGFR2",
                            ),
                            vcf_record=VcfRecord(
                                genome_assembly="hg19",
                                chrom="12",
                                pos=12456342,
                                ref="A",
                                alt="C",
                            ),
                            allelic_state=OntologyClass(
                                id="GENO:0000136",
                                label="homozygous",
                            ),
                        ),
                    ),
                ),
                GenomicInterpretation(
                    subject_or_biosample_id="subject-1",
                    variant_interpretation=VariantInterpretation(
                        variation_descriptor=VariationDescriptor(
                            id="subject-1:14:17856324:T/G",
                            gene_context=GeneDescriptor(
                                value_id="ENSG00000133424",
                                symbol="LARGE1",
                            ),
                            vcf_record=VcfRecord(
                                genome_assembly="hg19",
                                chrom="14",
                                pos=17856324,
                                ref="T",
                                alt="G",
                            ),
                            allelic_state=OntologyClass(
                                id="GENO:0000135",
                                label="heterozygous",
                            ),
                        ),
                    ),
                ),
            ],
        )

    def test_construct_diagnosis(self):
        self.assertEqual(
            self.subject_1.construct_diagnosis(yaml_job_file, diagnoses),
            Diagnosis(
                genomic_interpretations=[
                    GenomicInterpretation(
                        subject_or_biosample_id="subject-1",
                        variant_interpretation=VariantInterpretation(
                            variation_descriptor=VariationDescriptor(
                                id="subject-1:12:12456342:A/C",
                                gene_context=GeneDescriptor(
                                    value_id="ENSG00000066468",
                                    symbol="FGFR2",
                                ),
                                vcf_record=VcfRecord(
                                    genome_assembly="hg19",
                                    chrom="12",
                                    pos=12456342,
                                    ref="A",
                                    alt="C",
                                ),
                                allelic_state=OntologyClass(
                                    id="GENO:0000136",
                                    label="homozygous",
                                ),
                            ),
                        ),
                    ),
                    GenomicInterpretation(
                        subject_or_biosample_id="subject-1",
                        variant_interpretation=VariantInterpretation(
                            variation_descriptor=VariationDescriptor(
                                id="subject-1:14:17856324:T/G",
                                gene_context=GeneDescriptor(
                                    value_id="ENSG00000133424",
                                    symbol="LARGE1",
                                ),
                                vcf_record=VcfRecord(
                                    genome_assembly="hg19",
                                    chrom="14",
                                    pos=17856324,
                                    ref="T",
                                    alt="G",
                                ),
                                allelic_state=OntologyClass(
                                    id="GENO:0000135",
                                    label="heterozygous",
                                ),
                            ),
                        ),
                    ),
                ]
            ),
        )

    def test_construct_interpretations(self):
        self.assertEqual(
            self.subject_1.construct_interpretations(yaml_job_file, diagnoses),
            [
                Interpretation(
                    id="subject-1" + "-interpretation",
                    diagnosis=Diagnosis(
                        genomic_interpretations=[
                            GenomicInterpretation(
                                subject_or_biosample_id="subject-1",
                                variant_interpretation=VariantInterpretation(
                                    variation_descriptor=VariationDescriptor(
                                        id="subject-1:12:12456342:A/C",
                                        gene_context=GeneDescriptor(
                                            value_id="ENSG00000066468",
                                            symbol="FGFR2",
                                        ),
                                        vcf_record=VcfRecord(
                                            genome_assembly="hg19",
                                            chrom="12",
                                            pos=12456342,
                                            ref="A",
                                            alt="C",
                                        ),
                                        allelic_state=OntologyClass(
                                            id="GENO:0000136",
                                            label="homozygous",
                                        ),
                                    ),
                                ),
                            ),
                            GenomicInterpretation(
                                subject_or_biosample_id="subject-1",
                                variant_interpretation=VariantInterpretation(
                                    variation_descriptor=VariationDescriptor(
                                        id="subject-1:14:17856324:T/G",
                                        gene_context=GeneDescriptor(
                                            value_id="ENSG00000133424",
                                            symbol="LARGE1",
                                        ),
                                        vcf_record=VcfRecord(
                                            genome_assembly="hg19",
                                            chrom="14",
                                            pos=17856324,
                                            ref="T",
                                            alt="G",
                                        ),
                                        allelic_state=OntologyClass(
                                            id="GENO:0000135",
                                            label="heterozygous",
                                        ),
                                    ),
                                ),
                            ),
                        ]
                    ),
                )
            ],
        )

    def test_construct_meta_data(self):
        self.assertEqual(self.subject_1.construct_meta_data().created_by, "pheval-converter")
        self.assertEqual(
            list(self.subject_1.construct_meta_data().resources),
            [
                Resource(
                    id="hp",
                    name="human phenotype ontology",
                    url="http://purl.obolibrary.org/obo/hp.owl",
                    version="hp/releases/2019-11-08",
                    namespace_prefix="HP",
                    iri_prefix="http://purl.obolibrary.org/obo/HP_",
                )
            ],
        )
        self.assertEqual(self.subject_1.construct_meta_data().phenopacket_schema_version, "2.0")

    def test_construct_files(self):
        self.assertEqual(
            self.subject_1.construct_files(yaml_job_file),
            [
                File(
                    uri="/full/path/to/vcf",
                    file_attributes={
                        "fileFormat": "VCF",
                        "genomeAssembly": "hg19",
                    },
                )
            ],
        )


class TestConstructPedigree(unittest.TestCase):
    def setUp(self) -> None:
        self.pedigree = [
            "FAM1\tISDBM322016\t0\t0\t1\t1\n",
            "FAM1\tISDBM322018\t0\t0\t2\t1\n",
            "FAM1\tISDBM322015\tISDBM322016\tISDBM322018\t1\t1\n",
            "FAM1\tISDBM322017\tISDBM322016\tISDBM322018\t2\t2\n",
        ]

    def test_construct_pedigree(self):
        self.assertEqual(
            construct_pedigree(self.pedigree),
            (
                "FAM1",
                Pedigree(
                    persons=[
                        Pedigree.Person(
                            family_id="FAM1", individual_id="ISDBM322016", sex=2, affected_status=1
                        ),
                        Pedigree.Person(
                            family_id="FAM1", individual_id="ISDBM322018", sex=1, affected_status=1
                        ),
                        Pedigree.Person(
                            family_id="FAM1",
                            individual_id="ISDBM322015",
                            paternal_id="ISDBM322016",
                            maternal_id="ISDBM322018",
                            sex=2,
                            affected_status=1,
                        ),
                        Pedigree.Person(
                            family_id="FAM1",
                            individual_id="ISDBM322017",
                            paternal_id="ISDBM322016",
                            maternal_id="ISDBM322018",
                            sex=1,
                            affected_status=2,
                        ),
                    ]
                ),
            ),
        )
