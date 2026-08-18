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
- `Has Natives` = No for PST/MBOX containers themselves
- Password-protected containers get `Processing Status` = "Error", `Processing Error Type` = "Password Protected"
- ZIP children have unreliable date fields — `Date Created`/`Date Modified` may be blank or wrong due to missing time zone info in ZIP format

**Per-tier container counts:**

| Tier | PST/MBOX parents | ZIPs (as containers) |
|------|-----------------|---------------------|
| Small | 8 | 5–10 |
| Medium | 40 | 20–40 |
| Large | 400 | 200+ |

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

| Error Type | Small | Medium | Large |
|------------|-------|--------|-------|
| Password Protected (PST/ZIP) | 2 | 8 | 80 |
| Password Protected (Office doc) | 3 | 15 | 150 |
| Corrupt / Unreadable | 3 | 20 | 200 |
| Unsupported File Type | 4 | 30 | 400 |
| MIP Protected | 1 | 5 | 40 |
| OCR Failure (scanned PDF) | 1 | 10 | 200 |
| Container Extraction Timeout | 1 | 5 | 80 |
| Teams/Slack Conversion Error | 0 | 7 | 150 |
| Extraction Failure (large container) | 0 | 5 | 200 |

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
  Michael_Brennan/2014/01/DOC-0000318.docx
  Thomas_Bradley/2013/11/DOC-0000229.eml
  ...
```

The reason is Relativity Processing: a processing set assigns custodians **per data source**.
One flat folder means one data source, and therefore one custodian for the entire collection,
or manual sorting. One folder per custodian means one data source each, with custodian
assignment falling out of the structure.

Requirements:

- Every native lives under the path its `Processing Folder Path` describes. No files at the
  root of `natives/`.
- `NativeFilePath` in the load file is the package-relative path in backslash form, e.g.
  `natives\Michael_Brennan\2014\01\DOC-0000318.docx`.
- Every package ships `custodian-sources.csv`: one row per custodian with name, email, org,
  department, data source folder, document count, natives written and total bytes. This is the
  sheet whoever builds the processing set works down.
- Documents with no custodian go under `_Unassigned/`, and only when a build deliberately asks
  for them. The default build assigns every document to a custodian.

A flat layout is available via `--flat` for anyone who wants the old shape, but it cannot
support per-custodian data sources and the generated `IMPORT_README.txt` says so.

Verify a built package with:

```bash
python scripts/validate_load_package.py load-packages/small
```

---

## Applying These Rules

To regenerate any tier with these rules enforced:

```bash
python scripts/generate_mock_metadata.py --tier small
python scripts/generate_mock_metadata.py --tier medium
python scripts/generate_mock_metadata.py --tier large
```

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
