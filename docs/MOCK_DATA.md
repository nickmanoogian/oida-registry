# OIDA Mock Data — Canonical Reference

This is the single source of truth for the mock and real data published by the
`nickmanoogian/oida-registry` repository. It describes what the registry is, the
litigation narrative the data is built around, every data tier and its contents,
the key custodians, how the data feeds the ECI (Early Case Intelligence) demo, and
how to regenerate everything from scratch.

> **Where this lives.** The canonical copy is maintained in the repo at
> `docs/MOCK_DATA.md`. A cleaned-up copy is also published to the Relativity
> "Einstein" Confluence space (space key `einstein`). Confluence is read-only to
> the tooling that maintains this file, so the repo copy is authoritative and the
> Confluence page is a manual paste of it.

---

## 1. What the registry is

The registry is a **DVC data registry**: a git repo that holds pointers, tools,
and documentation rather than the data itself. Think of it as a card catalog, not
a library shelf. The actual bytes live in a public Amazon S3 bucket
(`s3://opioid-industry-documents-archive-dataset-bucket`, no credentials needed);
this repo holds `.dvc` pointer files plus scripts so anyone can reproducibly pull
exactly the files they need.

The repo publishes three distinct bodies of data:

| Body | What it is | Real or synthetic | Where |
|------|-----------|-------------------|-------|
| **OIDA data-products & archive** | The real Opioid Industry Documents Archive — prescriber CSVs, order records, full document collections, and a 22.3M-file raw archive | **Real** public litigation data | `data-products/`, `metadata/`, `samples/`, `manifest.tsv.gz` |
| **Relativity mock-data tiers** | Synthetic Relativity workspace metadata (small/medium/large) built around a scripted MDL 2804 narrative | **Synthetic** (generated, deterministic per seed) | `mock-data/` |
| **ECI real-data export** | The full real Insys document set exported from the OIDA index with real Relativity *processing* fields only | **Real** (no cap, no sampling, no synthetic values) | produced by `scripts/export_insys_documents.py` |

The mock-data tiers and the ECI real-data export are the two things the ECI demo
consumes. The rest is the underlying real archive they are derived from or modelled on.

---

## 2. The MDL 2804 litigation narrative

The synthetic mock-data tiers are built around **MDL 2804, the National
Prescription Opiate Litigation** — the real federal multi-district litigation
consolidating thousands of cases against opioid manufacturers, distributors, and
consultants. The mock workspace represents a single law firm's review of documents
produced across the defendants into that MDL.

Three defendant organizations (plus outside counsel) are represented:

| Org | Company name in data | Bates prefix | Role in the case |
|-----|---------------------|--------------|------------------|
| **Mallinckrodt** | Mallinckrodt Inc. | `MNK` | Manufactured generic oxycodone; failed to report suspicious orders (SOM) to the DEA |
| **Insys** | Insys Therapeutics | `INSYS` | Bribed doctors through a fraudulent speaker bureau and defrauded insurers; CEO convicted under RICO |
| **McKinsey** | McKinsey & Company | `MCK` | Consulted on opioid sales-maximization strategy; settled for $600M |
| **Outside Counsel** | Kirkland & Ellis LLP | `OC` | Defense litigation, DEA response, AG subpoenas, settlement |

The narrative runs across four phases:

| Phase | Years | Character | Responsive rate | Privilege rate |
|-------|-------|-----------|-----------------|----------------|
| **1 — Growth** | 2010–2012 | Routine sales, McKinsey engagement, speaker-bureau launch | ~12% | ~2% |
| **2 — Pressure** | 2013–2014 | SOM overrides, DEA inquiries, speaker-payment approvals, IRC call scripts | ~40% | ~8% |
| **3 — Crisis** | 2015–2016 | Legal holds, whistleblower, SOM deletion, AG subpoenas | ~55% | ~15% |
| **4 — Litigation** | 2017–2018 | MDL discovery, settlement, privilege logs, clawbacks | ~35% | ~25% |

Issue-tag clustering follows the same story: `SOM Override`, `Speaker Bureau
Payments`, `DEA Correspondence`, `Prior Auth Fraud`, `McKinsey Strategy`, `Legal
Hold`, `Whistleblower`, `State AG Investigation`.

> **A note on naming.** Earlier drafts of this program used placeholder company
> names; the current generator uses the **real MDL 2804 defendant names**
> throughout (Mallinckrodt, Insys, McKinsey). The ECI real-data export is scoped
> to the real OIDA collection `Insys Litigation Documents`. There is no
> "BigThorium"-style codename anywhere in the current repo, and no separate roster
> of "uncollected external" custodians — non-custodial parties surface only as the
> real `Mentioned` field in the ECI export (people named in documents who are not
> themselves custodians).

