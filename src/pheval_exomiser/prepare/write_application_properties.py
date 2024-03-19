import inspect
from pathlib import Path

from pheval_exomiser.constants import EXOMISER_DATA_DIRECTORY_TARGET_DOCKER
from pheval_exomiser.prepare.tool_specific_configuration_options import ExomiserConfigurations


class ExomiserConfigurationFileWriter:
    def __init__(self, input_dir: Path, configurations: ExomiserConfigurations):
        self.input_dir = input_dir
        self.configurations = configurations
        self.application_properties = open(input_dir.joinpath("application.properties"), "w")

    def write_remm_version(self) -> None:
        """Write the remm version to application.properties file."""
        if self.configurations.application_properties.remm_version is not None:
            self.application_properties.write(
                f"remm.version={self.configurations.application_properties.remm_version}\n"
            )

    def write_cadd_version(self) -> None:
        """Write the cadd version to application.properties file."""
        if self.configurations.application_properties.cadd_version is not None:
            self.application_properties.write(
                f"cadd.version={self.configurations.application_properties.cadd_version}\n"
            )

    def write_exomiser_data_directory(self) -> None:
        """Write the exomiser data directory to application.properties file."""
        if self.configurations.environment.lower() == "docker":
            self.application_properties.write(
                f"exomiser.data-directory={EXOMISER_DATA_DIRECTORY_TARGET_DOCKER}\n"
            )
        if self.configurations.environment.lower() == "local":
            self.application_properties.write(f"exomiser.data-directory={self.input_dir}\n")

    def write_exomiser_hg19_data_version(self) -> None:
        """Write the hg19 data version to application.properties file."""
        if self.configurations.application_properties.hg19_data_version is not None:
            self.application_properties.write(
                f"exomiser.hg19.data-version={self.configurations.application_properties.hg19_data_version}\n"
            )

    def write_exomiser_hg19_cadd_snv_path(self) -> None:
        """Write the hg19 cadd snv path to application.properties file."""
        if (
            self.configurations.application_properties.cadd_version is not None
            and self.configurations.application_properties.hg19_data_version is not None
        ):
            self.application_properties.write(
                "exomiser.hg19.cadd-snv-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg19/"
                "whole_genome_SNVs.tsv.gz\n"
            )

    def write_exomiser_hg19_cadd_indel_path(self) -> None:
        """Write the hg19 cadd indel path to application.properties file."""
        if (
            self.configurations.application_properties.cadd_version is not None
            and self.configurations.application_properties.hg19_data_version is not None
        ):
            self.application_properties.write(
                "exomiser.hg19.cadd-in-del-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg19/"
                "InDels.tsv.gz\n"
            )

    def write_exomiser_hg19_remm_path(self) -> None:
        """Write the hg19 remm path to application.properties file."""
        if (
            self.configurations.application_properties.remm_version is not None
            and self.configurations.application_properties.hg19_data_version is not None
        ):
            self.application_properties.write(
                "exomiser.hg19.remm-path="
                "${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg19.tsv.gz\n"
            )

    def write_exomiser_hg19_local_frequency_path(self) -> None:
        """Write the hg19 local frequency path to application.properties file."""
        if self.configurations.application_properties.hg19_local_frequency_path is not None:
            self.application_properties.write(
                f"exomiser.hg19.local-frequency-path="
                f"${{exomiser.data-directory}}/local/"
                f"{self.configurations.application_properties.hg19_local_frequency_path}\n"
            )

    def write_exomiser_hg38_data_version(self) -> None:
        """Write the hg38 data version to application.properties file."""
        if self.configurations.application_properties.hg38_data_version is not None:
            self.application_properties.write(
                f"exomiser.hg38.data-version={self.configurations.application_properties.hg38_data_version}\n"
            )

    def write_exomiser_hg38_cadd_snv_path(self) -> None:
        """Write the hg38 cadd snv path to application.properties file."""
        if (
            self.configurations.application_properties.cadd_version is not None
            and self.configurations.application_properties.hg38_data_version is not None
        ):
            self.application_properties.write(
                "exomiser.hg38.cadd-snv-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg38/"
                "whole_genome_SNVs.tsv.gz\n"
            )

    def write_exomiser_hg38_cadd_indel_path(self) -> None:
        """Write the hg38 cadd indel path to application.properties file."""
        if (
            self.configurations.application_properties.cadd_version is not None
            and self.configurations.application_properties.hg38_data_version is not None
        ):
            self.application_properties.write(
                "exomiser.hg38.cadd-in-del-path="
                "${exomiser.data-directory}/cadd/${cadd.version}/hg38/"
                "InDels.tsv.gz\n"
            )

    def write_exomiser_hg38_remm_path(self) -> None:
        """Write the hg38 remm path to application.properties file."""
        if (
            self.configurations.application_properties.remm_version is not None
            and self.configurations.application_properties.hg38_data_version is not None
        ):
            self.application_properties.write(
                "exomiser.hg38.remm-path="
                "${exomiser.data-directory}/remm/ReMM.v${remm.version}.hg38.tsv.gz\n"
            )

    def write_exomiser_hg38_local_frequency_path(self) -> None:
        """Write the hg38 local frequency path to application.properties file."""
        if self.configurations.application_properties.hg38_local_frequency_path is not None:
            self.application_properties.write(
                f"exomiser.hg38.local-frequency-path="
                f"${{exomiser.data-directory}}/local/"
                f"{self.configurations.application_properties.hg38_local_frequency_path}\n"
            )

    def write_exomiser_phenotype_data_version(self) -> None:
        """Write the phenotype data version to application.properties file."""
        self.application_properties.write(
            f"exomiser.phenotype.data-version={self.configurations.application_properties.phenotype_data_version}\n"
        )

    def write_hg19_white_list_path(self) -> None:
        """Write the hg19 whitelist path to application.properties file."""
        if self.configurations.application_properties.hg19_whitelist_path is not None:
            self.application_properties.write(
                f"exomiser.hg19.variant-white-list-path="
                f"{self.configurations.application_properties.hg19_whitelist_path}\n"
            )

    def write_hg38_white_list_path(self) -> None:
        """Write the hg38 whitelist path to application.properties file."""
        if self.configurations.application_properties.hg38_whitelist_path is not None:
            self.application_properties.write(
                f"exomiser.hg38.variant-white-list-path="
                f"{self.configurations.application_properties.hg38_whitelist_path}\n"
            )

    def write_cache_type(self):
        """Write the cache type to application.properties file."""
        if self.configurations.application_properties.cache_type is not None:
            self.application_properties.write(
                f"spring.cache.type=" f"{self.configurations.application_properties.cache_type}\n"
            )

    def write_cache_spec(self):
        """Write the cache spec to application.properties file."""
        if self.configurations.application_properties.cache_caffeine_spec is not None:
            self.application_properties.write(
                f"spring.cache.caffeine.spec=maximumSize="
                f"{self.configurations.application_properties.cache_caffeine_spec}\n"
            )

    def write_application_properties(self) -> None:
        """Write the application.properties file."""
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name, method in methods:
            if name != "write_application_properties" and name != "__init__":
                method()
        self.application_properties.close()
