from pathlib import Path

from pheval_exomiser.prepare.tool_specific_configuration_options import ExomiserConfigurations


class ExomiserConfigurationFileWriter:
    def __init__(self, input_dir: Path, configurations: ExomiserConfigurations):
        self.input_dir = input_dir
        self.configurations = configurations
        self.application_properties = open(input_dir.joinpath("application.properties"), "w")

    def write_remm_version(self):
        if self.configurations.remm_version is not None:
            self.application_properties.write(f"remm.version={self.configurations.remm_version}\n")

    def write_cadd_version(self):
        if self.configurations.cadd_version is not None:
            self.application_properties.write(f"cadd.version={self.configurations.cadd_version}\n")

    def write_exomiser_data_directory(self):
        if self.configurations.environment.lower() == "docker":
            self.application_properties.write(f"exomiser.data-directory={EXOMISER_DATA_DIRECTORY_TARGET_DOCKER}\n")
        if self.configurations.environment.lower() == "local":
            self.application_properties.write(f"exomiser.data-directory={self.input_dir}\n")

    def write_exomiser_hg19_data_version(self):
        if self.configurations.hg19_data_version is not None:
            self.application_properties.write(f"exomiser.hg19.data-version={self.configurations.hg19_data_version}\n")

    def write_exomiser_hg19_cadd_snv_path(self):
        if self.configurations.hg19_cadd_snv_path is not None:
            self.application_properties.write(
                "exomiser.hg19.cadd-snv-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg19/whole_genome_SNVs.tsv.gz\n")

    def write_exomiser_hg19_cadd_indel_path(self):
        if self.configurations.hg19_cadd_indel_path is not None:
            self.application_properties.write("exomiser.hg19.cadd-in-del-path="
                                              "${exomiser.data-directory}/cadd/${cadd.version}/hg19/InDels.tsv.gz\n")

    def write_exomiser_hg19_remm_path(self):
        if self.configurations.hg19_remm_path is not None:
            self.application_properties.write(
                "exomiser.hg19.remm-path="
                "${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg19.tsv.gz\n")

    def write_exomiser_hg19_local_frequency_path(self):
        if self.configurations.hg19_local_frequency_path is not None:
            self.application_properties.write(
                "exomiser.hg19.local-frequency-path="
                "${exomiser.data-directory}/local/local_frequency_test_hg19.tsv.gz\n")

    def write_exomiser_hg38_data_version(self):
        if self.configurations.hg38_data_version is not None:
            self.application_properties.write(f"exomiser.hg38.data-version={self.configurations.hg38_data_version}\n")

    def write_exomiser_hg38_cadd_snv_path(self):
        if self.configurations.hg38_cadd_snv_path is not None:
            self.application_properties.write(
                "exomiser.hg38.cadd-snv-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg38/whole_genome_SNVs.tsv.gz\n")

    def write_exomiser_hg38_cadd_indel_path(self):
        if self.configurations.hg38_cadd_indel_path is not None:
            self.application_properties.write("exomiser.hg38.cadd-in-del-path="
                                              "${exomiser.data-directory}/cadd/${cadd.version}/hg38/InDels.tsv.gz\n")

    def write_exomiser_hg38_remm_path(self):
        if self.configurations.hg38_remm_path is not None:
            self.application_properties.write(
                "exomiser.hg38.remm-path="
                "${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg38.tsv.gz\n")

    def write_exomiser_hg38_local_frequency_path(self):
        if self.configurations.hg19_local_frequency_path is not None:
            self.application_properties.write(
                "exomiser.hg38.local-frequency-path="
                "${exomiser.data-directory}/local/local_frequency_test_hg38.tsv.gz\n")

    def write_exomiser_phenotype_data_version(self):
        self.application_properties.write(
            f"exomiser.phenotype.data-version={self.configurations.phenotype_data_version}\n")

    def write_hg19_white_list_path(self):
        self.application_properties.write(
            "exomiser.hg19.variant-white-list-path=${exomiser.hg19.data-version}_hg19_clinvar_whitelist.tsv.gz\n")

    def write_hg38_white_list_path(self):
        if self.configurations.hg38_data_version is not None:
            self.application_properties.write(
                "exomiser.hg38.variant-white-list-path=${exomiser.hg38.data-version}_hg38_clinvar_whitelist.tsv.gz\n")

    def write_application_properties(self):
        self.write_remm_version()
        self.write_cadd_version()
        self.write_exomiser_data_directory()
        self.write_exomiser_phenotype_data_version()
        self.write_exomiser_hg19_data_version()
        self.write_exomiser_hg19_cadd_snv_path()
        self.write_exomiser_hg19_cadd_indel_path()
        self.write_exomiser_hg19_remm_path()
        self.write_exomiser_hg19_local_frequency_path()
        self.write_hg19_white_list_path()
        self.write_exomiser_hg38_data_version()
        self.write_exomiser_hg38_cadd_snv_path()
        self.write_exomiser_hg38_cadd_indel_path()
        self.write_exomiser_hg38_remm_path()
        self.write_exomiser_hg38_local_frequency_path()
        self.write_hg38_white_list_path()
        self.application_properties.close()
