# Mock Data — MDL 2804 Relativity Workspace Datasets

Pre-generated Relativity workspace metadata built around **MDL 2804, the National Prescription
Opiate Litigation** — the real federal multi-district case against opioid manufacturers,
distributors, and consultants. Three defendant organizations are represented: Mallinckrodt,
Insys Therapeutics, and McKinsey & Co.

The data tells a coherent story across four phases, with scripted hot documents, scripted
email threads, phase-aware responsiveness rates, and issue tag clustering that reflects how
the case actually unfolded.

See [`DEMO_GUIDE.md`](DEMO_GUIDE.md) for how to walk through this dataset in a Relativity demo.
See [`RULES.md`](RULES.md) for the full specification behind the distributions and file types.
See [`../docs/REQUEST_TEMPLATE.md`](../docs/REQUEST_TEMPLATE.md) if you are about to ask for a
corpus: most of what people ask for is already a flag, and the parts that are not are listed.

---

## Tiers at a glance

| | Small | Medium | Large | Extra large |
|---|---|---|---|---|
| **Documents** | 1,439 | 9,980 | 148,235 | 275,273 |
| **Custodians** | 10 (8 MNK + 1 Insys + 1 McKinsey) | 10 (7 MNK + 2 Insys + 1 McKinsey) | 40 (36 MNK + 2 Insys + 1 McKinsey + 1 outside counsel) | 40, the same roster as large |
| **Orgs** | 3 | 3 | 4 (+ outside counsel) | 4 (+ outside counsel) |
| **Phases** | 2–3 | 1–4 | 1–4 | 1–4 |
| **Scripted hot docs** | 8 | 11 | 13 | 13 |
| **Scripted threads** | 2 | 5 | 5 | 5 |
| **Planted findings** | 5 | 5 | 5 | 5 |
| **External entities** | 40 (28 singletons) | 60 (42) | 120 (84) | 120 (84) |
| **Aliased people** | 2 | 3 | 5 | 5 |
| **PI instances** | 102 | 443 | 3,326 | 6,048 |
| **Second languages** | German 2.0% | German 1.5%, Polish 1.0% | German 1.2%, Polish 0.8%, Spanish 0.4% | German 1.2%, Polish 0.8%, Spanish 0.4% |
| **Sent to review** | 724 | 4,002 | 56,344 | 104,618 |
| **Responsive** | 213 | 1,089 | 14,434 | 26,653 |
| **Privileged** | 30 | 146 | 1,991 | 3,654 |
| **`documents.csv`** | 1.4 MB | 9 MB | 130 MB | 260 MB |
| **Where it lives** | in git | v1.15.0 release, via DVC | v1.15.0 release, via DVC | v1.15.0 release, via DVC |

---

## What each widget can be tested against

Volume is not what people ask for. They ask whether a dataset can exercise the thing they
are building, so this is the table to read first. Measured on the **small** tier.

| Widget | What the tier gives it | Gaps |
|---|---|---|
| **Key Relationships** | 10 custodians, 45 internal pairs, an 8.5x volume spread (323 documents down to 38), **44 non-custodian entities** past the production cap of 25, **28 of them on a single document**, and **2 people sending from two addresses** for name normalisation (Rule 20). Plus Rule 18's principal, its decoy, and a **planted negative**: a pair corresponding at volume about one subject that touches no matter issue and appears nowhere else, so a correct "nothing here" can be told from a broken analysis | — |
| **Collection Coverage** | 48 months of dates with a real shape (15 to 48 documents per month, not a flat line), 10 per-custodian data source folders, hold status variation, and every native stamped from the manifest (Rule 19) | The data source axis is *custodian*, not source type: there is no `Data Source` field distinguishing Exchange from OneDrive from a mobile extraction, so sources with genuinely different metadata profiles cannot be compared. No deliberate collection gap or spike. |
| **File Types** | 25 distinct file type categories, containers with real children (Rule 3), chat and mobile RSMF, audio and video flagged unviewable, legacy formats, and unsupported types that land in error (Rule 6) | — |
| **Document Categories** | Four narrative phases with distinct subject matter, 8 issue tag clusters, a second-language population on an unrelated topic, and one document dense with PI and irrelevant to the matter | No population deliberately straddling two obvious categories. |
| **PI Detect** | 102 instances across 18 documents (Rule 16), spread over email bodies, spreadsheet cells, a PDF form and a chat, all non-issuable values, with `pi-ground-truth.csv` to diff against | — |
| **Primary Language Composition** | German at 2.0% on unrelated facilities notices (Rule 17), real prose in the natives, tunable with `--second-language-share` | Only one second language in the small tier. Medium adds Polish, large and extra large add Spanish. |

