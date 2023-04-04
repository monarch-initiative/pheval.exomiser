from pathlib import Path

from pheval_exomiser.prepare.tool_specific_configuration_options import ExomiserConfigurations


class ExomiserConfigurationFileWriter:
    def __init__(self, input_dir: Path, configurations: ExomiserConfigurations):
        self.input_dir = input_dir
        self.configurations = configurations
        self.application_properties = open(input_dir.joinpath("application.properties"), "w")

    def write_exomiser_data_directory(self):
        self.application_properties.write(f"exomiser.data-directory={self.input_dir}\n")

    def write_exomiser_hg19_data_version(self):
        if self.configurations.hg19_data_version is not None:
            self.application_properties.write(f"exomiser.hg19.data-version={self.configurations.hg19_data_version}\n")

    def write_exomiser_hg38_data_version(self):
        if self.configurations.hg38_data_version is not None:
            self.application_properties.write(f"exomiser.hg38.data-version={self.configurations.hg38_data_version}\n")

    def write_exomiser_phenotype_data_version(self):
        self.application_properties.write(
            f"exomiser.phenotype.data-version={self.configurations.phenotype_data_version}\n")

    def write_hg19_white_list_path(self):
        self.application_properties.write(
            "exomiser.hg19.variant-white-list-path=${exomiser.hg19.data-version}_hg19_clinvar_whitelist.tsv.gz\n")

    def write_application_properties(self):
        self.write_exomiser_data_directory()
        self.write_exomiser_phenotype_data_version()
        self.write_exomiser_hg19_data_version()
        self.write_hg19_white_list_path()
        self.write_exomiser_hg38_data_version()
        self.application_properties.close()
