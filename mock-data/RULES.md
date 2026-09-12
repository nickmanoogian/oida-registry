# Mock Data Rules — Relativity Dataset Standards

This document defines the rules for what makes a realistic, useful Relativity mock dataset.
It is the authoritative reference for the generator script, for engineers building features,
and for Claude Code when helping with mock data or Relativity-related work.

---

## Core Principle

A good mock dataset mirrors a **mid-size commercial litigation or regulatory investigation**.
The three tiers are:

| Tier | Total docs | Use case |
|------|-----------|----------|
| **Small** | ~1,500 | Single-plaintiff employment, small contract, targeted investigation |
| **Medium** | ~10,000 | Commercial litigation, regulatory response, mid-size matter |
| **Large** | ~150,000 | Mass tort, antitrust, securities fraud, large regulatory matter |
| **Extra large** | ~275,000 | The same matter above a quarter of a million documents: scale and performance work past what the large tier reaches |

The sweet spot for most product development is **medium**. Large enough to make analytics,
TAR, batching, and production meaningful. Small enough to load and query without performance issues.

---

## Rule 1 — File Type Distributions

File type affects processing, imaging, OCR, deduplication, analytics eligibility, and production.
Use these exact counts per tier. Do not simplify to "email and docs" — the variety is the point.

### Small (~1,500 docs)

| File Type | Count | % | Notes |
|-----------|-------|---|-------|
| Email (MSG/EML) | 800 | 53% | Primary email format |
| PST/MBOX containers | 8 parents | — | Container records only, not leaf docs |
| ICS (calendar invites) | 15 | 1% | Blank Date Sent — tests date handling |
| Word (DOCX/DOC) | 200 | 13% | Mix of .docx and some .doc |
| Excel (XLSX/XLS) | 100 | 7% | Include a few .xls for extraction mode |
| PowerPoint (PPTX/PPT) | 50 | 3% | High responsiveness rate — mark some as Hot |
| PDF | 100 | 7% | 5–10% scanned (OCR required) |
| Teams (RSMF) | 20 | 1% | Include HasPlaceholders on 3–5 |
| Slack (RSMF) | 10 | 0.7% | Channel + DM records |
| Images (JPEG/PNG/TIFF/HEIC) | 50 | 3% | EXIF GPS on 10–20% of JPEG/HEIC |
| Text/RTF/HTML/CSV | 50 | 3% | Extracted text fallback, logs |
| Unsupported / error types | 15 | 1% | Access, iWork, corrupt, unknown |
| Audio/Video | 5 | — | Flagged Supported by Viewer = No |

### Medium (~10,000 docs)

| File Type | Count | % | Notes |
|-----------|-------|---|-------|
| Email (MSG/EML) | 5,200 | 52% | |
| PST/MBOX containers | 40 parents | — | |
| ICS (calendar invites) | 150 | 1.5% | |
| Word (DOCX/DOC) | 1,200 | 12% | |
| Excel (XLSX/XLS) | 700 | 7% | |
| PowerPoint (PPTX/PPT) | 350 | 3.5% | |
| PDF | 700 | 7% | |
| Teams (RSMF) | 300 | 3% | |
| Slack (RSMF) | 200 | 2% | |
| SMS/WhatsApp/Mobile (RSMF) | 100 | 1% | Cellebrite UFDR pipeline |
| Google Chat/Gemini (RSMF) | 50 | 0.5% | Rsmf/Application = "Google Chat" |
| Images | 400 | 4% | |
| Google Workspace Docs | 100 | 1% | GoogleDrive/ fields populated |
| Text/RTF/HTML/CSV | 250 | 2.5% | |
| Source code / technical | 50 | 0.5% | .py, .js, .sql, .yaml |
| Audio/Video | 30 | — | |
| Cellebrite structured Excel | 20 | — | Call logs, contacts from UFDR |
| Unsupported / error types | 100 | 1% | |
| Visio / Project / Access | 50 | 0.5% | |

### Large (~150,000 docs)

| File Type | Count | % | Notes |
|-----------|-------|---|-------|
| Email (MSG/EML) | 70,000 | 47% | |
| PST/MBOX containers | 400 parents | — | |
| ICS | 2,000 | 1.3% | |
| Word | 15,000 | 10% | |
| Excel | 10,000 | 7% | |
| PowerPoint | 5,000 | 3% | |
| PDF | 10,000 | 7% | |
| Teams (RSMF) | 9,000 | 6% | |
| Slack (RSMF) | 6,000 | 4% | |
| SMS/WhatsApp/Mobile (RSMF) | 2,500 | 1.7% | |
| Google Chat/Gemini (RSMF) | 1,500 | 1% | |
| Bloomberg/Financial XML | 1,000 | 0.7% | Essential for financial matters |
| Images | 6,000 | 4% | |
| Google Workspace Docs | 2,500 | 1.7% | |
| Text/RTF/HTML/CSV | 3,500 | 2.3% | |
| Source code / technical | 1,500 | 1% | |
| Audio/Video | 500 | — | |
| Cellebrite structured Excel | 300 | — | |
| Unsupported / error types | 1,500 | 1% | |
| Visio / Project / Access | 700 | 0.5% | |

### Extra large (~275,000 docs)

Large's composition at 1.86x, so the mix is the same matter at a larger collection
rather than a differently shaped one. Every share stays inside the band the validator
checks.

| File Type | Count | % | Notes |
|-----------|-------|---|-------|
| Email (MSG/EML) | 130,000 | 47.2% | |
| PST/MBOX containers | 745 parents | — | |
| ICS (calendar invites) | 3,700 | 1.3% | |
| Word (DOCX/DOC) | 27,850 | 10.1% | |
| Excel (XLSX/XLS) | 18,550 | 6.7% | |
| PowerPoint (PPTX/PPT) | 9,250 | 3.4% | |
| PDF | 18,028 | 6.5% | includes 3,150 scanned and 28 MIP protected |
| Teams (RSMF) | 16,700 | 6.1% | |
| Slack (RSMF) | 11,150 | 4.1% | |
| SMS/WhatsApp/Mobile (RSMF) | 4,100 | 1.5% | |
| Google Chat (RSMF) | 2,800 | 1.0% | |
| Bloomberg/Financial XML | 1,850 | 0.7% | |
| Images | 11,150 | 4.1% | |
| Google Workspace Docs | 4,650 | 1.7% | |
| Text/RTF/HTML/CSV | 6,500 | 2.4% | |
| Source code / technical | 2,800 | 1.0% | |
| Audio/Video | 950 | — | |
| Cellebrite structured Excel | 560 | 0.2% | |
| Unsupported / error types | 2,800 | 1.0% | |
| Visio / Project / Access | 750 | 0.3% | |
| ZIP containers | 370 | 0.1% | |

### A note on short message share