For scale rather than coverage, the **extra large** tier is the same matter at 275,273
documents, above a quarter of a million:

```bash
make mock-xlarge
```

Add `--edge-cases` to starve any of them on purpose: no custodian, no date, a 1601 date, no
extracted text, an unexpected language, an orphan attachment, more text than a model
context holds. See Rule 13.

Two failure layers are opt in on the load package rather than the tier: `--with-errors`
fabricates natives that genuinely fail processing (Rule 12), and `build_broken_load_files.py`
produces load files that fail at import.

---

## Files per tier

| File | Description |
|------|-------------|
| `documents.csv` | One row per document. Every Relativity field + narrative fields. |
| `custodians.json` | Custodian profiles — name, org, role, narrative description, hold status. |
| `email-families.json` | Threading structure — organic families + 5 scripted story threads. |
| `batches.json` | Batch assignments — reviewer, status, doc list, dates. |
| `pi-ground-truth.csv` | One row per seeded PI instance, with the literal value and whether it is expected to be detected (Rule 16). |
| `language-mix.json` | The second-language slice: requested share, achieved share, and why it is irrelevant to the matter (Rule 17). |
| `findings.json` | Known-answer findings and the decoy, each with what it is findable by and what it is invisible to (Rule 18). |
| `entities.json` | The external entity population: each entity's organisation, kind and document count, the alias addresses, and the singleton tail (Rule 20). |
| `entities.json` | The external entity population: each entity's organisation, kind and document count, the alias addresses, and the singleton tail (Rule 20). |
| `edge-cases.json` | Only with `--edge-cases`: the documents starved of an input (Rule 13). |

---

## Quick start

### Pull into any project

```bash
# small — already in git, instant
dvc get https://github.com/nickmanoogian/oida-registry mock-data/small/documents.csv

# medium
dvc get https://github.com/nickmanoogian/oida-registry mock-data/medium/documents.csv

# large (compressed)
dvc get https://github.com/nickmanoogian/oida-registry mock-data/large/documents.csv.gz
gunzip documents.csv.gz
```

### Or use the Makefile

```bash
make mock-small        # pull small tier
make mock-medium       # pull medium tier
make mock-large        # pull large tier (compressed)
make mock-xlarge      # pull extra large tier (compressed)
```

### Validate after pulling

```bash
python scripts/validate_mock_data.py --tier small
```

---

## Key fields

### Workflow fields

| Field | Values | Notes |
|-------|--------|-------|
| `Workflow Stage` | `Pre-Review: Duplicate/NIST` `Pre-Review: Processing Error` `ECA: Excluded` `Review: Reviewed` `Review: In Progress` `Review: Queued` | Primary filter for the document universe |
| `Responsiveness` | `Responsive` `Non-Responsive` `Not Sure` | Only on reviewed docs |
| `Privilege` | `Privileged` *(blank)* | Only on responsive docs |
| `Hot Doc` | `Yes` `No` | ~1–2% of responsive docs |
| `TAR Score` | 0.00–100.00 | Bimodal: peaks at 0–20 and 75–100 |
| `AL Predicted Relevant` | `Yes` `No` | Score ≥ 50 = Yes |
| `Bates Begin` / `Bates End` | `MNK00000001` `INSYS00000001` `MCK00000001` | Org-specific prefix; only on produced docs |
| `Redacted` | `Yes` `No` | ~7–10% of produced docs |
| `Duplicate Spare` | `Yes` `No` | Marks deduped-out docs |
| `Processing Error Type` | `Password Protected` `Corrupt File` etc. | Only on error docs |
| `ECA Exclusion Reason` | `Date Out of Range` `No Keyword Hits` etc. | Only on ECA-excluded docs |
| `PI Seeded` | `SSN; Date of Birth` etc. | The PI types on this document (Rule 16); blank on the rest |

