from dataclasses import dataclass
from pathlib import Path

import yaml
from serde import serde
from serde.yaml import from_yaml

# @serde
# @dataclass
# class ExomiserPrepareScramble:
#     scramble_semsim: float
#     scramble_phenopacket: float
#
#
# @serde
# @dataclass
# class ExomiserPrepareUpdatePhenopacket:
#     update: bool
#     gene_identifer_to_update: str
#
#
# @serde
# @dataclass
# class ExomiserPrepareSpikeVcf:
#     spike: bool
#     path_to_template_vcf: Path | None
#     path_to_template_vcf_directory: Path | None
#
#
# @serde
# @dataclass
# class ExomiserPrepareConvertAnalysisYaml:
#     convert: bool
#     path_to_diagnoses_file: Path | None
#
#
# @serde
# @dataclass
# class ExomiserConfigPrepare:
#     scramble: ExomiserPrepareScramble
#     update_phenopacket_gene_identifier: ExomiserPrepareUpdatePhenopacket
#     create_spiked_vcf: ExomiserPrepareSpikeVcf
#     convert_exomiser_analysis_yaml: ExomiserPrepareConvertAnalysisYaml
#
#
# @serde
# @dataclass
# class ExomiserConfigRunPrepareBatch:
#     max_jobs: int
#
#
# @serde
# @dataclass
# class ExomiserConfigRunExomiserManualConfigs:
#     exomiser_phenotype_version: str
#     exomiser_hg19_version: str
#     exomiser_hg38_version: str
#
#
# @serde
# @dataclass
# class ExomiserConfigRunExomiserConfigs:
#     exomiser_version: str
#     path_to_application_properties_config: Path | None
#     exomiser_data_directory: Path
#     application_properties_arguments: ExomiserConfigRunExomiserManualConfigs
#
#
# @serde
# @dataclass
# class ExomiserConfigSingleRun:
#     prepare_batch: ExomiserConfigRunPrepareBatch
#     run_identifier: str
#     exomiser_configurations: ExomiserConfigRunExomiserConfigs
#     path_to_exomiser_software_directory: Path
#     path_to_analysis_yaml: Path
#     path_to_input_phenopacket_data: Path
#     path_to_input_vcf: Path
#     path_to_output_option_file: Path | None
#     path_to_output_option_directory: Path | None
#
#
# @serde
# @dataclass
# class ExomiserConfigRun:
#     environment: str
#     runs: List[ExomiserConfigSingleRun]
#
#
# @serde
# @dataclass
# class ExomiserConfigPostProcessing:
#     benchmark_gene_prioritisation: bool
#     benchmark_variant_prioritisation: bool
#     ranking_method: str
#     threshold: float
#     output_prefix: str
#
#
# @serde
# @dataclass
# class ExomiserConfig:
#     prepare: ExomiserConfigPrepare
#     run: ExomiserConfigRun
#     post_processing: ExomiserConfigPostProcessing


# def parse_exomiser_config(config_path: Path) -> ExomiserConfig:
#     """Reads the config file."""
#     with open(config_path, "r") as config_file:
#         config = yaml.safe_load(config_file)
#     config_file.close()
#     return from_yaml(ExomiserConfig, yaml.dump(config))


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
    path_to_exomiser_software_directory: Path
    path_to_analysis_yaml: Path
    exomiser_configurations: ExomiserConfigRunExomiserConfigs
    max_jobs: int


@serde
@dataclass
class ExomiserConfigPostProcess:
    ranking_method: str


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
