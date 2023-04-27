from pathlib import Path

from pydantic import BaseModel, Field


class ApplicationProperties(BaseModel):
    """
    Class for defining the application.properties configurations.
    Args:
        remm_version (str): Version of the REMM database
        cadd_version (str): Version of the CADD database
        hg19_data_version (str): Data version of the hg19 Exomiser data
        hg19_cadd_snv_path (Path): The file name of the CADD hg19 SNV data file
        hg19_cadd_indel_path (Path): The file name of the CADD hg19 indel data file
        hg19_remm_path (bool): Boolean to include hg19 remm path or not
        hg19_local_frequency_path (Path): The file name of the hg19 local frequency file
        hg38_data_version (str): Data version of the hg38 Exomiser data
        hg38_cadd_snv_path (Path): The file name of the CADD hg38 SNV data file
        hg38_cadd_indel_path (Path): The file name of the CADD hg38 indel data file
        hg38_remm_path (bool): Boolean to include hg38 remm path or not
        hg38_local_frequency_path (Path): The file name of the hg38 local frequency file
        phenotype_data_version (str): Data version of the Exomiser phenotype data
        cache_caffeine_spec (int): Cache limit
    """

    remm_version: str = Field(None)
    cadd_version: str = Field(None)
    hg19_data_version: str = Field(None)
    hg19_cadd_snv_path: Path = Field(None)
    hg19_cadd_indel_path: Path = Field(None)
    hg19_remm_path: bool = Field(None)
    hg19_local_frequency_path: Path = Field(None)
    hg38_data_version: str = Field(None)
    hg38_cadd_snv_path: Path = Field(None)
    hg38_cadd_indel_path: Path = Field(None)
    hg38_remm_path: bool = Field(None)
    hg38_local_frequency_path: Path = Field(None)
    phenotype_data_version: str = Field(None)
    cache_caffeine_spec: int = Field(None)


class ExomiserConfigurations(BaseModel):
    """
    Class for defining the Exomiser configurations in tool_specific_configurations field,
    within the input_dir config.yaml
    Args:
        environment (str): Environment to run Exomiser, i.e., local/docker
        analysis_configuration_file (Path): The file name of the analysis configuration file located in the input_dir
        application_properties (ApplicationProperties): application.properties configurations
    """

    environment: str = Field(...)
    analysis_configuration_file: Path = Field(...)
    application_properties: ApplicationProperties = Field(...)
