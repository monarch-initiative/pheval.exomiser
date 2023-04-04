from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExomiserConfigurations:
    environment: str
    analysis_configuration_file: Path
    remm_version: str
    cadd_version: str
    hg19_data_version: str
    hg19_cadd_snv_path: str
    hg19_cadd_indel_path: str
    hg19_remm_path: str
    hg19_local_frequency_path: str
    hg38_data_version: str
    hg38_cadd_snv_path: str
    hg38_cadd_indel_path: str
    hg38_remm_path: str
    hg38_local_frequency_path: str
    phenotype_data_version: str
    cache_caffeine_spec: str