Short message is the one family whose share of a tier genuinely moves with the size of
the matter, because the tables above add channels as the tier grows: small has Teams and
Slack only, and large and extra large add SMS, WhatsApp and Google Chat on top. The
totals are roughly **2% for small, 6.5% for medium, and 12.7% for large and extra
large**. A single validator band across all four tiers contradicted the very tables it
was checking, and failed medium and large for years; the band is per tier now.

---

## Rule 2 — Workflow Behavior by File Type

Every document must have these five behavior flags set correctly based on its file type.
These directly affect what Relativity can do with the document at each stage.

| File Type | Images? | OCR Required? | Native Produced? | Redactable? | Analytics Eligible? | Dedup Method |
|-----------|---------|---------------|-----------------|-------------|-------------------|--------------|
| MSG/EML | Yes | Rarely | Yes | Image only | Yes | MD5 hash |
| PST/OST/MBOX | Container | No | No | No | No | N/A |
| ICS | Yes | No | Yes | Image only | Yes | SHA256 |
| DOCX/XLSX/PPTX | Yes | No | Yes | Image only | Yes | SHA256 |
| DOC/XLS/PPT (legacy) | Yes | No | Yes | Image only | Yes | SHA256 |
| PDF (text-based) | Yes | No | Yes | Image only | Yes | SHA256 |
| PDF (scanned) | Yes | **Yes** | Yes | Image only | After OCR | SHA256 |
| PDF (MIP-protected) | Limited | No | Limited | No | No | SHA256 |
| RSMF (Teams/Slack/SMS) | Yes | No | No | Image only | Yes | EventCollectionId |
| Bloomberg XML | Yes | No | Yes | Image only | Yes | SHA256 |
| HEIC/JPEG | Yes | **Yes** | Yes | Image only | After OCR | SHA256 |
| PNG/TIFF | Yes | **Yes** | Yes | Image only | After OCR | SHA256 |
| Audio/Video | No | No | Yes | No | No | SHA256 |
| Cellebrite Excel | Yes | No | Yes | Image only | Yes | SHA256 |
| Unsupported | No | No | Native only | No | No | SHA256 |
| Visio/Project | Yes (partial) | No | Yes | Image only | No | SHA256 |

---

## Rule 3 — Container Records

PST, OST, MBOX, ZIP, RAR, and AD1 files are **containers**, not leaf documents.
They must appear as parent records only, never as reviewable documents.

Rules for container records:
- `File Type Category` = the container type (e.g. "PST", "ZIP")
- `Level` = 0 (the container itself is level 0)
- Children have `Level` = 1, `Container Name` and `Container ID` populated
- **Every container has at least one child, and every `Container ID` resolves to a container
  record that exists.** A container nothing points at is not a container. Children come from the
  same custodian as their container, 3–8 per container
- `Has Natives` = No for PST/MBOX containers themselves
- Password-protected containers get `Processing Status` = "Error", `Processing Error Type` = "Password Protected"
- ZIP children have unreliable date fields — `Date Created`/`Date Modified` may be blank or wrong due to missing time zone info in ZIP format

**Per-tier container counts:**

| Tier | PST/MBOX parents | ZIPs (as containers) |
|------|-----------------|---------------------|
| Small | 8 | 5–10 |
| Medium | 40 | 20–40 |
| Large | 400 | 200+ |
| Extra large | 745 | 370 |

**Per-custodian:** show 3–5 PST parent records per custodian, with 1–2 password errors across the dataset.

---

## Rule 4 — Special Cases and Edge Conditions

These must appear in every dataset to make the data realistic and useful for testing.

### ICS (Calendar Invites)
- `Date Sent` = **blank** (Outlook sends the .msg with a date, but the .ics file added to the calendar does not carry a sent date)
- `Date Received` = blank
- `Primary Date` = the meeting start time, not a sent date
- Important: tests that assume Primary Date = sent date will fail on ICS — this is intentional

### Scanned PDFs
- `OCR Flag` = Yes
- `Extracted Text Preview` = lower quality, shorter excerpt
- `Processing Status` = "Complete" (OCR ran) or "Error" (OCR failed — include a few)
- Aim for 5–10% of all PDFs being scanned

### MIP-Protected PDFs
- `Processing Status` = "Not Resolved" or "Error"
- `Processing Error Type` = "MIP Protected - Limited Extraction"
- `Has Natives` = Yes (native exists but content is protected)
- `Extracted Text Preview` = blank
- Include 2–3 per medium tier, 10–20 per large tier

### HEIC/JPEG with GPS EXIF
- Populate `GPS Latitude`, `GPS Longitude`, `GPS Altitude` on 10–20% of mobile images
- `Camera Make`, `Camera Model` should reflect iPhone or Android brands
- `Date Taken` should match the document date range of the matter

### ZIP Children — Date Gap
- `Date Created` and `Date Modified` on ZIP children should sometimes be blank or clearly wrong (e.g. 1980-01-01) to reflect the ZIP format's time zone limitation
- Flag these with a note in `Processing Status` = "Warning - Date Unreliable"

### Teams RSMF — Placeholders
- 3–5 Teams RSMF records per tier should have `Rsmf/HasPlaceholders` = Yes
- These represent call recordings or other unsupported event types
- `Rsmf/Application` = "Teams"

### Slack — Required Files
- Slack records require org_users.json and channel/DM metadata
- In mock data: ensure Slack RSMF records have `Rsmf/EventCollectionId` populated to represent the workspace channel
- Include direct messages, channel conversations, and group DMs as separate records

### Bloomberg XML
- Large tier only
- `Rsmf/Application` = "Bloomberg" or treat as structured container
- High responsiveness rate — financial communications are almost always relevant

### Google Workspace
- Populate `GoogleDrive/DocID`, `GoogleDrive/DocumentType`, `GoogleDrive/Author`
- `GoogleDrive/DocumentType` values: DOCUMENT, SPREADSHEET, PRESENTATION, FORM, DRAWING, SITES_PAGE
- Include at least one `GoogleDrive/SharedDriveID` per dataset to represent shared team drives
- Google Docs exported as .docx — the File Extension is docx but the type is "Google Workspace - Document"

### Cellebrite Structured Excel
- These are Excel files generated by Cellebrite from structured data (call logs, contacts, web history)
- `File Type Category` = "Cellebrite Structured Data"
- Appear in an "Other Data" virtual folder path
- Analytics eligible, dedup by SHA256

### Unsupported File Types
Every dataset needs a realistic spread of unsupported types. Minimum:
- 1–2 Microsoft Access (.mdb or .accdb) — "Not Supported" error
- 1–2 Apple iWork (.pages, .numbers, .key) — "Not Supported"
- 1–2 corrupt/zero-byte files — "Corrupt File" error
- 1 file with no recognized signature — "Unknown File Type"

---

## Rule 5 — Deduplication

