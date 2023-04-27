# Exomiser Runner for PhEval

This is the Exomiser plugin for PhEval. Highly experimental. Do not use.

## Developers

Warning, the `pheval` library is currently included as a file reference in the toml file.

```
pheval = { path = "/Users/matentzn/ws/pheval" }
```

This will change when pheval is published on pypi.

## Configuring the application.properties:

The input directory config should be formatted like so:

```yaml
tool: exomiser
tool_version: 13.2.0
phenotype_only: True
tool_specific_configuration_options:
  environment: local
  analysis_configuration_file: preset-exome-analysis.yml
  application_properties:
    remm_version:
    cadd_version:
    hg19_data_version: 2302
    hg19_cadd_snv_path:
    hg19_cadd_indel_path:
    hg19_remm_path:
    hg19_local_frequency_path:
    hg38_data_version:
    hg38_cadd_snv_path:
    hg38_cadd_indel_path:
    hg38_remm_path:
    hg38_local_frequency_path:
    phenotype_data_version: 2302
    cache_caffeine_spec:
```
The bare minimum fields are filled to give an idea on the requirements. This is so that the application.properties can be correctly configured.