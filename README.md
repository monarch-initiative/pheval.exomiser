# Exomiser Runner for PhEval

This is the Exomiser plugin for PhEval. Highly experimental. Do not use.

## Developers

Warning, the `pheval` library is currently included as a file reference in the toml file.

```
pheval = { path = "/Users/matentzn/ws/pheval" }
```

This will change when pheval is published on pypi.

## Configuring the application.properties:

The input directory config.yaml should be formatted like so:

```yaml
tool: exomiser
tool_version: 13.2.0
phenotype_only: False # NOTE phenotype-only preset analysis should only be run with Exomiser versions >= 13.2.0
tool_specific_configuration_options:
  environment: local
  exomiser_software_directory: exomiser-cli-13.2.0
  analysis_configuration_file: preset-exome-analysis.yml
  max_jobs: 0
  application_properties:
    remm_version:
    cadd_version:
    hg19_data_version: 2302
    hg19_local_frequency_path:
    hg38_data_version: 2302
    phenotype_data_version: 2302
    cache_type:
    cache_caffeine_spec:
  post_process:
    score_name: combinedScore
    sort_order: DESCENDING
```
The bare minimum fields are filled to give an idea on the requirements. This is so that the application.properties can be correctly configured. An example config has been provided `pheval.exomiser/config.yaml`.

The analysis configuration file should be located within the input directory.

If using optional databases, such as REMM/CADD/local frequency the optional data input should look like so in the input
directory:

```tree
├── cadd
│   └── {{CADD-VERSION}}
│       ├── hg19
│       │   ├── InDels.tsv.gz
│       │   └── whole_genome_SNVs.tsv.gz
│       └── hg38
│           ├── InDels.tsv.gz
│           └── whole_genome_SNVs.tsv.gz
├── local
│   ├── local_frequency_test_hg19.tsv.gz
│   └── local_frequency_test_hg38.tsv.gz
└── remm
    ├── ReMM.v{{REMM-VERSION}}.hg19.tsv.gz
    └── ReMM.v{{REMM-VERSION}}.hg38.tsv.gz
```