Deduplication method must match the file type exactly. This is used to populate the
`Duplicate Spare` field and group near-duplicates.

- **MD5**: MSG, EML — deduplicates on the hash of message content
- **SHA256**: all document types (DOCX, PDF, XLSX, PPTX, images, etc.)
- **EventCollectionId**: RSMF (Teams, Slack, SMS) — deduplicates on the conversation/channel ID
- **N/A**: Container types (PST, MBOX, ZIP parents) — containers are never deduplicated as a unit

---

## Rule 6 — Processing Error Distribution

Every tier must include a realistic spread of error types, not just "Password Protected."

**Rate: 5–12% of documents carry a processing error, with at least 6 distinct error types.**

Real matters run exceptions in that range; the per-tier counts this table used to specify
totalled 1% and never matched what the generator produced. The band is the rule, and the mix
below is the shape it should take, not an exact quota:

| Error Type | Relative weight |
|------------|-----------------|
| Unsupported File Type | heaviest |
| OCR Failure (scanned PDF) | heavy |
| Container Extraction Timeout | moderate |
| Corrupt / Unreadable | moderate |
| Extraction Failure | moderate |
| Teams/Slack Conversion Error | moderate |
| MIP Protected | light |
| Password Protected (PST/ZIP and Office) | light |

Error documents must also **reach the error queue**: at least 75% carry
`Workflow Stage` = "Pre-Review: Processing Error". An error that is labelled but never staged
is not modelled, it is decorated.

See Rule 12 for the requirement that these documents have natives that actually fail.

---

## Rule 7 — TAR Score Distribution

TAR scores must be **bimodal**, not uniform random. A flat distribution does not look like
real Active Learning output and will break any feature that visualizes or thresholds on it.

Distribution:
- **40%** score 0–20 (clearly non-responsive, model is confident)
- **35%** score 75–100 (clearly responsive, model is confident)
- **25%** score 20–75 (uncertain band — these are the documents that need human review)

Only assign TAR scores to documents that are in the **review population** (not ECA-excluded,
not duplicates/NIST, not processing errors). Score the full review population including
unreviewed docs — that's the realistic scenario where TAR is used to prioritize review order.

---

## Rule 8 — Custodian Rules

- Every custodian must have a realistic document volume (no custodian at exactly the same count)
- Hold status must vary: most acknowledged, 1–2 outstanding, 1 escalated in medium/large
- Key custodians (executives, primary actors) should have 3–5× the volume of peripheral custodians
- One custodian per dataset should never have acknowledged the hold
- Large tier: include 2–3 custodians with departed/deactivated accounts
- Large tier: include 1–2 custodians added to the hold after initial issuance (amended hold)

---

## Rule 9 — Email Family and Threading

- Email families (parent + attachments) have an average size of 3–4 documents
- ~22% of emails are standalone (no attachments, no thread)
- Thread-inclusive documents (~15–20% of threaded emails) are marked `Email Threading Inclusive` = Yes
- Near-duplicate groups span ~250 docs in medium, ~10,000 in large
- `In Reply To` on child emails must reference the parent's `Message ID`
- `Conversation Index` must be populated for all emails in a thread

---

## Rule 10 — Production Rules

- Only **Responsive, non-privileged** documents get Bates numbers
- Redacted documents have both `Bates Begin`/`Bates End` AND `Redacted` = Yes
- Privileged documents get a `Privilege Reason` but no Bates numbers
- `Production Set` reflects the volume name (e.g. VOL001, VOL002)
- Multiple productions in medium/large: use different Bates prefixes or volume numbers per production
- 10–25 clawback documents in large tier: previously produced, then `Redacted` changed to "Clawed Back"

---

## Rule 11 — Custodian Folder Structure

Rules 1 through 10 govern the *metadata*. This rule governs the *package on disk*.

`Processing Folder Path` is a contract, not a label. When a load package writes native files,
the directory tree must match that column exactly:

```
natives/
  Exchange_Online/Michael_Brennan/2014/01/DOC-0000318.eml
  OneDrive/Thomas_Bradley/2013/11/DOC-0000229.docx
  Mobile_Extraction_UFDR/Sarah_Chen/2015/12/DOC-0000901.heic
  ...
```

The data source is the first segment as of Rule 21. Relativity assigns a custodian **per
data source**, so the granularity that matters is the pair rather than the person: once
somebody's documents arrive through four channels, one folder per person is as wrong as one
folder for everybody.

The reason is Relativity Processing: a processing set assigns custodians **per data source**.
One flat folder means one data source, and therefore one custodian for the entire collection,
or manual sorting. One folder per custodian means one data source each, with custodian
assignment falling out of the structure.

Requirements:

- Every native lives under the path its `Processing Folder Path` describes. No files at the
  root of `natives/`.
- `NativeFilePath` in the load file is the package-relative path in backslash form, e.g.
  `natives\Exchange_Online\Michael_Brennan\2014\01\DOC-0000318.eml`.
- Every package ships `custodian-sources.csv`: **one row per data source and custodian**, with
  the source, name, email, org, department, folder, document count, natives written and total
  bytes. This is the sheet whoever builds the processing set works down, and it is keyed on the
  pair because that is what Relativity assigns a custodian at. The small tier yields 66 rows:
  8 sources across 10 custodians.
- Documents with no custodian go under `_Unassigned/`, and only when a build deliberately asks
  for them. The default build assigns every document to a custodian.

A flat layout is available via `--flat` for anyone who wants the old shape, but it cannot
support per-custodian data sources and the generated `IMPORT_README.txt` says so.

Verify a built package with:

```bash
python scripts/validate_load_package.py load-packages/small
```

---

## Rule 12 — Native Layer Error Fidelity

Rule 6 governs the *metadata* error distribution. This rule governs the *files*.

**A document flagged `Processing Status = Error` must have a native that actually produces that
error when processed.** Metadata that claims an error while sitting on top of a healthy file is
worse than no error modelling at all: it makes a dataset look like it covers the failure paths
when it does not.

When a package is built with `--with-errors`:

| `Processing Error Type` | The native on disk is |
|---|---|
| Password Protected | A real encrypted PDF, or a real password protected container for non-PDF rows |
| Corrupt File | A valid file truncated to 40% of its bytes |
| Unsupported File Type | A real stub of an unsupported format, correct magic bytes |
| Extraction Failure | A valid OOXML package with its main part removed |
| Container Extraction Timeout | Eight levels of nested containers, tiny payload |
| Teams Conversion Error | RSMF JSON truncated mid-object |
| OCR Failure - Poor Scan Quality | A PDF with vector marks only and no text layer |
| Empty File | Exactly 0 bytes |
| Extension Mismatch | PDF content under the extension the row claims |

Requirements:

- **Sizes must agree.** `File Size` in the load file is rewritten from the bytes actually
  written. The metadata's original figure describes a file that was never created.