---

## 3. Data tiers

### 3.1 Synthetic Relativity mock-data tiers

Three scales of pre-generated Relativity workspace metadata. These are **not** raw
OIDA files — they are structured CSV/JSON with every Relativity field populated
(custodians, file types, workflow stages, batches, TAR scores, Bates numbers,
privilege, email threading, and the narrative fields above). Built to mirror a real
matter, deterministic per random seed (default `42`).

| | Small | Medium | Large | Extra large |
|---|---|---|---|---|
| **Documents** | 1,439 | 9,980 | 148,235 | 275,273 |
| **Custodians** | 10 (8 MNK + 1 Insys + 1 McKinsey) | 10 (7 MNK + 2 Insys + 1 McKinsey) | 40 (36 MNK + 2 Insys + 1 McKinsey + 1 outside counsel) | 40, the same roster as large |
| **Orgs represented** | 3 | 3 | 4 | 4 |
| **Phases present** | 2–3 | 1–4 | 1–4 | 1–4 |
| **Scripted hot docs** | 8 | 11 | 13 | 13 |
| **Scripted email threads** | 2 | 5 | 5 | 5 |
| **Sent to review** | 724 | 4,002 | 56,344 | 104,618 |
| **Responsive** | 213 | 1,089 | 14,434 | 26,653 |
| **Privileged** | 30 | 146 | 1,991 | 3,654 |
| **Storage** | committed to git | DVC release artifact | DVC release artifact (gzipped) | DVC release artifact (gzipped) |
| **Best for** | quick tests, CI fixtures, component dev | feature dev, analytics, full workflow | scale/performance testing, TAR | scale past a quarter of a million documents |

Every document also carries a **`Record Type`** (`Email` / `EDoc` / `Container` / `Attachment`,
Rule 14) and **attachments are re-parented real documents, not invented rows** (Rule 15): the
small tier has 306 attachments across 131 emails. **Edge cases** (Rule 13, off by default,
`--edge-cases`) starve twelve scenarios — no custodian, no date, sentinel dates, no text,
non-English, broken families, orphan attachments, duplicate MD5, and more — so a feature that
aggregates over a collection is tested against incomplete input, not just complete rows.

Each tier contains eight files, and `make mock-medium` / `mock-large` / `mock-xlarge` pull all eight:

| File | Description |
|------|-------------|
| `documents.csv` | One row per document; 111 columns — every Relativity field plus the narrative fields and `PI Seeded` |
| `custodians.json` | Custodian profiles: name, email, org, role, dept, narrative, hold status, doc counts |
| `email-families.json` | Threading structure — organic parent/child families plus the scripted story threads |
| `batches.json` | Batch assignments — reviewer, status, doc list, dates |
| `pi-ground-truth.csv` | One row per seeded PI instance, with the value and whether it is expected to be detected (Rule 16) |
| `language-mix.json` | The second-language slice and why it is irrelevant to the matter (Rule 17) |
| `findings.json` | Known-answer findings and the decoy (Rule 18) |
| `entities.json` | The external entity population, alias addresses and singleton tail (Rule 20) |

`docs/REQUEST_TEMPLATE.md` is the intake form for a corpus request, with a map from each
common ask to the flag that serves it and an honest list of what is not modelled yet.

`mock-data/README.md` opens with a table of what each of the six Early Insights widgets can
be tested against, and where the tiers still fall short. Read that before picking a tier:
volume is rarely the thing that decides it.

**Pull the small tier (already in git, instant):**

```bash
dvc get https://github.com/nickmanoogian/oida-registry mock-data/small/documents.csv
# or, via Makefile
make mock-small
```

**Medium / large:**

```bash
make mock-medium
make mock-large          # documents.csv.gz + email-families.json.gz are compressed
```

**Validate a tier against the rules:**

```bash
python scripts/validate_mock_data.py --tier small
```

The full specification behind the distributions (file-type mix, workflow behaviour
by file type, container records, dedup methods, processing-error spread, bimodal
TAR scores, custodian rules, threading, production rules) lives in
[`../mock-data/RULES.md`](../mock-data/RULES.md). A demo walkthrough of the
narrative lives in [`../mock-data/DEMO_GUIDE.md`](../mock-data/DEMO_GUIDE.md).

### 3.2 Real-data load package (`small-real`)

