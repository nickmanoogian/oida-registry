# Opioid Industry Documents Archive — DVC Data Registry

A [DVC data registry](https://dvc.org/doc/use-cases/data-registry) providing reproducible, versioned access to the [Opioid Industry Documents Archive (OIDA)](https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/index.html) — a public dataset of internal documents from opioid manufacturers and distributors.

**No data is stored here.** This repo contains only `.dvc` pointer files that let you pull exactly the files you need from the original public S3 bucket — no AWS credentials required.

---

## Available datasets

### `data-products/` — Structured datasets (analysis-ready)

| File | Size | Description |
|------|------|-------------|
| `prescribers.csv` | 29 MB | Master prescriber list — joins to all bydates files |
| `mnk_customer_orders.csv` | 38 MB | Mallinckrodt customer order records |
| `mnk_customer_orders.csv.zip` | 3.6 MB | Mallinckrodt customer orders (compressed) |
| `oida-image-collection-metadata-version-1.csv.gz` | 1.7 MB | Image collection metadata |
| `duexis_bydates.csv` | 100 MB | Duexis prescriptions by date |
| `sumavel_bydates.csv` | 83 MB | Sumavel prescriptions by date |
| `xartemis_bydates.csv` | 161 MB | Xartemis prescriptions by date |
| `mnk_prescriber_records.zip` | 301 MB | Mallinckrodt prescriber records |
| `insys_authorized_rx.csv.zip` | 693 MB | Insys authorized prescriptions (compressed) |
| `exalgo_bydates.csv` | 1.2 GB | Exalgo prescriptions by date |
| `image_collection_version_1.zip` | 1.4 GB | Document image collection v1 |
| `pennsaid_bydates.csv` | 1.8 GB | Pennsaid prescriptions by date |
| `insys_full_dedup.zip` | 2.7 GB | Insys full deduplicated dataset |
| `mckinsey_full_dedup.zip` | 4.0 GB | McKinsey full deduplicated dataset |
| `insys_authorized_rx.csv` | 4.6 GB | Insys authorized prescriptions (full CSV) |
| `mallinckrodt_full_dedup.zip` | 61 GB | Mallinckrodt full deduplicated dataset |

Each dataset has a corresponding `.readme.txt` with source notes. See [`data-products/SCHEMA.md`](data-products/SCHEMA.md) for full column descriptions.

### `metadata/` — Archive indexes (Parquet)

| File | Size | Description |
|------|------|-------------|
| `metadata/oida-index.parquet` | 2.2 GB | Full document index |
| `metadata/oida-index-by-artifact.parquet` | 2.6 GB | Document index grouped by artifact |

### `samples/` — Sample data

| File | Size | Description |
|------|------|-------------|
| `samples/oida-bulk-download-sample.zip` | 2.4 MB | Small sample of the bulk archive |

### Raw document archive — 22.3 million files, 7.5 TB

The full archive is split across 16 single-letter prefix directories (`f/`, `g/`, `h/`, ...), each containing ~1.4 million individual PDFs, TIFFs, and OCR files (~460 GB each). See [Generating the full manifest](#generating-the-full-manifest) to browse or selectively download from the raw archive.

---

## Quickstart

### Option A — DVC (recommended, reproducible)

```bash
pip install "dvc[s3]"

# pull a single file into the current directory
dvc get https://github.com/nickmanoogian/oioda-registry data-products/prescribers.csv

# or import with lineage tracking into your own project
dvc import https://github.com/nickmanoogian/oioda-registry data-products/pennsaid_bydates.csv
```

### Option B — Direct download (no DVC needed)

```bash
git clone https://github.com/nickmanoogian/oioda-registry
cd oioda-registry

# list available files
python scripts/download.py --list

# download one or more files
python scripts/download.py prescribers.csv --out ./data/
python scripts/download.py pennsaid_bydates.csv mnk_customer_orders.csv --out ./data/
```

---

## Using in your project

### With DVC (full lineage tracking)

```bash
# in your project root
dvc import https://github.com/nickmanoogian/oioda-registry data-products/insys_full_dedup.zip

# this creates insys_full_dedup.zip.dvc — commit it to git
git add insys_full_dedup.zip.dvc .gitignore
git commit -m "add OIDA insys dataset"

# teammates reproduce it with
dvc pull
```

### As mock/fixture data in tests

```python
import subprocess

def fetch_oida(filename, dest="tests/fixtures"):
    subprocess.run([
        "dvc", "get",
        "https://github.com/nickmanoogian/oioda-registry",
        f"data-products/{filename}",
        "--out", f"{dest}/{filename}",
    ], check=True)

fetch_oida("prescribers.csv")   # 29 MB — fast enough for CI
fetch_oida("mnk_customer_orders.csv")
```

---

## Full archive manifest

A pre-built manifest of all **22,307,281 files** (581 MB compressed) is available as a release artifact:

```bash
# download via DVC
dvc get https://github.com/nickmanoogian/oioda-registry manifest.tsv.gz

# or direct download
curl -L -O https://github.com/nickmanoogian/oioda-registry/releases/download/v1.0.0/manifest.tsv.gz
```

Columns: `key`, `size`, `etag`

```python
import pandas as pd

df = pd.read_csv("manifest.tsv.gz", sep="\t")

# browse the raw document archive for a specific prefix
raw_f = df[df["key"].str.startswith("f/")]

# filter by file type
pdfs = df[df["key"].str.endswith(".pdf")]
```

To regenerate from scratch (e.g. if the bucket is updated):

```bash
# rewrites manifest.tsv.gz locally — takes ~30 min for 22M files
python scripts/fetch_manifest.py

# or just a subset
python scripts/fetch_manifest.py --prefix f/f/b/ --out fb_manifest.tsv.gz
```

---

## Source

- **Dataset:** [Opioid Industry Documents Archive](https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/index.html)
- **S3 bucket:** `s3://opioid-industry-documents-archive-dataset-bucket` (public, no credentials required)
- **Registry repo:** https://github.com/nickmanoogian/oioda-registry
