from pathlib import Path

from pydantic import BaseModel, Field


class ApplicationProperties(BaseModel):
    """
    Class for defining the application.properties configurations.
    Args:
        remm_version (str): Version of the REMM database
        cadd_version (str): Version of the CADD database
        hg19_data_version (str): Data version of the hg19 Exomiser data
        hg19_local_frequency_path (Path): The file name of the hg19 local frequency file
        hg38_data_version (str): Data version of the hg38 Exomiser data
        hg38_local_frequency_path (Path): The file name of the hg38 local frequency file
        phenotype_data_version (str): Data version of the Exomiser phenotype data
        cache_caffeine_spec (int): Cache limit
    """

    remm_version: str = Field(None)
    cadd_version: str = Field(None)
    hg19_data_version: str = Field(None)
    hg19_local_frequency_path: Path = Field(None)
    hg38_data_version: str = Field(None)
    hg38_local_frequency_path: Path = Field(None)
    phenotype_data_version: str = Field(None)
    cache_type: str = Field(None)
    cache_caffeine_spec: int = Field(None)


class PostProcessing(BaseModel):
    """
    Class for defining the post-processing configurations.
    Args:
        score_name (str): Name of score to extract from results.
        sort_order (str): Order to sort results
    """
    score_name: str = Field(...)
    sort_order: str = Field(...)


class ExomiserConfigurations(BaseModel):
    """
    Class for defining the Exomiser configurations in tool_specific_configurations field,
    within the input_dir config.yaml
    Args:
        environment (str): Environment to run Exomiser, i.e., local/docker
        exomiser_software_directory (Path): Directory name for Exomiser software directory
        analysis_configuration_file (Path): The file name of the analysis configuration file located in the input_dir
        max_jobs (int): Maximum number of jobs to run in a batch
        application_properties (ApplicationProperties): application.properties configurations
        post_process (PostProcessing): Post-processing configurations
    """

    environment: str = Field(...)
    exomiser_software_directory: Path = Field(...)
    analysis_configuration_file: Path = Field(...)
    max_jobs: int = Field(...)
    application_properties: ApplicationProperties = Field(...)
    post_process: PostProcessing = Field(...)
