# Changelog

All notable changes to this repository are documented here.

---

## [Unreleased]

### Fixed — Rules that were not being enforced

An audit of `validate_mock_data.py` against RULES.md found most rules were checking far less
than they claimed. The validator went from **28 checks to 62**, and two real data problems fell
out of it.

- **Containers referenced nothing.** RULES.md Rule 3 requires children to carry `Container Name`
  and `Container ID`. All 1,439 small-tier documents had both fields **empty**, so the 16
  container records were isolated rows nothing pointed at. The validator only ever checked the
  parents. The generator now links 3–8 children per container from the same custodian, and Rule
  3 checks that every `Container ID` resolves, every container has a child, and children carry
  the name and Level 1.

- **Rule 6's error counts were fiction.** The table specified 15 errored documents for the small
  tier; the generator produces 118, with types the table lists as zero. Nothing enforced it
  because the check only asked for "2 or more distinct types". The 1% the table implied is also
  low for a real matter. Rule 6 is now a **rate band, 5–12%, with at least 6 distinct types**,
  plus a requirement that 75% of error documents actually reach
  `Workflow Stage = Pre-Review: Processing Error`.

- **Rule 1** checked only that email was 45–65% and that containers and ICS existed. It now
  checks the share of every file type family and the count of distinct categories.
- **Rule 2** checked that the flag *columns* existed, and two dedup values. It now asserts 13
  values from the Rule 2 table across file type families.
- **Rule 9** never checked that documents named in `email-families.json` exist. Family records
  can now be caught pointing at absent documents; deliberate ones declared in `edge-cases.json`
  are excused.
- **Rule 10** checked that privileged documents have no Bates. It now also checks that only
  Responsive documents have them, that redacted documents carry them, and that they are unique.

### Fixed — bugs found while doing the above

- `password_zip` staged its payload beside the output file, so on a `.txt` row the payload and
  the archive resolved to the same path and `zip` exited 12, failing the build.
  `scripts/test_error_scenarios.py` now drives all 315 scenario/extension combinations and runs
  in CI, so that class of bug fails in a test rather than mid-build.
- Edge cases could rewrite a container's file type, leaving its children pointing at a record
  that was no longer a container. Container records are now excluded from the edge-case pool.
- Edge cases could delete a scripted HOT document via `broken_family`. They are now protected.

### Changed

- CI also runs the error scenario matrix and generates plus validates an edge-case tier.
- `mock-data/small/` regenerated with container linkage.

### Added — Edge cases: documents that starve a feature

- **`--edge-cases` on `generate_mock_metadata.py`.** Rule 12 covers files that fail processing.
  This covers the more dangerous case: documents that process perfectly and still leave a
  feature with nothing to work with. The generated tiers were uniform to a fault, every document
  carrying a custodian, a date, extracted text and `Language = English`, so any feature that
  aggregates over a collection had only ever seen a complete input.

  Twelve scenarios, each drawn from a disjoint pool so no document carries two faults: no
  custodian, no date, sentinel dates (1601, 1970, 2099), no extracted text, non-English, mixed
  language, blank recipients, distribution-list-only recipients, orphan attachments, families
  naming an absent document, duplicate MD5 across custodians, and audio/video with no text.

- **`edge-cases.json`** in any tier that has them: per scenario, what it starves, the count, and
  the document list. The counterpart to `EXPECTED_ERRORS.csv`.

- **RULES.md Rule 13**, and Rule 13 checks in `validate_mock_data.py` that probe every listed
  document and fail if one is not actually starved, so the report cannot drift from the data.

- `make mock-small-edge`. `make load-small-errors` now builds from the edge-case tier, so the
  errored package carries both kinds of problem.

### Changed

- Documents with no custodian land in `natives/_Unassigned/` and get their own row in
  `custodian-sources.csv`.

**Off by default.** Edge cases run on a separate RNG stream after generation, so default output
stays byte-identical and the committed tiers plus the CI determinism check are unaffected.

### Added — Pre-built errored package

- **`load-packages/small-errors.zip`**, published alongside the clean package rather than
  replacing it. Same 1,439 documents, 106 natives that genuinely fail processing, plus
  `EXPECTED_ERRORS.csv`. `load-packages/small.zip` stays clean, so nobody pulling fixture data
  gets broken files by accident.

  ```bash
  dvc get https://github.com/nickmanoogian/oioda-registry load-packages/small-errors.zip
  ```