- **`Processing Status` and `Processing Error Type` belong in the load file.** Both are in
  `DAT_COLUMNS` so an import-only workflow still sees the intended outcome.
- **Every package ships `EXPECTED_ERRORS.csv`**: control number, custodian, native file,
  scenario, how it was built, the expected Relativity error, whether that outcome is
  guaranteed, and any caveat. A tester compares it against the processing error report.
- **Never fabricate a zip bomb, malware, or an EICAR style test file.** Container scenarios use
  shallow nesting with tiny payloads.
- **State what cannot be fabricated.** MIP protected rows need a real tenant to apply the
  label, so their natives stay healthy and the build says so out loud rather than pretending
  coverage exists.
- **Be honest about non-determinism.** OCR failure, container timeout and conversion errors
  depend on engine and worker configuration. Those rows are marked `Guaranteed = no` with the
  reason, and the expected error is treated as a family, not an exact string.
- **Never rescue a deliberately broken file.** The generator's exception fallback is disabled
  for documents with a fabrication scenario; a failure there is a bug worth seeing.

Verify with:

```bash
python scripts/validate_load_package.py load-packages/small
```

---

## Rule 13 — Edge Cases: Documents That Starve a Feature

Rule 12 covers files that fail processing. This covers the more dangerous case: documents that
process **perfectly** and still leave a feature with nothing to work with.

The generated tiers are uniform to a fault. Every document has a custodian, a date, extracted
text, and `Language = English`. Any feature that aggregates over a collection has therefore only
ever been exercised against a complete input, which is not a state any real matter reaches.

`--edge-cases` starves a slice of the tier. Twelve scenarios, each drawn from a disjoint pool so
no document carries two faults:

| Scenario | What it starves |
|---|---|
| `no_custodian` | Key Relationships, Collection Coverage, any per-custodian rollup |
| `missing_date` | timelines and date range filters |
| `sentinel_date` | timelines: an axis stretched to 1601 or 2099 |
| `no_extracted_text` | Topics, Summaries, PI Detect, anything reading document text |
| `non_english` | Primary Language, and any English-only text analysis |
| `mixed_language` | Primary Language: no single right answer |
| `blank_recipients` | Key Relationships: an email with no edge to draw |
| `list_only_recipients` | Key Relationships: an edge to a list rather than a person |
| `orphan_attachment` | family rollups: a child whose parent is not in the set |
| `broken_family` | family rollups: a family record naming a document that is absent |
| `duplicate_md5` | dedup and Collection Coverage |
| `media_no_text` | Topics, Summaries, Document Categories: no text, ever |
| `oversized_text` | summarisation and topic extraction: more text than a model context holds |

Requirements:

- **Off by default.** Edge cases run on their own RNG stream and are applied after generation,
  so default output stays byte-identical. The committed tiers and the CI determinism check are
  unaffected, and anyone using a tier as clean fixture data keeps clean fixture data.
- **Scripted hot documents are never touched.** They carry the narrative.
- **Every tier that has them ships `edge-cases.json`**: per scenario, what it starves, the count,
  and the document list. It is the counterpart to `EXPECTED_ERRORS.csv`.
- **`Word Count` is the contract for `oversized_text`.** The builder writes a native holding the
  number of words the metadata claims (300k, 800k and 1.5M, roughly 2 MB, 5 MB and 10 MB), so a
  document claiming a million words really has them. The text is a cycled seed, which is fine for
  exercising a token limit and unrealistic for topic modelling; it also compresses to nothing, so
  16.7 MB of raw text adds nothing to the download.
- **Documents with no custodian go to `_Unassigned/`** in a load package, and get their own row
  in `custodian-sources.csv` (Rule 11).
- **The report must be true.** `validate_mock_data.py` probes each listed document and fails if
  one is not actually starved, so the report cannot drift from the data.

Verify with:

```bash
python scripts/validate_mock_data.py --tier small --dir mock-data/small-edge
```

---

## Rule 14 — Production Drill Baseline

The ECI document drill always shows the same universal columns
(`docs/widgets/cross-cutting-ux.md` in eci-ui, decided 2026-07-21):

> Control Number · Custodian · Primary Date/Time · **Record Type** · Unified Title ·
> Topic (AI) · Summary (AI)

Three of those are produced by ECI downstream (Unified Title, Topic, Summary) and do not belong
in a collected dataset. The rest are collected fields, and `Record Type` was missing, so a drill
built against this data could not populate a column it always shows.

Every document carries a `Record Type`:

| Value | Applies to |
|---|---|
| `Email` | MSG and EML records |
| `Container` | the container parents (Level 0) |
| `EDoc` | everything else |

`Attachment` is covered by Rule 15: loose documents re-parented onto the emails that claim them.
Thread replies remain `Email`, since that is what they are.

### Custodian count and distribution

Production caps Key Relationships at the **top 25 pairs and top 25 non-custodian entities** and
tells the user that pairs below the cut are not listed. A tier that cannot reach the cut cannot
test it.

| Tier | Custodians | Internal pairs |
|---|---|---|
| Small | 10 | 45 |
| Medium | 10 | 45 |
| Large | 40 | 780 |
| Extra large | 40 | 780 |

Extra large borrows large's roster rather than inventing a second one, so there is one
set of custodians and one set of scripted documents to keep true. Its volumes run from
14.8% of the collection down to 0.02%, the same skew large has, since the weights are
the same and only the totals differ.

The small tier ran on 4 custodians, giving 6 pairs, and 4 is not a realistic collection at ~1,500
documents anyway. It is now 10, roughly 150 documents each, spanning Mallinckrodt, Insys and
McKinsey. The six added were drawn from the medium roster rather than invented, so the MDL 2804
narrative holds and the people the scripted hot documents name are actually custodians.

**The distribution must be skewed, and it must follow `doc_target`.** `doc_target` was declared on
every custodian and never read: `random.choice` picked uniformly, so every tier came out flat at
roughly 10% each. Real collections are nothing like that, and a flat one hides every bug that
depends on one custodian dominating. Assignment is now weighted, and the small tier runs from 23%
down to 2.4%, a 9.6x spread.

---

## Rule 15 — Attachments

`Has Attachments` and `Attachment Count` were rolled at random and backed by nothing. No
attachment existed as its own document, so `Record Type` never took the value `Attachment` and
nothing that rolls up a family by attachment record could be tested against this data.

Attachments are **re-parented from existing loose documents**, not invented. Inventing them would
inflate the tier and skew the Rule 1 shares; re-parenting keeps both intact, and it is realistic,
since attachments really are Word, Excel, PDF and image files.

Requirements:

- An attachment is a non-email, non-container document with `Record Type` = `Attachment`, a
  `Parent Document ID` that resolves to an **email**, and the parent's `Family ID`.