### Narrative fields (new in v1.3.0)

| Field | Values | Notes |
|-------|--------|-------|
| `Custodian Org` | `Mallinckrodt` `Insys` `McKinsey` `Outside Counsel` | Which defendant organization |
| `Narrative Phase` | `1` `2` `3` `4` | Story act (see below) |
| `Narrative Phase Name` | `Growth` `Pressure` `Crisis` `Litigation` | Human-readable phase label |
| `Bates Prefix` | `MNK` `INSYS` `MCK` `OC` | Org-specific Bates prefix |
| `Issue Tags` | `SOM Override` `Speaker Bureau Payments` `DEA Correspondence` `Prior Auth Fraud` `McKinsey Strategy` `Legal Hold` `Whistleblower` `State AG Investigation` | Populated on responsive docs |

### Finding the story documents

```python
import pandas as pd
docs = pd.read_csv("documents.csv")

# The 13 scripted hot documents (the key evidentiary moments)
hot = docs[docs["Control Number"].str.startswith("HOT-")]

# The 5 scripted email threads (the decision chains)
threads = docs[docs["Email Thread ID"].str.startswith("STHR-", na=False)]

# Filter by narrative phase
crisis = docs[docs["Narrative Phase Name"] == "Crisis"]

# Filter by defendant org
insys = docs[docs["Custodian Org"] == "Insys"]

# SOM override cluster
som = docs[docs["Issue Tags"].str.contains("SOM Override", na=False)]

# All privileged documents in the litigation phase
priv_lit = docs[(docs["Privilege"] == "Privileged") & (docs["Narrative Phase"] == 4)]
```

---

## The four phases

| Phase | Years | Character | Responsive rate |
|-------|-------|-----------|----------------|
| **Growth** | 2010–2012 | Routine sales, McKinsey engagement, speaker bureau launch | ~12% |
| **Pressure** | 2013–2014 | SOM overrides, DEA inquiries, speaker payment approvals, IRC call scripts | ~40% |
| **Crisis** | 2015–2016 | Legal holds, whistleblower, SOM deletion, AG subpoenas | ~55% |
| **Litigation** | 2017–2018 | MDL discovery, settlement negotiations, privilege logs | ~35% |

---

## Loading into Relativity (Mode B — native files)

To produce actual native files and a Relativity `.dat` load file ready for workspace import:

```bash
# install native file dependencies (one-time)
pip install python-docx openpyxl python-pptx fpdf2

# build with real OIDA OCR content
make load-small

# or synthetic content only (no network, faster)
python scripts/build_load_package.py --tier small --no-oida
```

Output in `load-packages/small/`:

| File | Description |
|------|-------------|
| `natives/` | ~1,400 actual `.eml`, `.docx`, `.xlsx`, `.pptx`, `.pdf`, `.rsmf` files, each stamped with its manifest date (Rule 19) |
| `load-file.dat` | Relativity Concordance load file — 58 fields, all metadata |
| `custodian-sources.csv` | One row per custodian: the processing data source setup sheet |
| `pi-ground-truth.csv`, `language-mix.json`, `findings.json` | Carried across from the tier, so the seeded content can be scored |
| `IMPORT_README.txt` | Step-by-step Relativity import instructions |

The 13 scripted HOT- documents get hand-crafted MDL 2804 content. All other documents use real OIDA OCR text from the S3 archive.

---

## Regenerating

```bash
# default seed (42) — always produces the same dataset
python scripts/generate_mock_metadata.py --tier small

# different seed — different but equally valid dataset
python scripts/generate_mock_metadata.py --tier medium --seed 99

# then validate
python scripts/validate_mock_data.py --tier small
```

Output is deterministic per seed.

### Tuning what gets seeded

```bash
# a standard-format SSN area, for detectors that score the never-issued 9xx block low
python scripts/generate_mock_metadata.py --tier small --ssn-range 666

# a second-language slice under 1%
python scripts/generate_mock_metadata.py --tier small --second-language-share 0.008

# back to the v1.12.0 shape: no PI, one language, no findings, 15 addresses
python scripts/generate_mock_metadata.py --tier small --no-pi --no-language-mix --no-findings --no-entities
```

With all three off the output is byte-identical to v1.12.0, so a tier used as clean fixture
data stays clean fixture data.