### Fixed

- **The health check failed on every release-prep PR.** A PR that repoints a `.dvc` file at a
  new release tag always 404s during review, because the assets only exist once the release is
  published. `verify_urls.py` now distinguishes the two cases: if the release tag itself does
  not resolve, the pointer is reported as PENDING; if the tag exists and the asset is missing,
  that is still a hard failure. Pending is tolerated on `pull_request` runs and on
  `--allow-pending`, and fails everywhere else, so a pointer that reaches main without its
  release being published is still caught by the weekly run.
- `make load-small-errors` wrote into `load-packages/small/`, overwriting the clean package with
  an errored build. It now writes to `load-packages/small-errors/`. `make load-validate` checks
  both when both exist.

### Added — Errored files for failure path testing

- **`--with-errors` fabricates natives that genuinely fail processing.** Rule 6 has always
  specified a processing error distribution and the generator has always honoured it: 118 of
  the 1,439 small-tier documents carry `Processing Status = Error`. The natives behind those
  rows were healthy files, so importing the package and running Processing produced zero
  errors. A row flagged "Password Protected" sat on a 672-byte plain `.eml`.

  Nine scenarios, keyed off `Processing Error Type` so the metadata drives the fabrication:
  encrypted PDF, password protected container, truncation, header corruption, OOXML with its
  main part removed, nested containers, malformed RSMF JSON, text-free PDF, unsupported format
  stubs with real magic bytes, and zero-byte files. 106 files in the small tier.

- **`--error-rate`** promotes extra documents to errors using the mix already present, for
  exercising the failure paths harder than production ever would.

- **`EXPECTED_ERRORS.csv`** in every errored package: control number, custodian, native file,
  scenario, how it was built, expected Relativity error, whether that outcome is guaranteed,
  and the caveat when it is not. Testers diff it against the processing error report.

- **RULES.md Rule 12 — Native Layer Error Fidelity.** A document flagged as an error must have
  a file that actually errors.

- Rule 12 checks in `scripts/validate_load_package.py`: every fabricated native exists and
  matches its scenario's signature, `File Size` in the load file matches bytes on disk, and
  anything flagged but not fabricated is a documented exclusion rather than a silent gap.

### Changed

- `Processing Status` and `Processing Error Type` are now columns in `load-file.dat`. They were
  modelled in `documents.csv` and dropped entirely at the load file boundary.
- `File Size` in the load file is written from the bytes actually on disk. It previously carried
  the metadata's figure, which described a file that was never created.
- The generator's exception fallback no longer rescues a deliberately broken file by writing a
  valid `.txt` in its place.

### Not covered

- MIP protected rows are not fabricated: applying a sensitivity label needs a real Microsoft 365
  tenant. Their natives stay healthy and the build reports it.
- Malware, EICAR strings and zip bombs are out of scope.
- OCR failure, container timeout and conversion errors depend on engine and worker
  configuration. Those rows are marked `Guaranteed = no`.

### Added — Custodian folders in load packages

- **Natives are written into one folder per custodian**, mirroring the `Processing Folder Path`
  column instead of landing flat in a single directory. `natives/Michael_Brennan/2014/01/DOC-0000318.docx`
  rather than `natives/DOC-0000318.docx`. The metadata described this hierarchy all along (191
  distinct paths in the small tier); only the CSV knew about it.

  This is what makes a package consumable as raw data. A Relativity processing set assigns
  custodians per data source, so a flat folder yields one custodian for the whole collection or
  a manual sort. One folder per custodian yields a data source each.

- **`custodian-sources.csv`** in every package: name, email, org, department, data source
  folder, document count, natives written, total bytes. The setup sheet for building the
  processing set.

- **`scripts/validate_load_package.py`** and `make load-validate`: checks a built package
  against the new RULES.md Rule 11. Every `NativeFilePath` resolves, paths use backslashes,
  nothing loose at the root of `natives/`, folder matches the row's custodian, and
  `custodian-sources.csv` agrees with what is on disk.

- **RULES.md Rule 11 — Custodian Folder Structure.** Rules 1 through 10 govern the metadata;
  Rule 11 governs the package on disk.

- `--flat` on `build_load_package.py` preserves the old single-directory layout. The generated
  `IMPORT_README.txt` states that it cannot support per-custodian data sources.

