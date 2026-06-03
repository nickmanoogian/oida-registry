# Opioid Industry Documents Archive — DVC Data Registry

A [DVC data registry](https://dvc.org/doc/use-cases/data-registry) providing reproducible, versioned access to the [Opioid Industry Documents Archive (OIDA)](https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/index.html) public dataset.

Data lives in the original public S3 bucket — nothing is re-hosted here. This repo contains only pointer files (`.dvc`) that let you pull exactly the files you need into your own project.

## Dataset overview

| File | Size | Description |
|------|------|-------------|
| `data-products/duexis_bydates.csv` | 100 MB | Duexis prescriptions by date |
| `data-products/exalgo_bydates.csv` | 1.2 GB | Exalgo prescriptions by date |
| `data-products/image_collection_version_1.zip` | 1.4 GB | Document image collection v1 |
| `data-products/insys_authorized_rx.csv` | 4.6 GB | Insys authorized prescriptions |
| `data-products/insys_authorized_rx.csv.zip` | 693 MB | Insys authorized prescriptions (compressed) |
| `data-products/insys_full_dedup.zip` | 2.7 GB | Insys full deduplicated dataset |
| `data-products/mallinckrodt_full_dedup.zip` | 61 GB | Mallinckrodt full deduplicated dataset |
| `data-products/mckinsey_full_dedup.zip` | 4.0 GB | McKinsey full deduplicated dataset |
| `data-products/mnk_customer_orders.csv` | 38 MB | Mallinckrodt customer orders |
| `data-products/mnk_prescriber_records.zip` | 301 MB | Mallinckrodt prescriber records |
| `data-products/oida-image-collection-metadata-version-1.csv.gz` | 1.7 MB | Image collection metadata |
| `data-products/pennsaid_bydates.csv` | 1.8 GB | Pennsaid prescriptions by date |
| `data-products/prescribers.csv` | 29 MB | Prescriber records |
| `data-products/sumavel_bydates.csv` | 83 MB | Sumavel prescriptions by date |
| `data-products/xartemis_bydates.csv` | 161 MB | Xartemis prescriptions by date |

The raw document archive (`f/`) contains ~3 million individual PDFs, TIFFs, and OCR files totalling ~1 TB. See `manifest.tsv` for the full listing.

## Requirements

```bash
pip install "dvc[s3]"
```

## Usage

### Pull a single file into your project

```bash
dvc get https://github.com/nickmanoogian/oioda-registry data-products/pennsaid_bydates.csv
```

### Import with lineage tracking (recommended)

```bash
# in your project's root
dvc import https://github.com/nickmanoogian/oioda-registry data-products/insys_full_dedup.zip

# later, update to latest version
dvc update insys_full_dedup.zip.dvc
```

This creates a `.dvc` file in your project that records the exact source and version. Anyone who clones your project can reproduce the same data with `dvc pull`.

### Pull multiple files

```bash
# clone this registry locally
git clone https://github.com/nickmanoogian/oioda-registry
cd oioda-registry

# pull specific datasets
dvc pull data-products/pennsaid_bydates.csv
dvc pull data-products/prescribers.csv
```

### Use as mock data in tests / notebooks

```python
import subprocess, os

def get_oioda(path, dest="."):
    """Download a file from the OIDA registry."""
    subprocess.run([
        "dvc", "get",
        "https://github.com/nickmanoogian/oioda-registry",
        path, "--out", os.path.join(dest, os.path.basename(path))
    ], check=True)

get_oioda("data-products/prescribers.csv", dest="tests/fixtures/")
```

## Full manifest

`manifest.tsv` contains the complete listing of all ~3M files in the archive with keys, sizes, and ETags.

## Source

Original dataset: [Opioid Industry Documents Archive](https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/index.html)  
S3 bucket: `s3://opioid-industry-documents-archive-dataset-bucket` (public, no credentials required)