A second native-file load package alongside the synthetic ones in §3.1, built entirely
from real archive content rather than the MDL 2804 narrative.
`scripts/build_real_load_package.py` reads the OIDA index parquet directly
(`collection = 'Insys Litigation Documents'`) and emits a small, fully real,
ready-to-import package at `load-packages/small-real/`. Default 60 documents.

**Every value is real.** No synthetic fields, no review decisions, no invented people,
which is the same principle `export_insys_documents.py` applies at full scale (§3.4). The
load file is 23 fields and deliberately carries no `Responsive`, `Privileged` or `TAR
Score`: those are created during review inside Relativity and do not exist in a produced
archive.

| File | What it is |
|------|-----------|
| `natives/{id}.pdf` | 60 real produced PDFs, 26 KB to 378 KB each, 8.5 MB in total. Kept small on purpose so the package stays committable |
| `text/{id}.txt` | The real OCR extracted text for the same 60 documents |
| `load-file.dat` | Concordance load file, 23 fields: Control Number, real Bates (present on all 60), Bates Alias, Custodian, file metadata, MD5, email fields, dates, page count, Redacted, `Collection`, and a `Source URL` back to industrydocuments.ucsf.edu |
| `IMPORT_README.txt` | Step-by-step Relativity import instructions |

The 60 documents span **19 real custodians**, so even at this size the package has a
custodian distribution rather than a single name.

```bash
pip install -r requirements.txt        # duckdb
python scripts/build_real_load_package.py --count 60
```

**This one is tracked in git rather than published**, unlike every other package. It is
real archive content, not generated output, so no `make` target reproduces it and no seed
recreates it: delete it and it is gone until someone re-queries the index. That is why
`load-packages/small-real/` is the one path under `load-packages/` that `.gitignore` does
not exclude.

Use it when the question is whether something works against genuine produced documents,
with real OCR text, real Bates numbers and a real citation back to the public archive.
Use §3.1 when you need review fields, a narrative, or a particular failure mode.

### 3.3 Real OIDA data-products and raw archive

The real, analysis-ready datasets and the raw document archive that back the whole
project. Pulled the same way (`dvc get …` or a direct S3 URL).

| Item | Size | What it contains |
|------|------|-----------------|
| `data-products/prescribers.csv` | 29 MB | Master prescriber list — join key for every other dataset |
| `data-products/mnk_customer_orders.csv` | 38 MB | Mallinckrodt customer orders incl. suspicious-order flags |
| `data-products/*_bydates.csv` | 100 MB–1.8 GB | Weekly prescription counts by prescriber per drug (Duexis, Sumavel, Xartemis, Exalgo, Pennsaid) |
| `data-products/insys_authorized_rx.csv[.zip]` | 693 MB–4.6 GB | Insys prescription transaction records |
| `data-products/*_full_dedup.zip` | 2.7–61 GB | Full document collections (Insys, McKinsey, Mallinckrodt) |
| `metadata/oida-index.parquet` | 2.2 GB | Index of every document in the archive |
| `metadata/oida-index-by-artifact.parquet` | 2.6 GB | Same index grouped by artifact/exhibit |
| `samples/oida-bulk-download-sample.zip` | 2.4 MB | Small slice of the raw archive for format exploration |
| `manifest.tsv.gz` | 581 MB | Index of all **22,307,281** raw files (7.5 TB): `key`, `size`, `etag` |

Column definitions for the structured CSVs are in
[`../data-products/SCHEMA.md`](../data-products/SCHEMA.md).

### 3.4 ECI real-data export (real processing fields)

`scripts/export_insys_documents.py` reads `metadata/oida-index.parquet`
(`collection = 'Insys Litigation Documents'`) and emits **all 1,633,778 real
documents** with real Relativity *processing*-field metadata only — custodian,
email From/To/CC, dates, file type/size/MD5/media type, page count, redaction,
Bates, and `Mentioned` — plus a deterministic **`OCR Text URL`** per document so
the real extracted text can be fetched on demand instead of baking ~112 GB of OCR
into the file. `custodians.json` lists every real collected custodian (111) with
its real document count.

