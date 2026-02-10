# Exomiser Runner for PhEval

This is the [Exomiser](https://github.com/exomiser/Exomiser) plugin for PhEval. With this plugin, you can leverage the variant prioritisation tool, Exomiser, to run the PhEval pipeline seamlessly. Instructions for setting up the appropriate directory layout, including the input directory and test data directory for a single PhEval run, can be found here

---

## Contents

- [Quick start](#quick-start-running-exomiser-with-pheval)
- [Installation](#installation)
- [Running with `pheval run`](#running-with-pheval-run)
- [Input directory structure](#input-directory-structure)
- [Test data directory structure](#testdata-directory-structure)
- [Post-processing pre-generated Exomiser results](#post-processing-pre-generated-exomiser-results)
- [Generating Exomiser batch files](#generating-exomiser-batch-files)
- [Outputs](#outputs)

---

## Quick start: running Exomiser with PhEval

```bash
pheval run \
  --input-dir /path/to/input_dir \
  --testdata-dir /path/to/testdata_dir \
  --runner exomiserphevalrunner \
  --output-dir /path/to/output_dir \
  --version 15.0.0
```

This command will:

1. Prepare Exomiser inputs 
2. Execute Exomiser  
3. Post-process raw Exomiser outputs into **PhEval-standardised Parquet results** ready for benchmarking  

---

## Installation

Install from PyPI (recommended):

```bash
pip install pheval.exomiser
```

Or from source:

```bash
git clone https://github.com/monarch-initiative/pheval.exomiser.git
cd pheval.exomiser
poetry install
poetry shell
```

---

## Running with `pheval run`

The `pheval run` command manages the full lifecycle:

prepare → run → post-process.

```bash
pheval run \
  --input-dir /path/to/input_dir \
  --testdata-dir /path/to/testdata_dir \
  --runner exomiserphevalrunner \
  --output-dir /path/to/output_dir \
  --version 15.0.0
```

---

## Input directory structure

The input directory contains **all Exomiser configuration, databases, and software**.

### Required files

```text
input_dir/
├── config.yaml
├── exomiser-cli-15.0.0/
│   └── exomiser-cli-15.0.0.jar
├── preset-exome-analysis.yml
├── 2302_phenotype/
├── 2302_hg19/
└── 2302_hg38/
```

### `config.yaml`

```yaml
tool: exomiser
tool_version: 15.0.0
# NOTE gene-only preset analysis should only be run with Exomiser versions >= 13.2.0
variant_analysis: true
gene_analysis: true
disease_analysis: false
tool_specific_configuration_options:
  environment: local
  exomiser_software_directory: exomiser-cli-15.0.0
  analysis_configuration_file: preset-exome-analysis.yml # can be blank if running without VCF, alternatively specify your own analysis configuration file for phenotype only
  max_jobs: 0
  application_properties:
    remm_version:
    cadd_version:
    hg19_data_version: "2508"
    hg19_local_frequency_path:
    hg19_whitelist_path:
    hg38_data_version: "2508"
    hg38_local_frequency_path:
    hg38_whitelist_path:
    phenotype_data_version: "2508"
    # either none, simple, or caffeine
    cache_type: none
    cache_caffeine_spec:
  output_formats: [PARQUET] # options include HTML, JSON, PARQUET (v15.0.0 onwards), TSV_VARIANT, TSV_GENE, VCF
  post_process:
    # For Exomiser < 15.0.0, valid ranking methods include combinedScore, priorityScore, variantScore or pValue
    # For Exomiser >= 15.0.0, valid ranking methods include geneCombinedScore, geneVariantScore or pValue
    score_name: geneCombinedScore
    # sort order should be specified to either ASCENDING or DESCENDING
    # ASCENDING orders results with the lowest values ranked first
    # DESCENDING orders results with the highest values ranked first
    # NOTE when changing the score_name ensure the sort_order is also correct
    sort_order: DESCENDING
```

### Optional databases

```text
input_dir/
├── cadd/
│   └── {{CADD-VERSION}}/
│       ├── hg19/
│       └── hg38/
├── local/
│   ├── local_frequency_test_hg19.tsv.gz
│   └── local_frequency_test_hg38.tsv.gz
└── remm/
    ├── ReMM.v{{REMM-VERSION}}.hg19.tsv.gz
    └── ReMM.v{{REMM-VERSION}}.hg38.tsv.gz
```

---

## Testdata directory structure

```text
testdata_dir/
├── phenopackets/
└── vcf/            # optional
```

### Phenotype-only mode

Set:

```yaml
variant_analysis: false
```

Only `phenopackets/` is required.

> **Important**  
> If `variant_analysis: true` and no `vcf/` directory exists, the VCF path
> will be taken from the Phenopacket.

---

## Post-processing pre-generated Exomiser results

If Exomiser was run outside PhEval:

```bash
pheval-exomiser post-process-exomiser-results \
  --results-dir /path/to/exomiser_results \
  --phenopacket-dir /path/to/phenopackets \
  --output-dir /path/to/write/output \
  --score-name geneCombinedScore \
  --gene-analysis \
  --variant-analysis \
  --version 15.0.0
```

Use `pheval-exomiser post-process-exomiser-results --help` for more options.

### ⚠️ Critical file naming rule (stem matching)

PhEval matches results to cases using **file stem equality**.

```text
Phenopacket: patient_001.json
Result file: patient_001.json              ✅
Result file: patient_001-exomiser.json     ✅ (auto-stripped)
Result file: patient_001_run1.json         ❌
```

**Rule:** the result filename stem **must exactly match** the phenopacket stem.

---

## Generating Exomiser batch files

Generate batch scripts without running Exomiser:

```bash
pheval-exomiser prepare-exomiser-batch \
  --phenopacket-dir /phenopackets \
  --vcf-dir /vcf \
  --variant-analysis \
  --analysis-yaml preset-exome-analysis.yml \
  --output-dir /batch_files \
  --results-dir /exomoiser_results
  --exomiser-version 15.0.0
  --output-formats PARQUET
  --output-formats HTML 
```

Use `pheval-exomiser prepare-exomiser-batch --help` for more options.

This writes batch files under `tool_input_commands/`.

---

## Outputs

```text
output_dir/
├── pheval_gene_results/
├── pheval_variant_results/
├── pheval_disease_results/
├── raw_results/
└── results.yml
```

These outputs are directly consumable by PhEval benchmarking utilities.