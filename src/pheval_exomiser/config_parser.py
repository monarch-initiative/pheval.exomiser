from dataclasses import dataclass
from pathlib import Path

import yaml
from serde import serde
from serde.yaml import from_yaml


@serde
@dataclass
class ExomiserConfigRunExomiserManualConfigs:
    exomiser_phenotype_version: str
    exomiser_hg19_version: str
    exomiser_hg38_version: str


@serde
@dataclass
class ExomiserConfigRunExomiserConfigs:
    exomiser_version: str
    path_to_application_properties_config: Path
    application_properties_arguments: ExomiserConfigRunExomiserManualConfigs


@serde
@dataclass
class ExomiserConfigRun:
    environment: str
    phenotype_only: bool
    path_to_exomiser_software_directory: Path
    path_to_analysis_yaml: Path
    exomiser_configurations: ExomiserConfigRunExomiserConfigs
    max_jobs: int


@serde
@dataclass
class ExomiserConfigPostProcess:
    score_name: str
    score_order: str


@serde
@dataclass
class ExomiserConfig:
    run: ExomiserConfigRun
    post_process: ExomiserConfigPostProcess


def parse_exomiser_config(config_path: Path) -> ExomiserConfig:
    """Reads the config file."""
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
    config_file.close()
    return from_yaml(ExomiserConfig, yaml.dump(config))
