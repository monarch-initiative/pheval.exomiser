# Exomiser Runner for PhEval

This is the Exomiser plugin for PhEval. With this plugin, you can leverage the variant prioritisation tool, Exomiser, to run the PhEval pipeline seamlessly. Detailed documentation on how to set up and run the PhEval Makefile pipeline with the Exomiser runner can be found [here](https://monarch-initiative.github.io/pheval/exomiser_pipeline/). The setup process for running the full PhEval Makefile pipeline differs from setting up for a single run. The Makefile pipeline creates directory structures for corpora and configurations to handle multiple run configurations. Detailed instructions on setting up the appropriate directory layout, including the input directory and test data directory, can be found here.

## Installation

You can install the Exomiser directly with PyPi (recommended):

```shell
pip install pheval.exomiser
```

Alternatively you can clone the pheval.exomiser repo and set up the poetry environment:

```shell
git clone https://github.com/monarch-initiative/pheval.exomiser.git
cd pheval.exomiser
poetry shell
poetry install
```

## Configuring a *single* run:

### Setting up the input directory

A `config.yaml` should be located in the input directory and formatted like so:

```yaml
tool: exomiser
tool_version: 13.2.0
variant_analysis: True
gene_analysis: True
disease_analysis: False
tool_specific_configuration_options:
  environment: local
  exomiser_software_directory: exomiser-cli-13.2.0
  analysis_configuration_file: preset-exome-analysis.yml
  max_jobs: 0
  application_properties:
    remm_version:
    cadd_version:
    hg19_data_version: 2302
    hg19_local_frequency_path: # name of hg19 local frequency file 
    hg19_whitelist_path: 2302_hg19_clinvar_whitelist.tsv.gz # only required for Exomiser v13.3.0 and earlier, can be left blank for Exomiser v14.0.0 onwards.
    hg38_data_version: 2302
    hg38_local_frequency_path: # name of hg38 local frequency file 
    hg38_whitelist_path:
    phenotype_data_version: 2302
    cache_type:
    cache_caffeine_spec:
  output_formats: [JSON,HTML] # options include HTML, JSON, TSV_VARIANT, TSV_GENE, VCF
  post_process:
    score_name: combinedScore
    sort_order: DESCENDING
```
The bare minimum fields are filled to give an idea on the requirements. This is so that the application.properties for Exomiser can be correctly configured. An example config has been provided `pheval.exomiser/config.yaml`.

The Exomiser input data directories (phenotype database and variant database) should also be located in the input directory - or a symlink pointing to the location.

The `exomiser_software_directory` points to the name of the Exomiser distribution directory located in the input directory.

The analysis configuration file (in this case: `preset-exome-analysis.yml`) should be located within the input directory.

The whitelist paths for the hg19 and hg38 dbs need only be specified for Exomiser v13.3.0 and earlier (unless specifying your own whitelist), as Exomiser v14.0.0 now includes this in the db.

To save on diskspace we recommend limiting the Exomiser output to JSON, this can be specified by setting the `output_formats` field in the `config.yaml` to [JSON]

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


The overall structure of the input directory should look like this with the cadd, local and remm directories being optional, depending on the exomiser configuration:
```tree
.
├── 2302_hg19
│   ├── 2302_hg19_clinvar_whitelist.tsv.gz
│   ├── 2302_hg19_clinvar_whitelist.tsv.gz.tbi
│   ├── 2302_hg19_genome.h2.db
│   ├── 2302_hg19_transcripts_ensembl.ser
│   ├── 2302_hg19_transcripts_refseq.ser
│   ├── 2302_hg19_transcripts_ucsc.ser
│   └── 2302_hg19_variants.mv.db
├── 2302_phenotype
│   ├── 2302_phenotype.h2.db
│   ├── hp.obo
│   ├── phenix
│   │   ├── ALL_SOURCES_ALL_FREQUENCIES_genes_to_phenotype.txt
│   │   ├── hp.obo
│   │   └── out
│   └── rw_string_10.mv
├── config.yaml
├── exomiser-cli-13.2.0
│   ├── lib
│   └── exomiser-cli-13.2.0.jar
├── preset-exome-analysis.yml
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
### Setting up the testdata directory

The Exomiser plugin for PhEval accepts phenopackets and vcf files as an input for running Exomiser. The plugin can be run in `phenotype_only` mode, where only phenopackets are required as an input, however, this *must* be specified in the `config.yaml` by setting `variant_analysis: False`

The testdata directory should include subdirectories named `phenopackets` and `vcf` if running with variant prioritisation.

e.g., 

```tree
├── testdata_dir
   ├── phenopackets
   └── vcf
```

## Run command

Once the testdata and input directories are correctly configured for the run, the `pheval run` command can be executed.

```bash
pheval run --input-dir /path/to/input_dir \
--testdata-dir /path/to/testdata_dir \
--runner exomiserphevalrunner \
--output-dir /path/to/output_dir \
--version 13.2.0
```

## Common errors

You may see an error that is related to the current `setuptools` being used:

```shell
pkg_resources.extern.packaging.requirements.InvalidRequirement: Expected closing RIGHT_PARENTHESIS
    requests (<3,>=2.12.*) ; extra == 'parse'
             ~~~~~~~~~~^
```

To fix the error, `setuptools` needs to be downgraded to version 66:

```shell
pip uninstall setuptools
pip install -U setuptools=="66"
```