- **Attachments share their parent's custodian and date.** A collection does not split a family
  across custodians.
- **The claim must match reality in both directions.** An email saying it has three attachments
  has three; one saying it has none has none. Where the custodian's pool of loose documents runs
  out, the claim is reset rather than left dangling.
- Scripted hot documents and thread stubs are never re-parented.
- **Edge cases move a family as a unit.** Blanking one side's custodian would leave a family
  straddling two custodians, which no collection produces and which is indistinguishable from a
  bug. `broken_family` never removes an attachment, since that would falsify its parent's count.
  `orphan_attachment` records what it detached from, so Rule 15 can tell a planted orphan from a
  broken one and can excuse the parent whose count it falsified.

- **Only half of each custodian's loose documents may be consumed.** Without a reserve,
  attachments took 595 of 617 and left 22 standalone EDocs, which is not a collection anyone has
  ever seen.

In the small tier this yields 306 attachments across 131 emails (16% of email), alongside 311
documents that stay loose, with the tier size unchanged at 1,439. Two of those attachments are
Rule 18's, re-parented to carry the encrypted payload on the planted finding and its decoy.

---

## Rule 16 — Personal Information

Rules 1 through 15 build a corpus with no personal information in it at all. PI Detect
could therefore only ever be tested by starving it (Rule 13's `no_extracted_text`) or by
hand-editing a native. A widget whose whole job is finding PI had never been run against
a corpus that has any.

Two things matter more than volume:

- **Distribution.** PI concentrated in one spreadsheet is the easy case. Most instances
  sit in **email bodies**, which is where PI really accumulates and the harder catch.
  The rest spread across a roster, a benefits form and a chat.
- **Irrelevance.** One document per tier is dense with PI and has nothing to do with the
  matter, so the widget has to surface something nobody asked about.

| Scenario | Where the PI lives | Small | Medium | Large | Extra large |
|---|---|---|---|---|---|
| `email_body_ssn` | email body | 6 | 30 | 300 | 560 |
| `email_body_card` | email body | 3 | 15 | 150 | 280 |
| `spreadsheet_roster` | spreadsheet cells | 2 | 8 | 60 | 110 |
| `benefits_form_pdf` | pdf body | 3 | 12 | 90 | 170 |
| `chat_phone_numbers` | chat message | 3 | 12 | 90 | 170 |
| `irrelevant_high_sensitivity` | document body | 1 | 2 | 4 | 7 |

### Every value must be non-issuable

Nothing seeded here can collide with a real person:

| Type | Value space | Why it is safe |
|---|---|---|
| SSN | area 900-999 | the SSA has never issued an area number above 899 |
| SSN (toggle) | area 666 | the SSA has never allocated area 666 |
| Payment card | the published test numbers | the card networks hand these out for testing |
| Phone | `555-01xx` | the block reserved for fiction |
| Personal email | `.invalid` TLD | reserved by RFC 2606; it cannot resolve |

**The SSN range is a config toggle**, because the never-issued 9xx block is exactly the
kind of value some detectors score as low confidence, which makes a widget look like it
is under-reporting when it is behaving as designed:

```bash
python scripts/generate_mock_metadata.py --tier small --ssn-range 9xx   # default
python scripts/generate_mock_metadata.py --tier small --ssn-range 666   # standard format
```

Rows seeded from the 9xx block carry `Expected To Detect = maybe` and say why. Rows in
the 666 range carry `yes`.

Requirements:

- **On by default.** A pass that *feeds* a widget belongs in the tier; a pass that
  *starves* one (Rule 13) has to be asked for. `--no-pi` turns it off.
- **Every tier ships `pi-ground-truth.csv`**: one row per instance, with control number,
  custodian, scenario, type, where it lives, the literal value, whether it is expected to
  be detected, and the caveat. One row per instance, not per document, so it diffs
  straight against a PI Detect export.
- **The native text is rendered *from* those rows**, by `pi_layer.render`. There is no
  second copy of the values. A corpus and a ground truth that could disagree make the
  ground truth worthless.
- **`PI Seeded` on `documents.csv`** lists the types on that document, so the coded field
  and the ground truth can be checked against each other in both directions.
- **PI never lands on a document the edge cases starve**, on a fabricated error, or on a
  produced document that a recode would contradict (Rule 10).

Verify with:

```bash
python scripts/validate_mock_data.py --tier small          # values are non-issuable
python scripts/validate_load_package.py load-packages/small # values are in the natives
```

---

## Rule 17 — Language Composition

Every row in every tier carried `Language = English`, so Primary Language Composition had
one bar: no second slice, no minor slice that has to stay legible next to a major one, and
no sort order to get wrong.

The second-language documents are **deliberately unrelated to the matter**: facilities
notices, canteen closures, parking markings. A German slice about suspicious order
monitoring would leave a reviewer wondering whether the foreign-language population is
secretly responsive. This one answers that question up front.

| Tier | Mix |
|---|---|
| Small | German 2.0% |
| Medium | German 1.5%, Polish 1.0% |
| Large | German 1.2%, Polish 0.8%, Spanish 0.4% |
| Extra large | German 1.2%, Polish 0.8%, Spanish 0.4% |

```bash
python scripts/generate_mock_metadata.py --tier small --second-language-share 0.008
python scripts/generate_mock_metadata.py --tier small --no-language-mix
```

Requirements:

- **Real sentences.** A classifier fed lorem ipsum reports Latin, and a classifier fed one
  word reports nothing. The bodies are ordinary office prose in the target language, and
  the load package writes them into the natives.
- **Text-bearing documents only.** Setting `Language` on a media file or a container claims
  a classification nothing could have produced.
- **Non-responsive or unreviewed documents only**, and never coded onto an issue. Rewriting
  a document a reviewer coded Responsive into a canteen notice contradicts its own coding.
- **Every tier ships `language-mix.json`**: the requested share, the achieved share, the
  document list with each body, and the note saying why the slice is irrelevant.
- Rule 13's `non_english` and `mixed_language` remain the *unexpected* language cases, and
  stay opt in. Rule 17 is the expected one.

---

## Rule 18 — Planted Findings, and a Decoy

The thirteen scripted hot documents (Rule 4 and the narrative) are all the same kind of
finding: surface the document, read it, and the story is on the page. That tests review. It
cannot test the claim early case assessment actually makes, which is about what metadata
surfaces *before* anyone reads anything.

So each tier plants a matched pair, a decoy, and one extraction-depth case:

| Finding | Findable by | Invisible to |
|---|---|---|
| `metadata_only` | one outbound message to an address that appears exactly once in the corpus, carrying an encrypted attachment | content analysis: the body is three words and the attachment will not open |
| `content_only` | reading it | every keyword filter on the matter, and every metadata cut |
| `decoy` | the same filter that catches the principal, and it is innocent | nothing: it is meant to be caught |
| `buried_deep` | full extraction: the payload is on tab 11 of 12 | any extraction that stops at the first sheet |
| `no_overlap_pair` | the pair itself: two custodians corresponding at volume, so the edge is real | any topical link to the matter, because there is none |

The decoy's distinguisher is **buried in the record, not stated**: a second message to the
same address shows it belongs to an external assurance provider on an internal controls
review. So the decoy's address appears twice and the principal's appears once, and the
right answer comes from walking the entity rather than from reading either document.

Requirements:

- **Ground truth at generation time.** Every tier ships `findings.json` with, per finding,
  what it is findable by, what it is invisible to, the expected answer and how to verify
  it. A tester who gets a negative result needs to know whether that is the right answer.
- **The unique address appears exactly once**, across `Email From SMTP`, `Email To SMTP`,
  `Email CC SMTP`, `Email BCC SMTP` and `Rsmf/Participants`. One stray message shifts the
  entity's active range and invalidates the finding, so it is asserted, not assumed.
- **No document names a planted correspondent before its seeded date.** Also asserted.
- **The content-only finding hits zero matter keywords** and names no custodian in full.
  `planted_findings.MATTER_KEYWORDS` is the list, and the check runs against it.
- **The encrypted attachment is a real one.** It is flagged `Password Protected`, so
  `--with-errors` fabricates a genuinely encrypted native for it (Rule 12).
- **Families stay true.** The attachment is re-parented from a loose document of the same
  custodian, and both sides' claims are updated together (Rule 15).
- **Planted documents are off limits to the edge cases**, and to Rule 20. Starving one
  falsifies its own ground truth, and `no_overlap_pair` owns a whole correspondence rather
  than a single document, so rewriting a recipient anywhere in it would break the very edge
  the finding asserts.

### The planted negative

`no_overlap_pair` is the odd one out: the other four are things to find, and this one is a
thing to correctly find nothing in. Two custodians exchange 18 documents, every one of them
about an employee blood drive. They share no issue tag, and the vocabulary of that
correspondence appears in no other document in the corpus.

So a feature asked what connects them should find one mundane subject and nothing else, and
a feature asked whether they discuss the matter should say no. **Without a planted negative
there is no way to tell a correct "nothing here" from a broken analysis**, which is the only
reason it exists.

Both halves of the pair keep substantial volume elsewhere, asserted at more than twice the
correspondence, so the edge is not their whole story and the pair cannot be dismissed as
noise.

---

## Rule 19 — The Native Date Layer

Rule 12 governs whether a native fails the way its metadata claims. This governs the dates
on the ones that succeed.

**Every date on a native must come from the manifest.** python-docx, python-pptx, openpyxl
and fpdf2 each stamp their own date on every file they write, and those stamps are what
Relativity reads at processing time. The `.dat` carried no `Date Created` column to override
them, so the leak landed straight in Collection Coverage.

Measured on the package shipped in v1.12.0, `load-packages/small-load-package.zip`:

| What | What it carried |
|---|---|
| every `.xlsx` | created and modified `2026-08-19`, creator `openpyxl` |
| every `.pdf` | `CreationDate 2026-08-19` |
| every `.pptx` | created `2013-01-27`, `lastModifiedBy` "Steve Canny", on every file |
| every `.docx` | created correct, modified `2013-12-23`, the python-docx template default, which precedes its own created date |
| every native | filesystem mtime set to the build clock |

299 of 448 Office and PDF natives carried a date outside the matter window, 403 carried a
library's name in their document properties, and 448 filesystem mtimes were adrift.

Requirements:

- **Both Office core properties are set**, created and modified, from `Date Created` and
  `Date Last Modified`. Setting only created leaves the library's default in the other one.
- **`Date Created` and `Date Last Modified` are in `DAT_COLUMNS`.** Without them Relativity
  derives both from the file, which is the whole failure mode.
- **Filesystem mtimes are stamped** from `Date Last Modified`, with the same fallback chain
  the properties use. Skipped outside 1971-2100, since `os.utime` cannot represent a 1601
  sentinel; the document properties still carry it, which is where the test wants it.
- **No library name survives in document properties.** `openpyxl`, `python-docx`,
  `python-pptx` and "Steve Canny" are all asserted absent. openpyxl overwrites
  `properties.modified` inside `save_workbook`, so the workbook is written through
  `ExcelWriter` directly.
- **A document with no date still gets one**, from the midpoint of the tier's window. Every
  real file has a date; it is the load file that is missing one (Rule 13 `missing_date`).
- **Documented wrong dates stay wrong.** Rule 4's 1980-01-01 ZIP marker and Rule 13's
  sentinels are exempted by name, not by widening the window.

Verify with:

```bash
python scripts/validate_load_package.py load-packages/small
```

---

## Rule 20 — The Entity Population

Rule 14 fixed the *custodian* side of Key Relationships: ten custodians give 45 internal
pairs, past the top-25 cut production applies. The non-custodian side was never fixed, and
it is half of what the widget shows.

Measured on the small tier before this rule:

| | Before | After |
|---|---|---|
| Distinct addresses in the collection | 15 | 54 |
| Non-custodian entities | 12 | 44 |
| Entities on exactly one document | 1, and it was planted by Rule 18 | 28 |
| People reachable at two addresses | 0 | 2 |

Twelve non-custodian entities against a production cap of **25** meant the tier could not
reach the cut, so the "entities below the cut are not listed" behaviour was untestable with
the package most people download. One singleton meant there was no organic long tail. And no
alias meant name normalisation had never been run against this data at all.

### What it seeds

- **An external roster**, sized to clear the cap comfortably rather than squeak past it: 40
  entities for small, 60 for medium, 120 for large and extra large. Fictional people at the
  organisations this matter actually involves, which is the convention the custodian roster
  already follows.
- **A skewed volume distribution**: a short heavy head, a moderate middle, and a tail that is
  mostly singletons. That is the shape a real external population has, and the tail is
  precisely what a top-N cap hides.
- **Alias addresses**: 2 people for small, up to 5 for the big tiers, each sending a minority
  of their own mail from a second address. The reasons are the realistic ones, a legacy domain
  from before a spin-off, an older account format, a personal address used for work.

The named roster carries the narrative: counterparties a reviewer could plausibly chase,
including the speaker bureau physicians Rule 4's story already names. Beyond it the tail is
generated as dispensing pharmacies, because a matter this size really does have hundreds of
dispensing counterparties that appear once each and writing them out by hand would add
nothing.

### Requirements

- **On by default**, like Rules 16 to 18. `--no-entities` turns it off.
- **Every tier ships `entities.json`**: each entity with its organisation, its kind, its
  document count and a sample of its documents, plus the alias list and the singletons.
- **The counts are a census of the corpus, not a record of what the pass handed out.** Three
  regulator inboxes were already recipients in the generator's own round-robin, so an
  assignment count understated them by an order of magnitude. The validator checks every
  claimed count against the corpus, which is how that was caught.
- **Runs after Rules 16 to 18 and respects everything they claimed**, so a rewritten
  recipient cannot land on a document whose ground truth depends on its current one. In
  particular Rule 18's unique address still appears exactly once, which is asserted.
- **The rewritten documents join the protected set**, so the edge cases cannot blank a
  recipient the entity census counts.

Verify with:

```bash
python scripts/validate_mock_data.py --tier small
```

---

## Rule 21 — The Data Source Dimension

Collection Coverage exists to compare data sources, and the tiers had no such axis. The only
grouping available was custodian, so "sources with genuinely different metadata profiles"
stood as the longest-running gap in the widget coverage table.

**The rule does not fabricate a difference.** The metadata profiles already varied, and they
varied by file type: email documents carry email metadata and no EXIF, mobile images carry
EXIF and no email metadata, Google Workspace documents carry Drive fields and an extension
that deliberately disagrees with their type. A real collection produces those differences
*because* the documents came through different channels. This rule names the channel, so the
difference becomes something you can group by rather than something you can only infer.

| Source | What it collects | Measured profile, small tier |
|---|---|---|
| Exchange Online | Mailbox: mail and calendar | 821 documents, email metadata on 98% |
| OneDrive | Personal drive: loose Office documents and PDFs | 293 documents, Office properties on 74% |
| Network Share | File server: loose documents, archives, unsupported formats | 222 documents, Office properties on 64%, 4% containers |
| Mobile Extraction (UFDR) | Cellebrite handset: chat, photos, call logs | 38 documents, camera model 92%, EXIF GPS 10%, OCR 92% |
| Scanned Production | Paper, scanned and OCR'd | 27 documents, OCR on 100% |
| Microsoft Teams | Channel and chat export | 20 documents, RSMF on 100% |
| Slack Export | Workspace export | 10 documents, RSMF on 100% |
| Exchange (PST export) | Archived mail as containers | 8 documents, 100% containers |

Medium and above add **Google Workspace** and **Bloomberg Vault**, because those file types
only exist from the medium tier up.

**OneDrive and Network Share share a profile on purpose.** Two sources whose metadata looks
identical is a real case, and a widget still has to group them separately. A rule where every
source is trivially distinguishable would not test that.

### Requirements

- **On by default.** `--no-sources` turns it off and leaves custodian as the only axis.
- **`Data Source` on `documents.csv`**, and in the load file, so Relativity has the field
  rather than having to derive it from a path.
- **The source is the first segment of `Processing Folder Path`**, and therefore of the tree
  on disk (Rule 11). Asserted per document.
- **`custodian-sources.csv` is keyed on the pair**, one row per source and custodian.
- **Every tier ships `data-sources.json`**: per source, what it collects, its folder, its
  document count, its custodian count, its file types, and **the profile measured from the
  data** rather than described. The validator checks every count against the corpus, and
  fails if fewer than four distinct profiles appear, because an axis where everything
  measures the same is decoration.
- **Runs before the other passes**, since `Processing Folder Path` depends on it.

Verify with:

```bash
python scripts/validate_mock_data.py --tier small
python scripts/validate_load_package.py load-packages/small
```

---

## Rule 22 — Collection Shape: a Gap, a Spike, and an Ambiguous Population

The last two gaps in the widget coverage table, and they share a shape: both are about
giving a widget something **hard** rather than something more.

**The date axis had nothing to detect.** Measured on the small tier before this rule: 48
months running 15 to 48 documents, a 3.2x spread with no anomaly in it. That is organic
variation, and a feature claiming to surface collection gaps could not be tested against it
either way, because there was no gap to find and no spike to explain.

**Document Categories had no ambiguous case.** Every document sat squarely in one topic, so
categorisation was only ever asked easy questions. A population that plausibly belongs to
two categories is the one that tells you whether a classifier commits, hedges, or guesses.

### What it plants

| | Small tier |
|---|---|
| **A gap** | The highest-volume custodian has **zero** documents across a three month window that holds **28, 32 and 26** documents for everybody else, against a median month of 28 |
| **A spike** | One month carries **3.9x** the median, 108 documents against a median of 28 and a next-highest of 43 |
| **An ambiguous population** | 24 documents carrying both `Speaker Bureau Payments` and `Prior Auth Fraud`, with content that supports both |

The gap is **one custodian's, not the collection's**. That is how a real hole appears: one
person's mailbox preserved late, or a migration that lost a period, while everybody else's
data is fine. A collection-wide dip is a different thing and a much easier one to spot.

The ambiguous population is a speaker-bureau honorarium to a practice whose prior
authorisation numbers moved afterwards. There is no single right category, so a classifier
that commits to one is not wrong and one that reports both is not hedging. Both categories
also occur **on their own** elsewhere in the tier, asserted, because an overlap only means
something if the two categories exist separately.

### Requirements

- **Nothing is deleted or invented.** The gap and the spike are made by **moving dates**, so
  the tier keeps its size and its Rule 1 file type shares.
- **Every move stays inside the matter window and inside the document's own narrative
  phase.** A document that moves does not change what it is about, and Rule 19's window
  assertions still hold afterwards, which is checked on the built package.
- **Every date on a document moves together**: `Primary Date`, `Sort Date`, `Date Sent`,
  `Date Received`, `Date Created`, `Date Last Modified`, `Date Taken` and the RSMF range.
  Moving one and not the others would plant an inconsistency nobody asked for.
- **The gap goes where the collection is busy**, chosen as the highest-floor quarter the
  custodian appears in rather than by position in the month list. Placed positionally it
  landed in the corpus's thin leading tail, where the medium tier held 35 documents between
  every other custodian against a median of 137: an empty row there is indistinguishable
  from the matter not having started yet. Asserted **month by month**, not summed, because
  three months summed against a one-month median is what let the weak placement through.
- **The spike draws from eight surrounding months, not two.** Pulling eighty documents from
  two neighbours halved them, which is its own anomaly; spread wide, the dip is a few
  documents each.
- **The two anomalies never touch.** The gap spreads the documents it moves across six
  receiving months in proportion to what they already carry, rather than stacking them into
  the nearest one, which at xlarge builds an accidental spike bigger than the planted one.
  The spike never draws from the gap window, and its month can never be inside it. Both are
  asserted. Two planted anomalies have to be independently readable, or they read as one
  confusing event.
- **Runs first of all**, before Rule 21, because `Processing Folder Path` carries year and
  month and Rule 11 makes that path a contract with the tree on disk.
- **Every tier ships `collection-shape.json`**: the gap's custodian and months, the spike's
  month and multiple, the ambiguous categories, and for each one what to expect and how to
  verify it.
- **On by default.** `--no-shape` turns it off and leaves the date axis with nothing to find.

Verify with:

```bash
python scripts/validate_mock_data.py --tier small
```

---

## Rule 23 — The Extracted Text Layer

Rule 12 governs whether a native fails the way its metadata claims, and Rule 19 governs its
dates. This governs the **text**, and it exists because two of the six widgets read nothing
else.

**Document Categories and PI Detect are LLM passes over extracted text**, not over metadata and
not over the native file. So a package with perfect metadata and no text reaches neither. Before
this rule, the load file carried **none** of Rule 16: measured on the built small package, 0 of
102 seeded PI values appeared anywhere in the `.dat`. They were inside the natives, which a
metadata-only import never reads.

### What it requires

- **Every document with a native ships its extracted text** as a sidecar at
  `text/{Control Number}.txt`, named by the `ExtractedTextFilePath` column. Relativity accepts
  extracted text inline or as a per-document path; the path form is what
  `load-packages/small-real/` already used, and it keeps the `.dat` readable instead of carrying
  0.3 GB of prose inline.
- **The text is extracted from the native, not from the body that went into it.** This is the
  part that matters. A body-derived sidecar held only 39 of 102 seeded values, because the
  spreadsheet PI scenario writes into cells via `make_xlsx` and never touches the body.
  Extracting from the file finds everything actually in it, which is what Relativity does.
- **A document flagged `Processing Status = Error` gets an empty sidecar.** Extraction is
  precisely what failed on it. Claiming text for a file that cannot be read is the same lie the
  native layer exists to avoid.
- **`Language` is a load file column**, so a language breakdown has something to read from
  metadata alone. Relativity derives its own during processing; this is for the import that has
  no natives to process.
- Asserted on the built package: every declared path exists, no healthy document has empty
  text, and **every seeded PI value is reachable from the text without the native**.

Cost, measured on the small tier: **1.0 KB a document**, against roughly 8 KB for the native.
At the extra large tier that is about 0.3 GB of text against 2.2 GB of natives.

Verify with:

```bash
python scripts/validate_load_package.py load-packages/small
```

---

## Rule 24 — Mail Direction

Rule 14 fixed the custodian side of Key Relationships and Rule 20 fixed the external side.
Both are about **who** is in the graph. This is about which way the edges point, and it was
wrong in every tier shipped before it.

Measured on the medium tier before this rule, over its 5,214 emails:

| | Before | After |
|---|---|---|
| Emails sent by their own custodian | 5,214 of 5,214 | 3,016 of 5,214 |
| Emails the custodian received | 0 | 2,198 |
| Addressed to their own sender | 396 | 18 |
| Carrying more than one To recipient | 0 | 1,474 |
| Distinct senders | 13 | 25 |

The generator set `Email From` to the custodian's own name unconditionally, so the corpus
contained **no inbound mail at all**. A collection is a set of mailboxes, and a mailbox is
mostly things other people sent you. Ten custodians radiating outward with nothing coming
back is not a shape a matter produces, and it is the one shape that makes a relationship
graph look deliberate.

The recipient was drawn from a pool that included the custodian without excluding them, so
one email in thirteen was a person writing to themselves. A self edge carries no relationship
and production has to special-case it.

And CC went multi-value under Rule 20 while To never did, so **the semicolon path in the To
column was never exercised by any tier**. That is the path an importer is most likely to get
wrong, which makes it the one worth having in the data.

### What it requires

- **Direction is made by swapping, never by rewriting.** An inbound email exchanges the From
  pair with the first To pair. The two people on the document do not change and neither does
  any address count, because the entity census in Rule 20 counts all four address fields
  rather than the To column alone. Only the arrow moves. Rewriting a participant would
  falsify Rule 20's counts and Rule 18's findings; a swap cannot, by construction.
- **`Custodian` is left alone on a flipped document.** The mail is in that custodian's mailbox
  because they received it, which is the ordinary case.
- **Extra To recipients come from the custodian roster only.** An external here would move a
  Rule 20 singleton off the singleton tail, and that tail is an asserted number in
  `entities.json`.
- **Protected documents are skipped**, the same set the edge cases honour: anything carrying a
  planted finding, a PI instance, a second language or a Rule 20 entity rewrite. A swap
  preserves counts, but Rule 18 asserts correspondence it describes in prose, and prose has a
  direction in it. Those documents are why a handful of self-addressed emails survive.
- Between a quarter and three quarters of email arrives rather than departs. Real collections
  run further toward inbound than that, but the custodians are the narrative's authors: push
  it past half and the planted story stops being told by the people it is about.

Applied after generation on its own RNG stream. Turn it off with `--no-direction`.

Verify with:

```bash
python scripts/validate_mock_data.py --tier medium
```

---

## Applying These Rules

To regenerate any tier with these rules enforced:

```bash
python scripts/generate_mock_metadata.py --tier small
python scripts/generate_mock_metadata.py --tier medium
python scripts/generate_mock_metadata.py --tier large
python scripts/generate_mock_metadata.py --tier xlarge
```

The extra large tier takes about two minutes and writes a 260 MB `documents.csv`, so it is
published as a release artifact rather than committed. `make mock-xlarge` pulls it.

Rules 16, 17 and 18 are on by default. To turn one off, or to change what it seeds:

```bash
python scripts/generate_mock_metadata.py --tier small --ssn-range 666
python scripts/generate_mock_metadata.py --tier small --second-language-share 0.008
python scripts/generate_mock_metadata.py --tier small --no-pi --no-language-mix --no-findings --no-entities --no-sources --no-shape
```

With all three off the output is byte-identical to v1.12.0, so a tier used as clean
fixture data stays clean fixture data.

To verify a dataset conforms to these rules:

```python
import pandas as pd

docs = pd.read_csv("mock-data/small/documents.csv")

# Rule 2: verify dedup method matches file type
assert all(docs[docs["File Type Category"] == "Email"]["Dedup Method"] == "MD5")
assert all(docs[docs["File Type Category"].str.contains("RSMF")]["Dedup Method"] == "EventCollectionId")

# Rule 7: verify TAR score bimodality
review = docs[docs["TAR Score"] != ""].copy()
review["TAR Score"] = review["TAR Score"].astype(float)
low  = (review["TAR Score"] < 20).mean()
high = (review["TAR Score"] > 75).mean()
assert 0.30 < low  < 0.50, f"Low band should be ~40%, got {low:.0%}"
assert 0.25 < high < 0.45, f"High band should be ~35%, got {high:.0%}"

# Rule 4: ICS records should have blank Date Sent
ics = docs[docs["File Extension"] == "ics"]
assert ics["Date Sent"].isna().all() or (ics["Date Sent"] == "").all()

# Rule 3: containers should not be leaf docs
containers = docs[docs["File Type Category"].isin(["PST", "MBOX", "ZIP"])]
assert all(containers["Level"].astype(str) == "0")
```
