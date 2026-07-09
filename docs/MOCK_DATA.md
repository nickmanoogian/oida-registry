# OIODA Mock Data — Canonical Reference

This is the single source of truth for the mock and real data published by the
`nickmanoogian/oioda-registry` repository. It describes what the registry is, the
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

| | Small | Medium | Large |
|---|---|---|---|
| **Documents** | ~1,439 | ~9,900 | ~148,000 |
| **Custodians** | 4 (all Mallinckrodt) | 10 (7 MNK + 2 Insys + 1 McKinsey) | 40 (across all orgs + outside counsel) |
| **Orgs represented** | 1 | 3 | 4 |
| **Phases present** | 2–3 | 1–4 | 1–4 |
| **Scripted hot docs** | 8 | 11 | 13 |
| **Scripted email threads** | 2 | 5 | 5 |
| **Sent to review** | ~470 | ~3,600 | ~36,000 |
| **Responsive** | ~228 | ~1,400 | ~13,000 |
| **Privileged** | ~33 | ~160 | ~1,700 |
| **Storage** | committed to git | DVC release artifact | DVC release artifact (gzipped) |
| **Best for** | quick tests, CI fixtures, component dev | feature dev, analytics, full workflow | scale/performance testing, TAR |

Each tier contains four files:

| File | Description |
|------|-------------|
| `documents.csv` | One row per document; 109 columns — every Relativity field plus the narrative fields |
| `custodians.json` | Custodian profiles: name, email, org, role, dept, narrative, hold status, doc counts |
| `email-families.json` | Threading structure — organic parent/child families plus the scripted story threads |
| `batches.json` | Batch assignments — reviewer, status, doc list, dates |

**Pull the small tier (already in git, instant):**

```bash
dvc get https://github.com/nickmanoogian/oioda-registry mock-data/small/documents.csv
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

### 3.2 Real OIDA data-products and raw archive

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

### 3.3 ECI real-data export (real processing fields)

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
make export-insys                      # -> /tmp/oioda-large/{documents.csv.gz, custodians.json}
```

Output: an ~1.63M-row `documents.csv.gz` (~163 MB) plus `custodians.json`. The
1.6M rows are aggregated downstream for the ECI dashboard; they are **not** loaded
in-browser.

---

## 4. Key custodians

The mock custodian roster grows with the tier. The **small** tier is four
Mallinckrodt custodians; **medium** adds Insys and McKinsey; **large** fills out
40 custodians across all four orgs. The people who carry the narrative:

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
Acknowledged, at least one is Outstanding (e.g. Lisa Torres in small; Tevelow in
medium/large), and the large tier includes an Escalated hold and several never
acknowledged. In the small tier the four custodians are Michael Brennan (VP Sales
& Marketing, key), Sarah Chen (Regional Sales Director), Thomas Bradley (CCO), and
Lisa Torres (Executive Assistant, hold Outstanding).

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
files plus a Relativity Concordance `.dat` load file, ready for workspace import):

```bash
pip install python-docx openpyxl python-pptx fpdf2
make load-small                # real OIDA OCR content
make load-small-synthetic      # synthetic content only, no network
# pre-built package: dvc get https://github.com/nickmanoogian/oioda-registry load-packages/small.zip
```

The scripted HOT- documents get hand-crafted MDL 2804 content; all other documents
use real OIDA OCR text pulled from S3 (or synthetic with `--no-oida`).

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
| `mock-data/RULES.md` | The 10 rules that define a realistic Relativity dataset |
| `mock-data/DEMO_GUIDE.md` | Narrative walkthrough for demos |
| `mock-data/{small,medium,large}/` | The three synthetic tiers (small in git; others via DVC) |
| `data-products/` | Real OIDA structured datasets (`.dvc` pointers) + `SCHEMA.md` |
| `metadata/`, `samples/`, `manifest.tsv.gz.dvc` | Real archive index, sample, and full manifest |
| `load-packages/` | Pre-built Relativity load package (`small.zip`) |
| `scripts/` | Generator, validator, exporter, downloader, manifest and URL tools |
| `.github/workflows/` | `health-check.yml` (weekly S3 URL check), `validate.yml` (per-PR rules + determinism) |
| `CHANGELOG.md` | Version history (current: v1.6.0) |

Current release: **v1.6.0** (2026-06-26). See [`../CHANGELOG.md`](../CHANGELOG.md)
for the full history.

---

## 9. Constraints

- The repo is **public** — never add anything sensitive.
- The data is real public litigation data or synthetic; nothing is re-hosted here.
- This doc is maintained in-repo; the Confluence "Einstein" copy is a manual paste
  because Confluence is read-only to the maintenance tooling.
