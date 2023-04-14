import unittest
from copy import copy
from pathlib import Path

from pheval_exomiser.config_parser import (
    ExomiserConfig,
    ExomiserConfigPostProcess,
    ExomiserConfigRun,
    ExomiserConfigRunExomiserConfigs,
    ExomiserConfigRunExomiserManualConfigs,
)
from pheval_exomiser.run.run import (
    EditExomiserApplicationProperties,
    ExomiserConfigParameters,
    add_exomiser_config_file_for_docker,
    create_docker_run_command,
)

exomiser_application_properties = [
    "#\n",
    "# The Exomiser - A tool to annotate and prioritize genomic variants\n",
    "#\n",
    "# Copyright (c) 2016-2021 Queen Mary University of London.\n",
    "# Copyright (c) 2012-2016 Charité Universitätsmedizin Berlin and Genome Research Ltd.\n",
    "#\n",
    "# This program is free software: you can redistribute it and/or modify\n",
    "# it under the terms of the GNU Affero General Public License as\n",
    "# published by the Free Software Foundation, either version 3 of the\n",
    "# License, or (at your option) any later version.\n",
    "#\n",
    "# This program is distributed in the hope that it will be useful,\n",
    "# but WITHOUT ANY WARRANTY; without even the implied warranty of\n",
    "# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n",
    "# GNU Affero General Public License for more details.\n",
    "#\n",
    "# You should have received a copy of the GNU Affero General Public License\n",
    "# along with this program.  If not, see <http://www.gnu.org/licenses/>.\n",
    "#\n",
    "\n",
    "## exomiser root data directory ##\n",
    "exomiser.data-directory=/fake/path/to/data\n",
    "\n",
    "## optional data sources ##\n",
    "# The location of these files need to be specified for each assembly in the sections below\n",
    "# REMM can be downloaded from https://zenodo.org/record/4768448\n",
    "# REMM is required for the genome preset.\n",
    "remm.version=0.3.1.post1\n",
    "# CADD can be downloaded from http://cadd.gs.washington.edu/download\n",
    "# CADD is an optional datasource\n",
    "cadd.version=1.4\n",
    "\n",
    "### hg19 assembly ###\n",
    "exomiser.hg19.data-version=2209\n",
    "# transcript source will default to ensembl. Can define as ucsc/ensembl/refseq\n",
    "#exomiser.hg19.transcript-source=ensembl\n",
    "# location of CADD/REMM Tabix files - you will need these for analysis of non-coding variants.\n",
    "# You will require the tsv.gz and tsv.gz.tbi (tabix) file pairs.\n",
    "# Un-comment and add the full path to the relevant tsv.gz files if you want to enable these.\n",
    "#exomiser.hg19.cadd-snv-path=${exomiser.data-directory}/cadd/${cadd.version}/hg19/whole_genome_SNVs.tsv.gz\n",
    "#exomiser.hg19.cadd-in-del-path=${exomiser.data-directory}/cadd/${cadd.version}/hg19/InDels.tsv.gz\n",
    "#exomiser.hg19.remm-path=${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg19.tsv.gz\n",
    "#exomiser.hg19.local-frequency-path=${exomiser.data-directory}/local/local_frequency_test_hg19.tsv.gz\n",
    "exomiser.hg19.variant-white-list-path=${exomiser.hg19.data-version}_hg19_clinvar_whitelist.tsv.gz\n",
    "\n",
    "### hg38 assembly ###\n",
    "#exomiser.hg38.data-version=2109\n",
    "#exomiser.hg38.cadd-snv-path=${exomiser.data-directory}/cadd/${cadd.version}/whole_genome_SNVs.tsv.gz\n",
    "#exomiser.hg38.cadd-in-del-path=${exomiser.data-directory}/cadd/${cadd.version}/InDels.tsv.gz\n",
    "#exomiser.hg38.remm-path=${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg38.tsv.gz\n",
    "#exomiser.hg38.local-frequency-path=${exomiser.data-directory}/local/local_frequency_test_hg38.tsv.gz\n",
    "#exomiser.hg38.variant-white-list-path=${exomiser.hg38.data-version}_hg38_clinvar_whitelist.tsv.gz\n",
    "\n",
    "### phenotypes ###\n",
    "exomiser.phenotype.data-version=2209\n",
    "#exomiser.phenotype.data-directory=${exomiser.data-directory}/${exomiser.phenotype.data-version}_phenotype\n",
    "# String random walk data file\n",
    "#exomiser.phenotype.random-walk-file-name=rw_string_10.mv\n",
    "#exomiser.phenotype.random-walk-index-file-name=rw_string_9_05_id2index.gz\n",
    "\n",
    "### caching ###\n",
    "# to your requirements\n",
    "#none/simple/caffeine\n",
    "#spring.cache.type=none\n",
    "#spring.cache.caffeine.spec=maximumSize=60000\n",
    "\n",
    "### logging ###\n",
    "#logging.file.name=logs/exomiser.log\n",
]

