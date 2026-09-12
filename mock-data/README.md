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
| **Data sources** | 8 | 10 | 10 | 10 |
| **Sent to review** | 724 | 4,002 | 56,344 | 104,618 |
| **Responsive** | 213 | 1,089 | 14,434 | 26,653 |
| **Privileged** | 30 | 146 | 1,991 | 3,654 |
| **`documents.csv`** | 1.4 MB | 9 MB | 130 MB | 260 MB |
| **Where it lives** | in git | v1.16.0 release, via DVC | v1.16.0 release, via DVC | v1.16.0 release, via DVC |

---

## What each widget can be tested against

Volume is not what people ask for. They ask whether a dataset can exercise the thing they
are building, so this is the table to read first. Measured on the **small** tier.

| Widget | What the tier gives it | Gaps |
|---|---|---|
| **Key Relationships** | 10 custodians, 45 internal pairs, an 8.5x volume spread (323 documents down to 38), **44 non-custodian entities** past the production cap of 25, **28 of them on a single document**, and **2 people reachable at two addresses** for name normalisation (Rule 20). **304 of the 806 emails arrive rather than depart, and 188 carry more than one To recipient** (Rule 24), so the graph has direction in it and the semicolon path in the To column is exercised. Plus Rule 18's principal, its decoy, and a **planted negative**: a pair corresponding at volume about one subject that touches no matter issue and appears nowhere else, so a correct "nothing here" can be told from a broken analysis | **Direction is capped below what a real collection looks like.** Real mailboxes run heavily inbound; this tier stops near 40% because the custodians are the narrative's authors, and pushing past half stops the planted story being told by the people it is about. Three emails are still addressed to their own sender, each on a document Rule 18 or Rule 20 protects. **And Rule 24 does not change what this widget shows, by construction.** Measured over the medium tier before and after: documents analysed stayed at 4,908, the custodian count at 10, the external count at the production cap of 25, and every custodian's top-partner list was identical. Only the per-entity document counts rose, because a custodian now appears as a recipient on more documents. That follows from the design: direction is a pair-preserving swap, so the pairs a relationship graph draws are the same pairs, and the extra To recipients come from the custodian roster, which reinforces custodian-to-custodian co-occurrence rather than widening it. **The lever that would move this widget is putting external entities into the To and CC positions**, and Rule 24 deliberately does not pull it, because an external there moves a Rule 20 singleton off the singleton tail that `entities.json` asserts |
| **Collection Coverage** | 48 months of dates, **8 data sources with measurably different metadata profiles** (Rule 21) across 66 source-and-custodian folders, and a **planted gap and spike** (Rule 22): the top custodian has zero documents across three months that hold 28, 32 and 26 for everybody else against a median of 28, and one month carries 3.9x the median. Every native stamped from the manifest (Rule 19) | — |
| **File Types** | 25 distinct file type categories, containers with real children (Rule 3), chat and mobile RSMF, audio and video flagged unviewable, legacy formats, and unsupported types that land in error (Rule 6). The load file carries the category in `File Type` and the extension in `File Extension` | **This widget cannot be reached from a load file, and that is now settled rather than suspected.** It reads `Relativity Native Type`, which Relativity reserves: the field carries the System keyword, Import/Export does not offer it as a mapping target, and only processing writes it. Proved by running the analysis twice over the same 9,980 documents. In between, `File Type` was corrected from the extension to the 25 categories and `File Extension` was added, both verified present in the workspace. The widget reported `Unidentified` for all 9,980 both times. Populate the corpus however you like; only a processing job changes this number |
| **Document Categories** | Four narrative phases with distinct subject matter, 8 issue tag clusters, a second-language population on an unrelated topic, one document dense with PI and irrelevant to the matter, and **24 documents that belong to two categories at once** (Rule 22) | — |
| **PI Detect** | 102 instances across 18 documents (Rule 16), spread over email bodies, spreadsheet cells, a PDF form and a chat, all non-issuable values, with `pi-ground-truth.csv` to diff against. **All 102 are reachable from the extracted text layer (Rule 23), so a load file with no natives still feeds this widget** | **`pi-ground-truth.csv` scores recall, never precision.** The real OIDA text carries its own personal information, so a detector finds far more than was seeded: on the medium tier it flagged 3,839 of 9,096 documents against 443 seeded instances. Those are not false positives. Diffing a detector's total against this file will look like a catastrophic precision problem and will be measuring the wrong thing |
| **Primary Language Composition** | German at 2.0% on unrelated facilities notices (Rule 17), real prose in the natives, **written with its own diacritics and planted only into file types whose native carries a body**, tunable with `--second-language-share` | Only one second language in the small tier. Medium adds Polish, large and extra large add Spanish. **Expect languages nobody planted**: the real OIDA text brings its own, and a run over medium returned Chinese and an Other bucket alongside the seeded German and Polish. Documents with no extracted text land in "unable to identify", which on medium was exactly the 868 that have none |

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
| `mail-direction.json` | Which way the email edges point: how many arrive, how many carry more than one recipient, and how many documents were left alone because another rule owns them (Rule 24). |
| `data-sources.json` | Each data source: what it collects, its folder, its document and custodian counts, its file types, and the metadata profile measured from the data (Rule 21). |

**A note on what a load file can and cannot feed.** Three of the six widgets read metadata and
are satisfied by the `.dat` alone: Collection Coverage (custodian plus `Sent Date/Time`, falling
back to created date), Key Relationships (the participant fields) and File Types (`File Type`).
Two read **extracted text** through an LLM pass, Document Categories and PI Detect, so they need
Rule 23's `text/` sidecars, which a package carries at about 1 KB a document. One,
**Primary Language Composition**, comes from Relativity's own Language Identification during
processing, so it needs the natives; the `Language` column is there for a metadata-only import
to read, but it is our value rather than Relativity's.

| `collection-shape.json` | The planted date gap and spike, and the population that belongs to two categories, each with what to expect and how to verify it (Rule 22). |
| `entities.json` | The external entity population: each entity's organisation, kind and document count, the alias addresses, and the singleton tail (Rule 20). |
| `mail-direction.json` | Which way the email edges point: how many arrive, how many carry more than one recipient, and how many documents were left alone because another rule owns them (Rule 24). |
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