No cap, no sampling, no synthetic values — this is the opposite of the mock-data
generator. Review/analytics fields (Responsiveness, Privilege, Issue Tags,
Batches, TAR/AL) are **intentionally omitted**: those are created during review
*inside* Relativity and do not exist in a raw produced archive.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt        # installs duckdb (no separate CLI)
make export-insys                      # -> /tmp/oida-large/{documents.csv.gz, custodians.json}
```

Output: an ~1.63M-row `documents.csv.gz` (~163 MB) plus `custodians.json`. The
1.6M rows are aggregated downstream for the ECI dashboard; they are **not** loaded
in-browser.

---

## 4. Key custodians

The mock custodian roster grows with the tier. The **small** tier has 10 custodians
(8 Mallinckrodt, 1 Insys, 1 McKinsey) with document counts weighted by `doc_target`
rather than flat — 323 documents down to 38; **large** fills out 40 custodians
across all four orgs, including outside counsel. The people who carry the narrative:

| Name | Org | Role | Role in the story |
|------|-----|------|-------------------|
| James Whitfield | Mallinckrodt | CEO | Ultimate SOM-override authority; McKinsey engagement sponsor |
| Mark Trevino | Mallinckrodt | Chief Commercial Officer | Commercial strategy; quota escalation (large tier) |
| Patricia Morrison | Mallinckrodt | VP, Marketing | Sales-maximization strategy; quota spreadsheet; McKinsey deck recipient |
| Robert Ashton | Mallinckrodt | VP, Sales | Approved the Cardinal Health SOM override |
| Diana Kowalski | Mallinckrodt | VP, Regulatory Affairs | DEA quota negotiations; forwarded the DEA letter (large tier) |
| Thomas Bradley | Mallinckrodt | Chief Compliance Officer | Internal objector; issued the legal hold; forwarded whistleblower tip |
| Sandra Nguyen | Mallinckrodt | Regional Sales Director | Sent the Cardinal Health anomaly alert that triggered the override chain |
| Gregory Nash | Mallinckrodt | Director, SOM Compliance | Wrote override justification memos; authored the SOM deletion log |
| Dr. Alec Harrington | Insys | VP, Sales | Speaker-bureau architect; prior-auth fraud overseer; RICO defendant |
| Natalie Rosen | Insys | Reimbursement Manager | Ran the IRC prior-auth fraud calls; call-guide author |
| Bradley Tevelow | McKinsey | Senior Engagement Manager | Delivered the "turbocharge" deck; hold Outstanding |
| Richard Galveston | Outside Counsel | Senior Litigation Partner | DEA response, AG subpoena, MDL settlement (large tier) |

**Hold status varies by design** (a key realism rule): most custodians have
Acknowledged, at least one is Outstanding (Lisa Torres and Bradley Tevelow, both
in the small tier), and the large tier includes an Escalated hold and several
never acknowledged. The full small-tier roster is Michael Brennan (VP Sales &
Marketing, key, 323 docs), Sarah Chen (Regional Sales Director, 243), Thomas
Bradley (CCO, 223), Gregory Nash (Director, SOM Compliance, 133), Robert Ashton
(VP Sales, 128), Patricia Morrison (VP Marketing, 117), James Whitfield (CEO,
94), Lisa Torres (Executive Assistant, 76, hold Outstanding), Dr. Alec Harrington
(Insys VP Sales, 64), and Bradley Tevelow (McKinsey, 38, hold Outstanding).

---

## 5. The scripted evidence

Filter `Control Number LIKE 'HOT-%'` for the 13 scripted hot documents (8 present
in small, 11 in medium, 13 in large) and `Email Thread ID LIKE 'STHR-%'` for the
scripted threads.

The anchor documents include the SOM override memo (`HOT-0000001`), the McKinsey
"turbocharge" deck (`HOT-0000002`), the DEA meeting forward (`HOT-0000003`), the
Insys IRC call guide (`HOT-0000005`), the whistleblower email (`HOT-0000006`,
privileged), the legal hold notice (`HOT-0000007`, issued 2015-09-14), and the SOM
deletion log (`HOT-0000008`, dated 2015-09-22 — eight days after the hold). The
five scripted threads (`STHR-0001`…`STHR-0005`) show the decision chains behind
these. Full detail is in [`../mock-data/DEMO_GUIDE.md`](../mock-data/DEMO_GUIDE.md).

---

## 6. How the data maps to the ECI demo

ECI (Early Case Intelligence) is a no-LLM, processing-fields-only orientation view
of a collection. Two datasets from this repo feed it:

- **The ECI real-data export (§3.3)** is what production ECI consumes. It is built
  strictly from real OIDA *processing* fields — the same fields ECI computes its
  insights from (custodian × time coverage, file-type mix, date ranges, sizes,
  languages derived from OCR). Because review/analytics fields are absent from a
  raw archive, ECI never depends on them, which is what makes the view defensible
  and demo-safe.
- **The synthetic mock-data tiers (§3.1)** provide a controllable, fully
  review-populated Relativity workspace for building and demoing UI that also
  needs Responsiveness, Privilege, Issue Tags, batches, and TAR — the fields the
  real export deliberately omits.

In short: the **real export** proves ECI's insights come only from processing
fields that genuinely exist pre-review, and the **mock tiers** give a rich,
end-to-end workspace for feature and demo work. The 1.6M-row real export is
aggregated server-side; only aggregates reach the browser.

---

## 7. How to regenerate

**Synthetic mock tiers** (deterministic per seed; default `42`):

```bash
python scripts/generate_mock_metadata.py --tier small
python scripts/generate_mock_metadata.py --tier medium --seed 99   # different but equally valid
python scripts/generate_mock_metadata.py --tier large --out ./my-test-data/
python scripts/validate_mock_data.py --tier small                  # verify against RULES.md
```

Two consecutive regenerations are byte-identical (RSMF participant ordering was
made deterministic in v1.6.0), and CI (`validate.yml`) regenerates the small tier
on every PR and fails if the output differs from the committed files.

**Native-file load package** (actual `.eml`/`.docx`/`.xlsx`/`.pptx`/`.pdf`/`.rsmf`
files plus a Relativity Concordance `.dat` load file, ready for workspace import).
Three variants ship, each testing a different failure surface:

| Package | Contents | Build |
|---|---|---|
| `small.zip` | Clean — everything imports and processes | `make load-small` |
| `small-errors.zip` | Fabricated processing failures **and** the twelve Rule 13 edge-case starves, plus `edge-cases.json` mapping every one | `make load-small-errors` |
| `load-broken` (local only, not published) | Seven variants that fail at **import**, not processing: missing native, duplicate control number, bad date, unqualified delimiter, bad encoding, short row, blank required field | `make load-broken` |

```bash
pip install python-docx openpyxl python-pptx fpdf2
make load-small                # real OIDA OCR content
make load-small-synthetic      # synthetic content only, no network
make load-release              # builds + validates + zips the release assets
# pre-built package: dvc get https://github.com/nickmanoogian/oida-registry load-packages/small.zip
```

The scripted HOT- documents get hand-crafted MDL 2804 content; all other documents
use real OIDA OCR text pulled from S3 (or synthetic with `--no-oida`). Every native
is stamped with the row's own `Date Created` / `Date Last Modified` (Rule 19), not
a library default, and encrypted artefacts use password `oida` (renamed from
`oioda` at the v1.9.1 → v1.10.0 boundary; each package documents its own password
in `IMPORT_README.txt`). `make check` (lint → typecheck → import cycles →
validators → scenario matrix → determinism) is the gate to run before a PR.

**ECI real-data export:** see §3.3 (`make export-insys`).

**Full archive manifest:**

```bash
python scripts/fetch_manifest.py           # full rebuild (~30 min)
python scripts/fetch_manifest.py --prefix f/ --out f_manifest.tsv.gz
```

---

## 8. Repository map

| Path | Contents |
|------|----------|
| `README.md` | Top-level usage for engineers and non-engineers |
| `docs/MOCK_DATA.md` | **This file** — canonical mock/real data reference |
| `mock-data/README.md` | Mock-tier usage and key fields |
| `mock-data/RULES.md` | The 19 rules that define a realistic Relativity dataset |
| `mock-data/DEMO_GUIDE.md` | Narrative walkthrough for demos |
| `mock-data/{small,medium,large}/` | The three synthetic tiers (small in git; others via DVC) |
| `data-products/` | Real OIDA structured datasets (`.dvc` pointers) + `SCHEMA.md` |
| `metadata/`, `samples/`, `manifest.tsv.gz.dvc` | Real archive index, sample, and full manifest |
| `load-packages/` | Pre-built Relativity load package (`small.zip`) |
| `scripts/` | Generator, validator, exporter, downloader, manifest and URL tools |
| `.github/workflows/` | `health-check.yml` (weekly S3 URL check), `validate.yml` (per-PR rules + determinism) |
| `CHANGELOG.md` | Version history (current: v1.14.0) |

Current release: **v1.14.0** (2026-09-09). Since v1.6.0, every tier gained
attachments and `Record Type` (Rule 15/14), PI/language/planted-findings ground
truth (Rules 16–18), a stamped native date layer (Rule 19), edge cases that starve
a feature on purpose (Rule 13), an extra large (275,273-doc) tier, and
import-failure load-file variants (`make load-broken`) — see
[`../CHANGELOG.md`](../CHANGELOG.md) for the full history.

---

## 9. Constraints

- The repo is **public** — never add anything sensitive.
- The data is real public litigation data or synthetic; nothing is re-hosted here.
- This doc is maintained in-repo; the Confluence "Einstein" copy is a manual paste
  because Confluence is read-only to the maintenance tooling.
