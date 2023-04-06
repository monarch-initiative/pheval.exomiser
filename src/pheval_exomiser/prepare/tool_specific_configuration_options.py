from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExomiserConfigurations:
    """
    Class for defining the Exomiser configurations in tool_specific_configurations field within the input_dir config.yaml
    Args:
        environment (str): Environment to run Exomiser, i.e., local/docker
        analysis_configuration_file (Path): The file name of the analysis configuration file located in the input_dir
        remm_version (str): Version of the REMM database
        cadd_version (str): Version of the CADD database
        hg19_data_version (str): Data version of the hg19 Exomiser data
        hg19_cadd_snv_path (Path): The file name of the CADD hg19 SNV data file
        hg19_cadd_indel_path (Path): The file name of the CADD hg19 indel data file
        hg19_remm_path (Path): The file name of the REMM hg19 data file
        hg19_local_frequency_path (Path): The file name of the hg19 local frequency file
        hg38_data_version (str): Data version of the hg38 Exomiser data
        hg38_cadd_snv_path (Path): The file name of the CADD hg38 SNV data file
        hg38_cadd_indel_path (Path): The file name of the CADD hg38 indel data file
        hg38_remm_path (Path): The file name of the REMM hg38 data file
        hg38_local_frequency_path (Path): The file name of the hg38 local frequency file
        phenotype_data_version (str): Data version of the Exomiser phenotype data
        cache_caffeine_spec (int): Cache limit
    """
    environment: str
    analysis_configuration_file: Path
    remm_version: str
    cadd_version: str
    hg19_data_version: str
    hg19_cadd_snv_path: Path
    hg19_cadd_indel_path: Path
    hg19_remm_path: Path
    hg19_local_frequency_path: Path
    hg38_data_version: str
    hg38_cadd_snv_path: Path
    hg38_cadd_indel_path: Path
    hg38_remm_path: Path
    hg38_local_frequency_path: Path
    phenotype_data_version: str
    cache_caffeine_spec: int