### Changed

- `IMPORT_README.txt` now documents two paths: **PATH A** processes the package as raw data with
  one data source per custodian, **PATH B** is the existing load file import. It also lists the
  custodian folders and their document counts.
- `NativeFilePath` in `load-file.dat` now uses backslash separators, which is what the load file
  format and the README always claimed. It was emitting forward slashes on macOS builds.

## [v1.6.0] — 2026-06-26

### Fixed

- **S3 health check was silently checking zero DVC-tracked URLs.** The workflow's parser matched lines starting with `path: https://`, but `.dvc` files write dependencies as YAML list items (`- path: https://...`), so only the three hardcoded release URLs were ever tested. All 37 URLs are now checked.
- **Mock data regeneration is now deterministic.** RSMF participant lists were joined via `set()`, whose iteration order varies between Python runs, so every `make mock-regen-small` produced a spurious diff. Two consecutive regenerations are now byte-identical.

### Changed

- URL checking consolidated into `scripts/verify_urls.py`, shared by `make verify` and the health-check workflow. `make verify` now covers `metadata/`, `samples/`, `load-packages/`, and the root manifest in addition to `data-products/`.
- The health check also runs on pull requests that touch `.dvc` files.

### Added

- **Real OIDA export for ECI** — `scripts/export_insys_documents.py` reads `oida-index.parquet` (`collection = 'Insys Litigation Documents'`) and emits **all 1,633,778 docs** with real Relativity *processing*-field metadata only (custodian, email `From/To/CC` from `au`/`rc`/`cc`, dates, file type/size/MD5/media type, page count, redaction, Bates, mentioned) plus a deterministic **`OCR Text URL`** per doc (`id`→`…/t/h/k/d/<id>/<id>.ocr`, verified) so real Extracted Text is fetched on demand rather than baking ~112 GB into the file. `custodians.json` = every real collected custodian (111) + real doc count. No cap, no sampling, no synthetic values — unlike `generate_mock_metadata.py`, which fabricates everything. Review/analytics fields (Responsiveness, Privilege, Issue Tags, Batches, TAR/AL) are intentionally omitted: they're created in Relativity during review, not present in a raw archive.
- `validate.yml` CI workflow: every PR runs small-tier validation against RULES.md and a regeneration-determinism check (regenerates the small tier and fails if the output differs from the committed files).

---

## [v1.5.0] — 2026-06-05

### Added — Pre-built small tier load package

The small tier load package is now accessible via DVC without a build step:

```bash
dvc get https://github.com/nickmanoogian/oioda-registry load-packages/small.zip
unzip small.zip
```

`load-packages/small.zip.dvc` added as a pointer to the v1.5.0 release artifact (9 MB compressed). Contains ~1,423 native files + `load-file.dat` + `IMPORT_README.txt`.

---

## [v1.4.1] — 2026-06-04

### Changed — DRY cleanup across all scripts

- `fetch_manifest.py`: pre-compute XML namespace tag names outside loop; `urlencode` for URL building; `PROGRESS_INTERVAL` constant
- `validate_mock_data.py`: pre-filter doc slices once at top instead of 10+ full-list scans; dict-based JSON loading; `EMAIL_TYPES` / `CONTAINER_TYPES` sets; Rules 7 and 8 collapsed to loops; cleaner GPS predicate
- `generate_mock_metadata.py`: `ORG_COMPANY_NAME` constant replaces inline dict literal; `bates_n` computed from `ORG_BATES_PREFIX.values()` (single source of truth); unused `n_redacted` removed; O(1) doc lookup in `find_or_stub` via pre-built dict
- `build_load_package.py`: 50-branch `if/elif` in `doc_to_dat_row` replaced with declarative `_COLUMN_MAP` dict; `build_family_index` simplified

---

## [v1.4.0] — 2026-06-04

### Added — Native file load package generator (Mode B)

`scripts/build_load_package.py` generates actual native files and a Relativity
`.dat` / `.opt` load file ready for workspace import.

```bash
pip install python-docx openpyxl python-pptx fpdf2
python scripts/build_load_package.py --tier small           # OIDA OCR content
python scripts/build_load_package.py --tier small --no-oida # synthetic content
make load-small
```

Output: `load-packages/{tier}/natives/` + `load-file.dat` + `IMPORT_README.txt`

