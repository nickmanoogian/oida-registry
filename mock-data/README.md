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

---

## Tiers at a glance

| | Small | Medium | Large |
|---|---|---|---|
| **Documents** | ~1,430 | ~9,900 | ~148,000 |
| **Custodians** | 4 (all Mallinckrodt) | 10 (7 MNK + 2 Insys + 1 McKinsey) | 40 (across all orgs) |
| **Orgs** | 1 | 3 | 4 (+ outside counsel) |
| **Phases** | 2–3 | 1–4 | 1–4 |
| **Scripted hot docs** | 8 | 11 | 13 |
| **Scripted threads** | 2 | 5 | 5 |
| **Sent to review** | ~470 | ~3,600 | ~36,000 |
| **Responsive** | ~228 | ~1,400 | ~13,000 |
| **Privileged** | ~33 | ~160 | ~1,700 |
| **In git** | ✅ | via DVC | via DVC |

---

## Files per tier

| File | Description |
|------|-------------|
| `documents.csv` | One row per document. Every Relativity field + narrative fields. |
| `custodians.json` | Custodian profiles — name, org, role, narrative description, hold status. |
| `email-families.json` | Threading structure — organic families + 5 scripted story threads. |
| `batches.json` | Batch assignments — reviewer, status, doc list, dates. |

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
make mock-small    # pull small tier
make mock-medium   # pull medium tier
make mock-large    # pull large tier (compressed)
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
| `natives/` | ~1,400 actual `.eml`, `.docx`, `.xlsx`, `.pptx`, `.pdf`, `.rsmf` files |
| `load-file.dat` | Relativity Concordance load file — 53 fields, all metadata |
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
