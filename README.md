# Opioid Industry Documents Archive — DVC Data Registry

A [DVC data registry](https://dvc.org/doc/use-cases/data-registry) providing reproducible, versioned access to the [Opioid Industry Documents Archive (OIDA)](https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/index.html) — a public dataset of internal documents from opioid manufacturers and distributors.

**No data is stored here.** This repo contains only `.dvc` pointer files that let you pull exactly the files you need from the original public S3 bucket — no AWS credentials required.

---

## Available datasets

| File | Size | Description |
|------|------|-------------|
| `duexis_bydates.csv` | 100 MB | Duexis prescriptions by date |
| `exalgo_bydates.csv` | 1.2 GB | Exalgo prescriptions by date |
| `image_collection_version_1.zip` | 1.4 GB | Document image collection v1 |
| `insys_authorized_rx.csv` | 4.6 GB | Insys authorized prescriptions (full CSV) |
| `insys_authorized_rx.csv.zip` | 693 MB | Insys authorized prescriptions (compressed) |
| `insys_full_dedup.zip` | 2.7 GB | Insys full deduplicated dataset |
| `mallinckrodt_full_dedup.zip` | 61 GB | Mallinckrodt full deduplicated dataset |
| `mckinsey_full_dedup.zip` | 4.0 GB | McKinsey full deduplicated dataset |
| `mnk_customer_orders.csv` | 38 MB | Mallinckrodt customer orders |
| `mnk_customer_orders.csv.zip` | 3.6 MB | Mallinckrodt customer orders (compressed) |
| `mnk_prescriber_records.zip` | 301 MB | Mallinckrodt prescriber records |
| `oida-image-collection-metadata-version-1.csv.gz` | 1.7 MB | Image collection metadata |
| `pennsaid_bydates.csv` | 1.8 GB | Pennsaid prescriptions by date |
| `prescribers.csv` | 29 MB | Prescriber records |
| `sumavel_bydates.csv` | 83 MB | Sumavel prescriptions by date |
| `xartemis_bydates.csv` | 161 MB | Xartemis prescriptions by date |

Each dataset also has a corresponding `.readme.txt` with source notes.

The raw document archive contains ~7 million individual PDFs, TIFFs, and OCR files (~2.4 TB). See [Generating the full manifest](#generating-the-full-manifest) below.

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

## Generating the full manifest

To get a TSV listing of all ~7M files in the archive (keys, sizes, ETags):

```bash
# writes manifest.tsv.gz to the current directory (~200 MB compressed)
python scripts/fetch_manifest.py

# subset — just the document archive for a specific prefix
python scripts/fetch_manifest.py --prefix f/f/b/ --out fb_manifest.tsv.gz
```

The manifest is not committed to this repo (too large for git) but can be regenerated at any time from the public S3 bucket.

---

## Source

- **Dataset:** [Opioid Industry Documents Archive](https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/index.html)
- **S3 bucket:** `s3://opioid-industry-documents-archive-dataset-bucket` (public, no credentials required)
- **Registry repo:** https://github.com/nickmanoogian/oioda-registry