- Generates .eml, .docx, .xlsx, .pptx, .pdf, .rsmf, .txt native files
- Scripted hot documents (HOT- prefix) get hand-crafted MDL 2804 content
- All other documents use real OIDA OCR content from the S3 archive (or synthetic if `--no-oida`)
- 53-field Relativity Concordance .dat with all metadata, Bates numbers, TAR scores, issue tags
- `IMPORT_README.txt` with step-by-step Relativity import instructions
- `make load-small`, `load-medium`, `load-large` targets in Makefile

---

## [v1.3.0] — 2026-06-04

### Changed — MDL 2804 narrative rebuild (breaking for existing mock data users)

The mock data generator was completely rebuilt around a real litigation narrative:
**MDL 2804, the National Prescription Opiate Litigation**.

If you pulled mock data from v1.1.0 or v1.2.0, re-pull. The datasets are substantially different.

**What changed:**
- Custodians now span three organizations: Mallinckrodt, Insys Therapeutics, and McKinsey & Co — the actual MDL defendants
- 4 story phases with distinct document subjects, responsiveness rates, and issue tags: Growth (2010–12), Pressure (2013–14), Crisis (2015–16), Litigation (2017–18)
- 13 scripted hot documents named after real evidentiary moments in the case (SOM override memo, McKinsey turbocharge deck, IRC call guide, whistleblower email, legal hold notice, SOM deletion log, AG subpoena draft)
- 5 scripted email threads showing the decision chain (override chain, McKinsey engagement, Insys speaker bureau, whistleblower/hold thread, DEA response thread)
- Phase-aware responsiveness: 12% → 40% → 55% → 35% across phases
- Phase-aware privilege: 2% → 8% → 15% → 25% across phases
- Issue tag matrix by (org, phase): SOM Override, Speaker Bureau Payments, DEA Correspondence, Prior Auth Fraud, McKinsey Strategy, Legal Hold, Whistleblower, State AG Investigation
- Org-specific Bates prefixes: MNK (Mallinckrodt), INSYS, MCK, OC (Outside Counsel)

**New columns in documents.csv:**
- `Custodian Org` — Mallinckrodt / Insys / McKinsey / Outside Counsel
- `Narrative Phase` — 1 / 2 / 3 / 4
- `Narrative Phase Name` — Growth / Pressure / Crisis / Litigation
- `Bates Prefix` — org-specific prefix

**New files:**
- `mock-data/DEMO_GUIDE.md` — how to walk through the dataset in a Relativity demo
- `scripts/validate_mock_data.py` — verify a dataset conforms to RULES.md

---

## [v1.2.0] — 2026-06-03

### Changed — File type rules enforcement

Rebuilt generator to enforce all 10 rules in `mock-data/RULES.md`:
- 30+ distinct file types (not just "Email" and "PDF")
- ICS records with blank `Date Sent` / `Date Received`
- HEIC/JPEG with GPS EXIF on 15% of mobile images
- Google Workspace with `GoogleDrive/` fields
- Bloomberg XML in large tier
- RSMF `HasPlaceholders = Yes` on Teams records
- Container records at `Level = 0`
- Correct `Dedup Method` per file type (MD5 / SHA256 / EventCollectionId)
- Workflow behavior flags on every row

**New files:**
- `mock-data/RULES.md` — canonical rules document (10 rules with rationale)

---

## [v1.1.0] — 2026-06-03

### Added — Initial mock data tiers

First version of pre-generated Relativity workspace metadata:
- Small tier (~1,500 docs) committed to git
- Medium (~10,000 docs) and large (~150,000 docs) as release artifacts
- `scripts/generate_mock_metadata.py` — generator script
- `mock-data/README.md` — usage documentation

---

## [v1.0.0] — 2026-06-03

### Added — Initial registry

- DVC pointer files for all 16 structured datasets in `data-products/`
- `metadata/` Parquet index files
- `samples/` bulk download sample
- `manifest.tsv.gz` — full archive listing (22.3M files, 7.5 TB)
- `scripts/download.py` — direct downloader (no DVC required)
- `scripts/fetch_manifest.py` — manifest regeneration
- `data-products/SCHEMA.md` — column descriptions for all CSVs
- `.github/workflows/health-check.yml` — weekly S3 URL validation
- `Makefile` — convenience targets
