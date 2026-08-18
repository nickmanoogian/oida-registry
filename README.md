# Opioid Industry Documents Archive — Data Registry

[![S3 Health Check](https://github.com/nickmanoogian/oida-registry/actions/workflows/health-check.yml/badge.svg)](https://github.com/nickmanoogian/oida-registry/actions/workflows/health-check.yml)

This repository gives you access to the **Opioid Industry Documents Archive (OIDA)** — a public dataset of internal documents from opioid manufacturers and distributors, released as part of litigation and public health research.

You can use this data for research, analysis, mock/test data in projects, or to understand patterns in how opioid products were marketed and prescribed.

---

## What is this repo?

Think of this as a **card catalog**, not a library shelf. The actual data files live in a public storage bucket on Amazon S3 — this repo just contains a map of what's there and tools to pull exactly what you need into your project. Nothing is re-hosted here, and you don't need an Amazon account or any credentials to access the data.

When you use this repo, you're downloading directly from the original public source. That means:
- The data is always the authoritative version
- You only download what you actually need
- Anyone can reproduce your exact dataset by referencing this repo

---

## What's in the dataset?

The archive has two main parts:

### Structured data (analysis-ready spreadsheets)
These are the files most useful for research and mock data. They're in CSV or ZIP format and can be opened in Excel, Python, R, or any data tool.

| File | Size | What it contains |
|------|------|-----------------|
| `prescribers.csv` | 29 MB | Master list of prescribers — links to all other datasets. **Start here.** |
| `mnk_customer_orders.csv` | 38 MB | Mallinckrodt customer orders, including suspicious order flags |
| `oida-image-collection-metadata-version-1.csv.gz` | 1.7 MB | Index of the document image collection |
| `duexis_bydates.csv` | 100 MB | Weekly Duexis prescription counts by prescriber (2012–2013) |
| `sumavel_bydates.csv` | 83 MB | Weekly Sumavel prescription counts by prescriber (2012–2014) |
| `xartemis_bydates.csv` | 161 MB | Weekly Xartemis XR prescription counts by prescriber (2014) |
| `mnk_prescriber_records.zip` | 301 MB | Mallinckrodt prescriber records |
| `insys_authorized_rx.csv.zip` | 693 MB | Insys prescription transaction records (compressed) |
| `exalgo_bydates.csv` | 1.2 GB | Weekly Exalgo prescription counts by prescriber (2012–2014) |
| `image_collection_version_1.zip` | 1.4 GB | Document image collection |
| `pennsaid_bydates.csv` | 1.8 GB | Weekly Pennsaid prescription counts by prescriber (2012–2014) |
| `insys_full_dedup.zip` | 2.7 GB | Full Insys document collection |
| `mckinsey_full_dedup.zip` | 4.0 GB | Full McKinsey document collection |
| `insys_authorized_rx.csv` | 4.6 GB | Insys prescription transaction records (full, uncompressed) |
| `mallinckrodt_full_dedup.zip` | 61 GB | Full Mallinckrodt document collection |

> Each dataset also has a `.readme.txt` file with source notes. For detailed column descriptions, see [`data-products/SCHEMA.md`](data-products/SCHEMA.md).

### Archive indexes (for browsing the raw document archive)

| File | Size | What it contains |
|------|------|-----------------|
| `metadata/oida-index.parquet` | 2.2 GB | Index of every document in the archive |
| `metadata/oida-index-by-artifact.parquet` | 2.6 GB | Same index, grouped by artifact/exhibit |

### Sample

| File | Size | What it contains |
|------|------|-----------------|
| `samples/oida-bulk-download-sample.zip` | 2.4 MB | A small sample of the raw archive — good for exploring the format |

### Raw document archive
The full archive contains **22.3 million individual files** (PDFs, TIFFs, OCR text files) totalling **7.5 TB**. These are split across 16 folders. Use the [manifest](#full-archive-manifest) to browse and selectively download from this archive.

---

## For non-engineers: how to get the data

You don't need to be a programmer to download and use this data. Here's the simplest path:

### Option 1 — Download directly (no setup required)

Every file in the `data-products/` folder can be downloaded directly from the public S3 bucket. Just construct the URL like this:

```
https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/data-products/FILENAME
```

For example, to download `prescribers.csv`, paste this into your browser or use curl:

```
https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/data-products/prescribers.csv
```

### Option 2 — Use the download script (requires Python)

If you have Python installed (it comes pre-installed on Mac):

```bash
# clone this repo
git clone https://github.com/nickmanoogian/oida-registry
cd oida-registry

# see what's available
python scripts/download.py --list

# download a file
python scripts/download.py prescribers.csv --out ./data/
```

---

## For engineers: reproducible project integration

### Setup

```bash
pip install "dvc[s3]"
```

### Pull a file into any project

```bash
# one-time download — file lands in current directory
dvc get https://github.com/nickmanoogian/oida-registry data-products/prescribers.csv

# import with tracked lineage — creates a .dvc pointer file you commit to git
dvc import https://github.com/nickmanoogian/oida-registry data-products/prescribers.csv
```

### Adding to a project so teammates can reproduce it

```bash
# in your project root
dvc import https://github.com/nickmanoogian/oida-registry data-products/prescribers.csv --out data/prescribers.csv

# commit the pointer (not the data)
git add data/prescribers.csv.dvc .gitignore
git commit -m "add OIDA prescribers dataset"

# anyone who clones your project reproduces the exact same file with:
dvc pull
```

### As mock/fixture data in tests

```bash
# pull only the small files — fast enough for CI
make get-small
```

Or in Python:

```python
import subprocess

def fetch_oida(filename, dest="tests/fixtures"):
    subprocess.run([
        "dvc", "get",
        "https://github.com/nickmanoogian/oida-registry",
        f"data-products/{filename}",
        "--out", f"{dest}/{filename}",
    ], check=True)

fetch_oida("prescribers.csv")        # 29 MB — good for CI
fetch_oida("mnk_customer_orders.csv") # 38 MB — includes suspicious order flags
```

---

## ECI real-data export (real OIDA processing fields)

`scripts/export_insys_documents.py` exports the **real** Insys Litigation
Documents straight from the public OIDA index parquet — every document, every
Relativity *processing* field present in the archive (custodian, email
From/To/CC, dates, file type/size/MD5/media type, page count, redaction, Bates,
mentioned), plus a deterministic `OCR Text URL` per document so the real
extracted text can be fetched on demand. No cap, no sampling, no synthetic
values. Review/analytics fields (Responsiveness/Relevance, Privilege, Issue
Tags, Batches, TAR/AL) are intentionally omitted — they are created during
review *inside Relativity* and do not exist in a raw produced archive.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt        # installs duckdb (no separate CLI needed)
make export-insys                      # -> /tmp/oida-large/{documents.csv.gz, custodians.json}
# or: python3 scripts/export_insys_documents.py --out DIR
```

Output: an ~1.63M-row `documents.csv.gz` (~163 MB) plus `custodians.json` (every
real collected custodian + real doc count). The OIDA parquet is public S3;
DuckDB's `httpfs` loads automatically. This is the real dataset ECI consumes for
its dashboard (aggregated downstream; the 1.6M rows are not loaded in-browser).

---

## Relativity mock data — pre-built workspace datasets

If you're building Relativity features and need realistic test data, this repo includes
pre-generated workspace datasets at three litigation scales. These are **not** raw OIDA files —
they are structured CSVs with every Relativity field already populated: custodians, file types,
workflow stages, batch assignments, TAR scores, Bates numbers, privilege flags, email threading,
and more. Built to mirror a real matter, not synthetic random data.

See [`mock-data/RULES.md`](mock-data/RULES.md) for the full specification of what makes these
datasets realistic and how the distributions were chosen.

### Choose your tier

| | Small | Medium | Large |
|---|---|---|---|
| **Documents** | ~1,430 | ~9,800 | ~148,000 |
| **Best for** | Quick tests, CI fixtures, component dev | Feature dev, analytics, full workflow | Scale testing, performance, TAR |
| **Custodians** | 4 | 10 | 40 |
| **File types** | 25 types | 30 types | 30+ types |
| **Includes** | Emails, Office, PDF, Teams, Slack, images | + Google Workspace, Bloomberg, mobile chat | + full distribution across all types |
| **Stored in** | Git (instant) | Release artifact | Release artifact (compressed) |

### Get the small tier (fastest — already in the repo)

```bash
# pull directly into your project — no release download needed
dvc get https://github.com/nickmanoogian/oida-registry mock-data/small/documents.csv
dvc get https://github.com/nickmanoogian/oida-registry mock-data/small/custodians.json
dvc get https://github.com/nickmanoogian/oida-registry mock-data/small/email-families.json
dvc get https://github.com/nickmanoogian/oida-registry mock-data/small/batches.json
```

Or clone and use directly:
```bash
git clone https://github.com/nickmanoogian/oida-registry
# files are already there at mock-data/small/
```

### Get the medium tier (recommended for most feature work)

```bash
dvc get https://github.com/nickmanoogian/oida-registry mock-data/medium/documents.csv
dvc get https://github.com/nickmanoogian/oida-registry mock-data/medium/custodians.json
dvc get https://github.com/nickmanoogian/oida-registry mock-data/medium/email-families.json
dvc get https://github.com/nickmanoogian/oida-registry mock-data/medium/batches.json
```

### Get the large tier (scale and performance testing)

```bash
# documents.csv is compressed — decompress after download
dvc get https://github.com/nickmanoogian/oida-registry mock-data/large/documents.csv.gz
dvc get https://github.com/nickmanoogian/oida-registry mock-data/large/custodians.json
dvc get https://github.com/nickmanoogian/oida-registry mock-data/large/email-families.json.gz
dvc get https://github.com/nickmanoogian/oida-registry mock-data/large/batches.json

gunzip documents.csv.gz
gunzip email-families.json.gz
```

### Load in Python

```python
import pandas as pd, json

docs = pd.read_csv("documents.csv")

# filter by workflow stage
review_pop = docs[docs["Workflow Stage"].str.startswith("Review")]
responsive = docs[docs["Responsiveness"] == "Responsive"]
privileged = docs[docs["Privilege"] == "Privileged"]
produced   = docs[docs["Bates Begin"] != ""]

# filter by file type
emails = docs[docs["File Type Category"].isin(["Email - MSG", "Email - EML"])]
rsmf   = docs[docs["File Type Category"].str.contains("RSMF")]
pdfs   = docs[docs["File Type Category"].str.startswith("PDF")]

# TAR score distribution
import matplotlib.pyplot as plt
review_pop["TAR Score"].astype(float).hist(bins=20)
plt.title("TAR Score Distribution (bimodal)")

# custodians
with open("custodians.json") as f:
    custodians = json.load(f)

# email threading
with open("email-families.json") as f:
    families = json.load(f)
```

---

## Loading into a Relativity workspace

### Option A — Pull the pre-built package (no build step)

There are three packages, and **the clean one is the default**. The other two are opt in and
exist only for failure path testing:

| | What it is |
|---|---|
| `small.zip` | Clean. Everything imports and processes. Use it as fixture data or for a happy path run. |
| `small-errors.zip` | Natives that fail processing, plus documents that process cleanly with an input missing. |
| `broken-load-files/` | Load files that fail at import. Built locally, `.dat` only. |

```bash
# clean package: every native processes successfully
dvc get https://github.com/nickmanoogian/oida-registry load-packages/small.zip
unzip small.zip

# errored package: same documents, 106 natives that genuinely fail processing
dvc get https://github.com/nickmanoogian/oida-registry load-packages/small-errors.zip
unzip small-errors.zip
```

Each contains ~1,423 native files in per-custodian folders, `load-file.dat`,
`custodian-sources.csv` and `IMPORT_README.txt`. Ready to import immediately. The errored
package adds `EXPECTED_ERRORS.csv`.

### Option B — Build from scratch

```bash
# install native file dependencies
pip install python-docx openpyxl python-pptx fpdf2

# build with real OIDA OCR content
make load-small

# or synthetic content only (no network, faster)
make load-small-synthetic
```

Output in `load-packages/small/`:
- `natives/` — 1,400+ actual `.eml`, `.docx`, `.xlsx`, `.pptx`, `.pdf`, `.rsmf` files, in one folder per custodian
- `load-file.dat` — Relativity Concordance load file (53 fields, all metadata)
- `custodian-sources.csv` — one row per custodian: the processing data source setup sheet
- `IMPORT_README.txt` — step-by-step Relativity processing and import instructions

The 13 scripted hot documents (HOT- prefix) get hand-crafted MDL 2804 content —
the SOM override email, the McKinsey turbocharge deck, the IRC call guide, and more.
All other documents use real OIDA OCR text pulled from the S3 archive.

### Custodian folders

Natives are written into the folder structure the metadata describes, mirroring the
`Processing Folder Path` column:

```
natives/
  Michael_Brennan/2014/01/DOC-0000318.docx
  Sarah_Chen/2016/09/DOC-0000722.eml
  Thomas_Bradley/2013/11/DOC-0000229.eml
  Lisa_Torres/...
```

This is what makes the package usable as **raw data**. A Relativity processing set assigns
custodians per data source, so with one folder per custodian you add a data source for each
row in `custodian-sources.csv`, pick the custodian on it, and custodian assignment comes out
of the folder structure. With a single flat folder you would get one custodian for the whole
collection, or you would sort the files by hand.

`custodian-sources.csv` carries name, email, org, department, data source folder, document
count, natives written and total bytes:

| Custodian | Data Source Folder | Documents | Native Bytes |
|---|---|---|---|
| Michael Brennan | `natives\Michael_Brennan` | 370 | 2,614,388 |
| Thomas Bradley | `natives\Thomas_Bradley` | 368 | 2,162,254 |
| Sarah Chen | `natives\Sarah_Chen` | 351 | 2,375,388 |
| Lisa Torres | `natives\Lisa_Torres` | 350 | 3,080,278 |

If you want the old single-directory layout, pass `--flat`. It cannot support per-custodian
data sources, and the generated `IMPORT_README.txt` says so.

### Edge cases: documents that starve a feature

Broken files are the obvious failure mode. The subtler one is a document that processes
perfectly and still leaves a feature with nothing to work with.

The generated tiers are uniform to a fault: every document has a custodian, a date, extracted
text, and `Language = English`. No real matter looks like that, so any feature that aggregates
over a collection has only ever been tested against a complete input.

```bash
make mock-small-edge
# or: python scripts/generate_mock_metadata.py --tier small --edge-cases --out mock-data/small-edge
```

Twelve scenarios, each from a disjoint pool so no document carries two faults: documents with no
custodian, no date, sentinel dates (1601, 2099), no extracted text, non-English and mixed
language, emails with blank or distribution-list-only recipients, orphan attachments, families
naming a document that is absent, the same MD5 under two custodians, and audio/video with no
text at all.

The tier ships `edge-cases.json`: per scenario, what it starves, the count, and the document
list. `validate_mock_data.py` probes every listed document and fails if one is not actually
starved, so the report cannot drift from the data.

**Off by default.** Edge cases are applied after generation on their own RNG stream, so default
output is byte-identical. Committed tiers stay clean, and anything using a tier as fixture data
is unaffected.

The errored load package is built from an edge-case tier, so `small-errors.zip` carries both:
files that fail processing, and documents that process cleanly with a hole in them.

### Load files that fail at import

The two scenarios above break during or after processing. This one breaks before it: a load file
Relativity will not cleanly ingest.

```bash
make load-broken
# or: python scripts/build_broken_load_files.py
```

Seven variants, one fault each: a `NativeFilePath` pointing at a file that is not in the package,
a duplicated Control Number, unparseable dates, a raw column separator inside a field value,
Latin-1 bytes in a file read as UTF-8, a row with fewer fields than the header, and a blank
Control Number.

Only the `.dat` is written. Natives are not duplicated, and every variant points at the same
relative paths as the clean package, so you unzip `small.zip` and drop one `.dat` in beside its
`natives/` folder. `manifest.csv` lists each variant, the rows it affects by control number, and
the failure to expect.

`--verify` checks that every variant actually carries the fault it claims, because a broken load
file that parses cleanly is the same trap as a healthy native behind an error flag.

### Errored files for failure path testing

The default package is clean: every native processes successfully. That is the wrong shape for
bug bashing, where the interesting question is what the product does with documents that fail.

```bash
# pull the pre-built one
dvc get https://github.com/nickmanoogian/oida-registry load-packages/small-errors.zip

# or build it yourself
make load-small-errors
# or: python scripts/build_load_package.py --tier small --with-errors
```

The errored package is a **separate artifact**. `load-packages/small.zip` stays clean, so
nobody gets broken files by accident.

Every document already flagged `Processing Status = Error` in `documents.csv` gets a native
that genuinely fails in the way its `Processing Error Type` describes. In the small tier that
is 106 fabricated files across seven scenarios: password protection, corruption, unsupported
types, extraction failure, container nesting, conversion failure and PDFs with no text layer.
A password protected document is really encrypted, a corrupt file is really truncated.

Push the rate higher than production ever sees:

```bash
python scripts/build_load_package.py --tier small --with-errors --error-rate 0.25
```

The package gains `EXPECTED_ERRORS.csv`, one row per broken document with how it was built, the
error Relativity is expected to report, and whether that outcome is guaranteed. Rows marked
`Guaranteed = no` depend on engine or worker configuration rather than on the file. Encrypted
artefacts use the password `oida`, so you can test the password bank path or the failure path.

Two things are deliberately **not** fabricated. MIP protected rows need a real Microsoft 365
tenant to apply the sensitivity label, so their natives stay healthy and the build says so.
Malware, EICAR strings and zip bombs are out of scope for a shared dataset.

Verify a built package against [`mock-data/RULES.md`](mock-data/RULES.md) Rules 11 and 12:

```bash
make load-validate
# or: python scripts/validate_load_package.py load-packages/small
```

---

### Regenerate with different settings

```bash
# default seed (42) — always produces the same dataset
python scripts/generate_mock_metadata.py --tier small

# different seed — different but equally realistic dataset
python scripts/generate_mock_metadata.py --tier medium --seed 99

# custom output directory
python scripts/generate_mock_metadata.py --tier large --out ./my-test-data/
```

---

## Common scenarios

### "I just want to explore the data before committing to a download"

Start with the 2.4 MB sample — it's a small slice of the raw archive to help you understand the format:

```bash
dvc get https://github.com/nickmanoogian/oida-registry samples/oida-bulk-download-sample.zip
```

For the structured CSVs, you can preview just the first few rows without downloading the whole file:

```python
import pandas as pd

# reads only the first 100 rows — works for any size file
preview = pd.read_csv(
    "https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/data-products/pennsaid_bydates.csv",
    nrows=100
)
print(preview.shape)
print(preview.head())
```

### "I only need one or two columns from a large file"

Use `usecols` to download and parse only the columns you care about — much faster and uses far less memory:

```python
import pandas as pd

# pull just prescriber name, territory, and weekly totals — skip all the date columns
df = pd.read_csv(
    "pennsaid_bydates.csv",
    usecols=["Prescriber Name", "Territory", "13wk Total PENNSAID 1.5", "prescriber_code"]
)
```

### "I want the smallest useful dataset for mock data / CI"

`prescribers.csv` (29 MB) is the best starting point — it's small, has no dependencies, and is the join key for every other dataset. `mnk_customer_orders.csv` (38 MB) is also great for testing order/flagging workflows.

```bash
# pull both in one command
make get-small
```

Or just one:

```bash
dvc get https://github.com/nickmanoogian/oida-registry data-products/prescribers.csv
```

### "I want to browse what's in the raw archive without downloading 7.5 TB"

Download the manifest (581 MB compressed) and filter it locally:

```python
import pandas as pd

df = pd.read_csv("manifest.tsv.gz", sep="\t")

# see what file types exist
print(df["key"].str.split(".").str[-1].value_counts())

# find all files for a specific document
print(df[df["key"].str.contains("ffbb0235")])

# get a random sample of 100 PDFs to download
sample = df[df["key"].str.endswith(".pdf")].sample(100)
```

### "I want to understand the data before writing any code"

Open `prescribers.csv` in Excel or Google Sheets — it's small enough to open directly and gives you a feel for how prescribers are identified and organized. Then cross-reference with [`data-products/SCHEMA.md`](data-products/SCHEMA.md) for column definitions.

### "I'm using this in a shared project and want teammates to get the same data"

Use `dvc import` instead of `dvc get`. It creates a small pointer file you commit to git — when teammates clone the project and run `dvc pull`, they get the exact same file you used:

```bash
dvc import https://github.com/nickmanoogian/oida-registry data-products/prescribers.csv
git add prescribers.csv.dvc .gitignore
git commit -m "add prescribers dataset from OIDA registry"
# teammates run: dvc pull
```

---

## Working with the data

### Where to start

If you're exploring this dataset for the first time:

1. **Start with `prescribers.csv`** (29 MB) — it's the master list of prescribers and joins to every other dataset via the `prescriber_code` / `prescriber_number_code` column.
2. **Pick one bydates file** for the drug you're interested in — these show weekly prescription counts by prescriber over time.
3. **Use `mnk_customer_orders.csv`** if you're interested in distribution/ordering patterns rather than prescriptions.

### Loading the data

**Small files (under ~200 MB) — load directly:**
```python
import pandas as pd

prescribers = pd.read_csv("prescribers.csv")
orders = pd.read_csv("mnk_customer_orders.csv")
```

**Large CSVs (1 GB+) — read in chunks to avoid memory issues:**
```python
import pandas as pd

chunks = []
for chunk in pd.read_csv("pennsaid_bydates.csv", chunksize=10_000):
    # filter or process before accumulating
    chunks.append(chunk[chunk["Territory"] == "Northeast"])

df = pd.concat(chunks)
```

**Parquet files (metadata index) — requires pyarrow:**
```python
pip install pyarrow

import pandas as pd
index = pd.read_parquet("oida-index.parquet")
```

**ZIP files — extract first:**
```python
import zipfile
with zipfile.ZipFile("insys_full_dedup.zip") as z:
    z.extractall("insys_data/")
```

### Joining datasets

The bydates files (Duexis, Exalgo, Pennsaid, etc.) connect to `prescribers.csv` via a shared prescriber key:

| In bydates files | In prescribers.csv |
|---|---|
| `prescriber_code` (last column) | `prescriber_number_code` |

```python
import pandas as pd

prescribers = pd.read_csv("prescribers.csv")
pennsaid    = pd.read_csv("pennsaid_bydates.csv")

# merge to get prescriber details alongside prescription data
merged = pennsaid.merge(
    prescribers,
    left_on="prescriber_code",
    right_on="prescriber_number_code",
    how="left"
)
```

### Understanding the bydates format

The bydates CSVs are in **wide format** — each row is one prescriber, and there are hundreds of columns, one per week. The columns follow the pattern `YYYY-MM-DD-{drug}` for prescription counts and `YYYY-MM-DD-{drug}-market` for the total market.

To work with them in a more standard long format:

```python
import pandas as pd

df = pd.read_csv("pennsaid_bydates.csv")

# identify the weekly columns (they start with a year)
id_cols = ["Prescriber Name", "Address", "Territory", "prescriber_code"]
date_cols = [c for c in df.columns if c[0].isdigit()]

# reshape to long format: one row per prescriber per week
long = df.melt(id_vars=id_cols, value_vars=date_cols,
               var_name="week_drug", value_name="scripts")
```

### Files to avoid loading fully into memory

| File | Size | Recommendation |
|------|------|----------------|
| `insys_authorized_rx.csv` | 4.6 GB | Use chunked reading or filter on load |
| `pennsaid_bydates.csv` | 1.8 GB | Use chunked reading or select columns |
| `exalgo_bydates.csv` | 1.2 GB | Use chunked reading or select columns |
| `mallinckrodt_full_dedup.zip` | 61 GB | Extract only needed files from ZIP |
| `metadata/oida-index.parquet` | 2.2 GB | Use `filters=` param in `read_parquet` to push down predicates |

---

## Full archive manifest

A pre-built index of all **22,307,281 files** in the raw archive (581 MB compressed) is available as a release artifact. It's a gzipped TSV with columns: `key`, `size`, `etag`.

```bash
# download via DVC
dvc get https://github.com/nickmanoogian/oida-registry manifest.tsv.gz

# or direct download
curl -L -O https://github.com/nickmanoogian/oida-registry/releases/download/v1.0.0/manifest.tsv.gz
```

**Browsing the manifest:**

```python
import pandas as pd

df = pd.read_csv("manifest.tsv.gz", sep="\t")

print(f"{len(df):,} files, {df['size'].sum()/1e12:.1f} TB total")

# filter to a specific archive prefix
raw_f = df[df["key"].str.startswith("f/")]

# find all PDFs
pdfs = df[df["key"].str.endswith(".pdf")]

# find all files for a specific document ID
doc = df[df["key"].str.contains("ffbb0235")]
```

To regenerate the manifest if the bucket is updated:

```bash
python scripts/fetch_manifest.py        # full rebuild (~30 min)
python scripts/fetch_manifest.py --prefix f/ --out f_manifest.tsv.gz  # subset
```

---

## Makefile shortcuts

```bash
make list        # list all datasets with sizes
make get-small   # download files under 100 MB (good for mock data / CI)
make get-all     # download all structured datasets
make manifest    # regenerate manifest.tsv.gz
make verify      # check all S3 URLs are still reachable
```

---

## Source and attribution

- **Dataset:** [Opioid Industry Documents Archive](https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/index.html)
- **S3 bucket:** `s3://opioid-industry-documents-archive-dataset-bucket` (public, no credentials required)
- **Registry repo:** https://github.com/nickmanoogian/oida-registry

This registry was built to make the OIDA dataset easier to use reproducibly across projects. The underlying data is a public resource — if you use it, consider citing the original archive.
