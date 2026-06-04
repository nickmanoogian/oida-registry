# Mock Data — Relativity Workspace Datasets

Pre-generated Relativity workspace metadata at three litigation scales.
Each tier is built to mirror a realistic matter — correct workflow stage
distributions, custodian volumes, TAR score shapes, privilege rates, and
Bates structures. Content is drawn from Opioid Industry Documents Archive
patterns (real pharmaceutical/litigation subject matter).

---

## Tiers at a glance

| | Small | Medium | Large |
|---|---|---|---|
| **Documents** | 1,500 | 10,000 | 150,000 |
| **Custodians** | 4 | 10 | 40 |
| **File types** | 8 | 8 | 9 |
| **Sent to review** | ~765 | ~5,500 | ~65,000 |
| **Responsive** | ~183 | ~1,000 | ~15,000 |
| **Privileged** | ~21 | ~120 | ~2,000 |
| **Produced** | ~162 | ~800 | ~12,500 |
| **Email families** | ~370 | ~1,400 | ~25,000 |
| **Batches** | 3 | 12 | 90+ |
| **In git** | ✅ | via DVC | via DVC |

---

## Files per tier

Each tier produces four files:

| File | Description |
|------|-------------|
| `documents.csv` | One row per document. Every Relativity field populated. |
| `custodians.json` | Custodian profiles — name, role, email, hold status, doc count. |
| `email-families.json` | Parent/child threading structure for all email documents. |
| `batches.json` | Batch assignments — reviewer, status, doc list, dates. |

---

## Quick start

### In any project — pull a tier with DVC

```bash
# small tier (in git — no download needed after clone)
dvc get https://github.com/nickmanoogian/oioda-registry mock-data/small/documents.csv

# medium tier (release artifact)
dvc get https://github.com/nickmanoogian/oioda-registry mock-data/medium/documents.csv

# large tier (release artifact, compressed)
dvc get https://github.com/nickmanoogian/oioda-registry mock-data/large/documents.csv.gz
```

### Load in Python

```python
import pandas as pd, json

# documents
docs = pd.read_csv("documents.csv")

# filter by workflow stage
review_pop = docs[docs["Workflow Stage"].str.startswith("Review")]
responsive = docs[docs["Responsiveness"] == "Responsive"]
privileged = docs[docs["Privilege"] == "Privileged"]
produced   = docs[docs["Bates Begin"] != ""]

# filter by file type
emails = docs[docs["File Type Category"] == "Email"]
rsmf   = docs[docs["File Type Category"].str.contains("RSMF")]

# TAR score distribution
import matplotlib.pyplot as plt
review_pop["TAR Score"].hist(bins=20)

# custodians
with open("custodians.json") as f:
    custodians = json.load(f)

# email families
with open("email-families.json") as f:
    families = json.load(f)
```

### Key fields reference

| Field | Values | Notes |
|-------|--------|-------|
| `Workflow Stage` | `Pre-Review: Duplicate/NIST`, `Pre-Review: Processing Error`, `ECA: Excluded`, `Review: Reviewed`, `Review: In Progress`, `Review: Queued` | Use to filter the document universe |
| `Responsiveness` | `Responsive`, `Non-Responsive`, `Not Sure` | Only populated for reviewed docs |
| `Privilege` | `Privileged`, *(blank)* | Only populated for responsive docs |
| `TAR Score` | 0.00–100.00 | Bimodal: high at 0–20 and 75–100 |
| `AL Predicted Relevant` | `Yes`, `No` | Score ≥ 50 = Yes |
| `Bates Begin` / `Bates End` | `MNK00000001` | Only populated for produced docs |
| `Redacted` | `Yes`, `No` | ~7–10% of produced docs |
| `Hot Doc` | `Yes`, `No` | ~1–2% of responsive docs |
| `Duplicate Spare` | `Yes`, `No` | Marks deduped-out docs |
| `Processing Error Type` | `Password Protected`, `Corrupt File`, etc. | Only on error docs |
| `ECA Exclusion Reason` | `Date Out of Range`, `No Keyword Hits`, etc. | Only on ECA-excluded docs |

---

## Regenerating

```bash
python scripts/generate_mock_metadata.py --tier small
python scripts/generate_mock_metadata.py --tier medium
python scripts/generate_mock_metadata.py --tier large

# custom seed for a different but reproducible dataset
python scripts/generate_mock_metadata.py --tier medium --seed 99
```

Output is deterministic per seed — the same seed always produces the same dataset.
