import shutil
import tempfile
import unittest
from pathlib import Path

from pheval_exomiser.prepare.tool_specific_configuration_options import (
    ApplicationProperties,
    ExomiserConfigurations,
)
from pheval_exomiser.prepare.write_application_properties import ExomiserConfigurationFileWriter


class TestExomiserConfigurationFileWriter(unittest.TestCase):
    input_dir = None

    @classmethod
    def setUp(cls) -> None:
        cls.input_dir = tempfile.mkdtemp()
        cls.application_properties_settings = ExomiserConfigurationFileWriter(
            input_dir=Path(cls.input_dir),
            configurations=ExomiserConfigurations(
                environment="local",
                analysis_configuration_file=Path("preset_exome_analysis.py"),
                application_properties=ApplicationProperties(
                    remm_version="0.3.1.post1",
                    cadd_version="1.4",
                    hg19_local_frequency_path="local_frequency_test_hg19.tsv.gz",
                    hg38_local_frequency_path="local_frequency_test_hg38.tsv.gz",
                    phenotype_data_version="2302",
                    hg19_data_version="2302",
                    hg38_data_version="2302",
                    cache_caffeine_spec=60000,
                ),
            ),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.input_dir)

    def test_write_remm_version(self):
        self.application_properties_settings.write_remm_version()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, ["remm.version=0.3.1.post1\n"])

    def test_write_remm_version_none_specified(self):
        self.application_properties_settings.configurations.application_properties.remm_version = (
            None
        )
        self.application_properties_settings.write_remm_version()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_cadd_version(self):
        self.application_properties_settings.write_cadd_version()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, ["cadd.version=1.4\n"])

    def test_write_cadd_version_none_specified(self):
        self.application_properties_settings.configurations.application_properties.cadd_version = (
            None
        )
        self.application_properties_settings.write_cadd_version()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_exomiser_data_directory(self):
        self.application_properties_settings.write_exomiser_data_directory()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [f"exomiser.data-directory={self.input_dir}\n"])

    def test_write_exomiser_hg19_data_version(self):
        self.application_properties_settings.write_exomiser_hg19_data_version()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, ["exomiser.hg19.data-version=2302\n"])

    def test_write_exomiser_hg19_cadd_snv_path(self):
        self.application_properties_settings.write_exomiser_hg19_cadd_snv_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg19.cadd-snv-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg19/whole_genome_SNVs.tsv.gz\n"
            ],
        )

    def test_write_exomiser_hg19_cadd_snv_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.cadd_version = (
            None
        )
        self.application_properties_settings.write_exomiser_hg19_cadd_snv_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_exomiser_hg19_cadd_indel_path(self):
        self.application_properties_settings.write_exomiser_hg19_cadd_indel_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg19.cadd-in-del-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg19/InDels.tsv.gz\n"
            ],
        )

    def test_write_exomiser_hg19_cadd_indel_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.cadd_version = (
            None
        )
        self.application_properties_settings.write_exomiser_hg19_cadd_indel_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_exomiser_hg19_remm_path(self):
        self.application_properties_settings.write_exomiser_hg19_remm_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg19.remm-path="
                "${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg19.tsv.gz\n"
            ],
        )

    def test_write_exomiser_hg19_remm_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.remm_version = (
            None
        )
        self.application_properties_settings.write_exomiser_hg19_remm_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_exomiser_hg19_local_frequency_path(self):
        self.application_properties_settings.write_exomiser_hg19_local_frequency_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg19.local-frequency-path="
                "${exomiser.data-directory}/local/local_frequency_test_hg19.tsv.gz\n"
            ],
        )

    def test_write_exomiser_hg19_local_frequency_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.hg19_local_frequency_path = (
            None
        )
        self.application_properties_settings.write_exomiser_hg19_local_frequency_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_exomiser_hg38_data_version(self):
        self.application_properties_settings.write_exomiser_hg38_data_version()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, ["exomiser.hg38.data-version=2302\n"])

    def test_write_exomiser_hg38_cadd_snv_path(self):
        self.application_properties_settings.write_exomiser_hg38_cadd_snv_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg38.cadd-snv-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg38/whole_genome_SNVs.tsv.gz\n"
            ],
        )

    def test_write_exomiser_hg38_cadd_snv_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.cadd_version = (
            None
        )
        self.application_properties_settings.write_exomiser_hg38_cadd_snv_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_exomiser_hg38_cadd_indel_path(self):
        self.application_properties_settings.write_exomiser_hg38_cadd_indel_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg38.cadd-in-del-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg38/InDels.tsv.gz\n"
            ],
        )

    def test_write_exomiser_hg38_cadd_indel_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.cadd_version = (
            None
        )
        self.application_properties_settings.write_exomiser_hg38_cadd_indel_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_exomiser_hg38_remm_path(self):
        self.application_properties_settings.write_exomiser_hg38_remm_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg38.remm-path="
                "${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg38.tsv.gz\n"
            ],
        )

    def test_write_exomiser_hg38_remm_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.remm_version = (
            None
        )
        self.application_properties_settings.write_exomiser_hg38_remm_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_exomiser_hg38_local_frequency_path(self):
        self.application_properties_settings.write_exomiser_hg38_local_frequency_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg38.local-frequency-path="
                "${exomiser.data-directory}/local/local_frequency_test_hg38.tsv.gz\n"
            ],
        )

    def test_write_exomiser_hg38_local_frequency_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.hg38_local_frequency_path = (
            None
        )
        self.application_properties_settings.write_exomiser_hg38_local_frequency_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_exomiser_phenotype_data_version(self):
        self.application_properties_settings.write_exomiser_phenotype_data_version()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, ["exomiser.phenotype.data-version=2302\n"])

    def test_write_hg19_white_list_path(self):
        self.application_properties_settings.write_hg19_white_list_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg19.variant-white-list-path="
                "${exomiser.hg19.data-version}_hg19_clinvar_whitelist.tsv.gz\n"
            ],
        )

    def test_write_hg19_white_list_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.hg19_data_version = (
            None
        )
        self.application_properties_settings.write_hg19_white_list_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_hg38_white_list_path(self):
        self.application_properties_settings.write_hg38_white_list_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "exomiser.hg38.variant-white-list-path="
                "${exomiser.hg38.data-version}_hg38_clinvar_whitelist.tsv.gz\n"
            ],
        )

    def test_write_hg38_white_list_path_none_specified(self):
        self.application_properties_settings.configurations.application_properties.hg38_data_version = (
            None
        )
        self.application_properties_settings.write_hg38_white_list_path()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_cache_spec(self):
        self.application_properties_settings.write_cache_spec()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, ["spring.cache.caffeine.spec=maximumSize=60000\n"])

    def test_write_cache_spec_none_specified(self):
        self.application_properties_settings.configurations.application_properties.cache_caffeine_spec = (
            None
        )
        self.application_properties_settings.write_cache_spec()
        self.application_properties_settings.application_properties.close()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(contents, [])

    def test_write_application_properties(self):
        self.application_properties_settings.write_application_properties()
        with open(Path(self.input_dir).joinpath("application.properties"), "r") as config:
            contents = config.readlines()
        config.close()
        self.assertEqual(
            contents,
            [
                "spring.cache.caffeine.spec=maximumSize=60000\n",
                "cadd.version=1.4\n",
                f"exomiser.data-directory={self.input_dir}\n",
                "exomiser.hg19.cadd-in-del-path=${exomiser.data-directory}/cadd/${cadd.version}/hg19/InDels.tsv.gz\n",
                "exomiser.hg19.cadd-snv-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg19/whole_genome_SNVs.tsv.gz\n",
                "exomiser.hg19.data-version=2302\n",
                "exomiser.hg19.local-frequency-path="
                "${exomiser.data-directory}/local/local_frequency_test_hg19.tsv.gz\n",
                "exomiser.hg19.remm-path=${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg19.tsv.gz\n",
                "exomiser.hg38.cadd-in-del-path=${exomiser.data-directory}/cadd/${cadd.version}/hg38/InDels.tsv.gz\n",
                "exomiser.hg38.cadd-snv-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg38/whole_genome_SNVs.tsv.gz\n",
                "exomiser.hg38.data-version=2302\n",
                "exomiser.hg38.local-frequency-path="
                "${exomiser.data-directory}/local/local_frequency_test_hg38.tsv.gz\n",
                "exomiser.hg38.remm-path=${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg38.tsv.gz\n",
                "exomiser.phenotype.data-version=2302\n",
                "exomiser.hg19.variant-white-list-path=${exomiser.hg19.data-version}_hg19_clinvar_whitelist.tsv.gz\n",
                "exomiser.hg38.variant-white-list-path=${exomiser.hg38.data-version}_hg38_clinvar_whitelist.tsv.gz\n",
                "remm.version=0.3.1.post1\n",
            ],
        )