basic_pheval_config = ExomiserConfig(
    run=ExomiserConfigRun(
        environment="local",
        phenotype_only=False,
        path_to_exomiser_software_directory=Path(
            "/Users/yaseminbridges/exomiser/exomiser-cli-13.1.0"
        ),
        path_to_analysis_yaml=Path("/Users/yaseminbridges/preset-exome-analysis.yml"),
        exomiser_configurations=ExomiserConfigRunExomiserConfigs(
            exomiser_version="13.1.0",
            path_to_application_properties_config=Path(
                "/Users/yaseminbridges/exomiser/exomiser-cli-13.1.0/application.properties"
            ),
            application_properties_arguments=ExomiserConfigRunExomiserManualConfigs(
                exomiser_phenotype_version=None,
                exomiser_hg19_version=None,
                exomiser_hg38_version=None,
            ),
        ),
        max_jobs=0,
    ),
    post_process=ExomiserConfigPostProcess(score_name="combinedScore", sort_order="descending"),
)


class TestEditExomiserApplicationProperties(unittest.TestCase):
    def setUp(self) -> None:
        self.contents_to_edit_path = EditExomiserApplicationProperties(
            basic_pheval_config,
            Path("/path/to/exomiser/input/data"),
            exomiser_application_properties,
        )

    def test_edit_data_path_for_local_run(self):
        self.assertEqual(
            [
                line
                for line in self.contents_to_edit_path.edit_data_path_for_local_run()
                if line.startswith("exomiser.data-directory=")
            ],
            ["exomiser.data-directory=/path/to/exomiser/input/data\n"],
        )
        self.assertNotEqual(
            [
                line
                for line in self.contents_to_edit_path.edit_data_path_for_local_run()
                if line.startswith("exomiser.data-directory=")
            ],
            ["exomiser.data-directory=/fake/path/to/data\n"],
        )

    def test_edit_data_path_for_docker_run(self):
        self.assertEqual(
            [
                line
                for line in self.contents_to_edit_path.edit_data_path_for_docker_run()
                if line.startswith("exomiser.data-directory=")
            ],
            ["exomiser.data-directory=/exomiser-data\n"],
        )
        self.assertNotEqual(
            [
                line
                for line in self.contents_to_edit_path.edit_data_path_for_docker_run()
                if line.startswith("exomiser.data-directory=")
            ],
            ["exomiser.data-directory=/fake/path/to/data\n"],
        )

    def test_edit_data_path(self):
        self.assertEqual(
            [
                line
                for line in self.contents_to_edit_path.edit_data_path()
                if line.startswith("exomiser.data-directory=")
            ],
            ["exomiser.data-directory=/path/to/exomiser/input/data\n"],
        )
        copied_contents = copy(self.contents_to_edit_path)
        copied_contents.config.run.environment = "docker"
        self.assertEqual(
            [
                line
                for line in copied_contents.edit_data_path()
                if line.startswith("exomiser.data-directory=")
            ],
            ["exomiser.data-directory=/exomiser-data\n"],
        )


class TestAddExomiserConfigFileForDocker(unittest.TestCase):
    def test_add_exomiser_config_file_for_docker(self):
        self.assertEqual(
            add_exomiser_config_file_for_docker(basic_pheval_config),
            ExomiserConfigParameters(
                application_properties_path=Path(
                    "/Users/yaseminbridges/exomiser/exomiser-cli-13.1.0"
                ),
                exomiser_phenotype_version=None,
                exomiser_hg19_version=None,
                exomiser_hg38_version=None,
            ),
        )


class TestCreateDockerRunCommand(unittest.TestCase):
    def test_create_docker_run_command(self):
        self.assertEqual(
            [
                "--batch",
                "/exomiser-batch-file/file",
                "--spring.config.location=/exomiser-config/application.properties",
            ],
            create_docker_run_command(basic_pheval_config, Path("/path/to/batch/file")),
        )
