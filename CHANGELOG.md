# Changelog

All notable changes to this repository are documented here.

---

## [Unreleased]

### Removed — a stray nested load package, 1,426 files tracked in git

`load-packages/load-packages/small/` was committed by accident in d7e464c, the repository
rename: the unzip ran from inside `load-packages/`, and the archive carries its own
`load-packages/` prefix, so the whole extracted package landed one level too deep. It came
in with 1,570 other files and nobody noticed.

It was stale as well as misplaced. All 1,414 natives sat directly under `natives/` in the
old flat layout, with none in custodian folders, so anyone who found it got a package that
Rule 11 has not produced since August. It also carried a `load-file.opt` placeholder from
before the native-only import path.

Nothing referenced it: `.gitignore` already covered `/load-packages/small/` and
`/load-packages/*.zip`, the `small.zip.dvc` and `small-errors.zip.dvc` pointers import the
release assets, and the README tells you to `dvc get` the zips. The path is ignored now, so
the same slip cannot re-add it.

`load-packages/small-real/` stays tracked. Those 122 files are real OIDA PDFs rather than
generated output, so they are not reproducible from a `make` target.

### Fixed — the published medium and large tiers were ten releases out of date

`make mock-medium` and `make mock-large` resolved to the **v1.3.0** assets. Those files
predate the custodian folder structure, the real attachment records, `Record Type`, the
seeded PI, the second language, the planted findings and the native date layer. The
pointers were internally consistent (a URL and a byte count that agreed with each other),
so nothing caught it.

**v1.14.0 publishes every tier from the current generator**, and each tier now ships seven
files rather than four. The three additions are the ground truth for the seeded content,
without which the PI, the second language and the planted findings sit in the data with
nothing to score them against:

| Tier | Documents | Pointers |
|---|---|---|
| Medium | 9,980 | 7, all at v1.14.0 |
| Large | 148,235 | 7, all at v1.14.0 |
| Extra large | 275,273 | 7, all at v1.14.0 |

The extra large tier is **published now** rather than generate-on-demand: 59 MB gzipped is
cheaper than asking everyone to spend two minutes and 260 MB of disk. `make mock-xlarge`.

The two load packages are unchanged from v1.13.0 and re-attached to v1.14.0, because the
click-to-download links use `releases/latest/download/…` and would otherwise have broken
the moment a newer release existed.

### Fixed — `.gitignore` was swallowing the pointers it needed to keep

`/mock-data/medium/` and its siblings excluded the whole directory, and git cannot
re-include a file whose parent directory is excluded. So the four pointers that predated
the rule stayed tracked while thirteen new ones were silently ignored, and a pointer that
is not committed is a `make mock-*` target that cannot resolve. The patterns exclude the
directory *contents* now, with a negation for `*.dvc`, which is the form that works. The
data files themselves stay ignored, which is checked in both directions.

### Added — `scripts/write_dvc_pointers.py`

Writes every `mock-data/*.dvc` pointer from the files being published, so the URL, the byte
count and the tier they describe cannot disagree. The pointers were hand maintained, which
is how they drifted ten versions. `--check` reports without writing.

Verified: all 21 pointers resolve against the live release with a content length matching
the pointer, and both `releases/latest/download/…` links still serve the same bytes as
v1.13.0.

### Added — an extra large tier (~275,000 documents)

`--tier xlarge`: 275,273 documents, above a quarter of a million, for scale and
performance work past what the large tier reaches.

| | Large | Extra large |
|---|---|---|
| Documents | 148,235 | 275,273 |
| Sent to review | 56,344 | 104,618 |
| Responsive | 14,434 | 26,653 |
| Privileged | 1,991 | 3,654 |
| PI instances | 3,326 | 6,048 |
| Productions | 4 | 6 |
| Custodians | 40 | 40, the same roster |
| `documents.csv` | 130 MB | 260 MB |

It is **large's matter at 1.86x**, not a second story: `NARRATIVE_PARENT` points xlarge at
large, so the two share one custodian roster, one set of scripted hot documents and one
set of scripted threads. Only the volumes, the production count and the reviewer pool are
its own. Every file type share stays inside the band the validator checks.

Generated on demand rather than published, because two minutes of generation costs less
than shipping 260 MB:

```bash
make mock-regen-xlarge
```

`make load-xlarge` builds a load package from it.

### Fixed — three defects the new tier's scale exposed

- **`broken_family` removed documents that other records pointed at.** It is the only
  edge-case scenario that deletes rather than degrades, and it excused scripted documents
  but nothing else. At the small tier it removes five documents and rarely collided; at
  275,000 it removes a thousand, which orphaned 602 attachments and deleted 7 documents
  that `pi-ground-truth.csv` named. It now skips any document that is itself a parent, and
  any document the seeded content claims.
- **`Record Type` typed a scripted thread member as an attachment.** HOT-0000002, the deck
  Tevelow sent as the third message of STHR-0002, has a `Parent Document ID` from the
  thread structure rather than an attachment relationship. Typing it `Attachment` required
  it to carry Whitfield's custodian to satisfy Rule 15, and inflated a parent that claims
  no attachments. `validate_mock_data.py --tier medium` and `--tier large` both failed on
  it; both pass now.
- **The short message share band contradicted Rule 1.** `FAMILY_SHARE` capped RSMF at 6%
  of any tier while Rule 1's own tables specify roughly 2% for small, 6.5% for medium and
  12.7% for large. Medium failed at 6.4% and large at 12.6%, both correct against the
  rule. The band is per tier now, and Rule 1 states the progression explicitly.

### Fixed — two checks that only ever failed a partial package

- **`--limit` copied the tier's full ground truth into a package holding a slice of it.**
  A 400 document build of xlarge shipped manifests naming 7,908 seeded documents, 6,045 of
  which were not in the package. The manifests are filtered to what the package actually
  contains, and the build says so.
- **The PI distribution claim moved to the tier validator.** "Seeded PI spans at least four
  places" is a property of the tier, not of a package, and asserting it against a slice
  only ever failed the slice. `validate_mock_data.py` still checks it; the package
  validator prints what it found.

### Fixed — the Rule 17 share check double counted on an edge tier

Rule 13's `non_english` scenario hands out German, Polish and Spanish at random, and the
Rule 17 check counted those against its requested share. It counts the documents Rule 17
actually seeded now, which is the claim the report makes.

### Fixed — tier counts in the docs were estimates, and several had drifted

The tier tables carried round numbers from earlier versions. Medium and large were
regenerated and measured, and the values that were wrong are now the measured ones: medium
is 9,980 documents rather than ~9,900 and sends 4,002 to review rather than ~3,600; large
sends 56,344 rather than ~36,000 and has 14,434 responsive rather than ~13,000. The small
tier's custodian split was listed as 7 Mallinckrodt when it is 8. The PI counts introduced
in this release were themselves estimates for medium and large; they are 443 and 3,326.

### Changed — v1.13.0 packages

Republished. Every native in the v1.12.0 assets was stamped with a library's date rather than
the manifest's, so a processing run of the download put every spreadsheet and every PDF in
August 2026 and every deck in January 2013. Both packages also now carry the seeded content
and its ground truth.

| | v1.12.0 | v1.13.0 |
|---|---|---|
| Office and PDF dates | the build clock, or a 2013 template | the row's `Date Created` / `Date Last Modified` |
| Filesystem mtimes | the build clock | the row's `Date Last Modified` |
| `load-file.dat` fields | 56 | 58 (`Date Created`, `Date Last Modified`) |
| PI instances | none | 102 across 18 documents, in `pi-ground-truth.csv` |
| Languages | English only | + German 2.0%, in `language-mix.json` |
| Planted findings | none | 4, in `findings.json` |
| Fabricated errors | 100 | 102 |
| Starved documents | 210 | 221 |

Built and zipped with `make load-release`, which validates before it packages. The previous
assets were assembled by hand, which is how the date defect reached a published artifact
without anything failing.

### Fixed — every native carried a library's date, not the manifest's (Rule 19)

python-docx, python-pptx, openpyxl and fpdf2 each stamp their own date on every file they
write, and those stamps are what Relativity reads at processing time. The `.dat` carried no
`Date Created` column to override them, so the leak landed straight in Collection Coverage.

Measured on `load-packages/small-load-package.zip` as shipped in v1.12.0:

| | Before | After |
|---|---|---|
| `.xlsx` core properties | created and modified `2026-08-19`, creator `openpyxl` | the row's `Date Created` and `Date Last Modified` |
| `.pdf` `CreationDate` | `2026-08-19` | the row's `Date Created` |
| `.pptx` core properties | created `2013-01-27`, `lastModifiedBy` "Steve Canny", on every file | the row's dates, the custodian as author |
| `.docx` modified | `2013-12-23`, python-docx's template default, preceding its own created date | the row's `Date Last Modified` |
| filesystem mtimes | the build clock | the row's `Date Last Modified` |
| `.dat` date columns | `Date`, `Date Sent`, `Date Received` | + `Date Created`, `Date Last Modified` |

299 of 448 Office and PDF natives carried a date outside the matter window, 403 carried a
library's name in their document properties, and all 448 mtimes were adrift. openpyxl needed
`ExcelWriter` directly, because `save_workbook` overwrites `properties.modified` with the
clock on the line before it writes.

`validate_load_package.py` now asserts all of it, and fails on the v1.12.0 package.

### Added — PI, a second language, and known-answer findings (Rules 16, 17, 18)

Two of the six Early Insights widgets had nothing to work with. `Language` was `English` on
all 1,439 rows of the small tier, and there was no personal information anywhere in the
repository, so PI Detect could only be tested by starving it.

| Rule | Seeds | Ground truth |
|---|---|---|
| **16** PI | 102 instances across 18 documents in the small tier: email bodies (the harder catch), a roster's cells, a PDF form, a chat, and one high-sensitivity document with nothing to do with the matter | `pi-ground-truth.csv`, one row per instance |
| **17** Language | German at 2.0%, on facilities notices deliberately unrelated to the matter, with real prose in the natives. Medium adds Polish, large adds Spanish | `language-mix.json` |
| **18** Findings | a matched pair, a decoy and an extraction-depth case: metadata-only, content-only, an innocent lookalike whose distinguisher is buried in a second record, and a workbook whose payload sits on tab 11 of 12 | `findings.json` |

Every PI value is non-issuable: SSN areas the SSA has never issued, published test card
numbers, the `555-01xx` fiction block, the `.invalid` TLD. `--ssn-range 666` switches to the
other never-allocated area, because the 9xx block is exactly what some detectors score as low
confidence, which makes a widget look like it is under-reporting when it is not.

The native text is rendered *from* the ground truth rather than beside it, so the two cannot
drift, and `validate_load_package.py` confirms every seeded value is really in the file that
claims it, decoding base64 email bodies, OOXML zips and compressed PDF streams to do it.

**On by default**, unlike the edge cases: a pass that feeds a widget belongs in the tier, and
a pass that starves one has to be asked for. `--no-pi --no-language-mix --no-findings`
reproduces the v1.12.0 output byte for byte.

### Fixed — two ways a build could quietly produce a wrong package

- **Building over an older package left its files behind.** `natives/` was created with
  `exist_ok=True` and never cleared, so a rebuild mixed two generations: the custodian sheet
  and the load file described the new build while the folder held both. Found by
  `validate_load_package.py`, which reported 1,543 files on disk against 1,418 in the sheet.
  The builder now clears the tree it owns and says how many stale files it removed.
- **`oversized_text` could land on a document flagged as a processing error.** Rule 12's
  Corrupt File scenario truncates a native to 40% of its bytes, so a document claiming
  800,000 words held 319,998. The native is that scenario's whole contract, so it now draws
  only from documents with no error flag.

### Added — `make load-release`

Builds both packages, validates them, and zips the release assets. They were assembled by
hand, which is how the date defect above reached a published artifact without anything
failing.

### Added — a widget coverage table, and an intake form

`mock-data/README.md` now opens with what each of the six widgets can be tested against, and
where the tiers still fall short: 15 distinct addresses so the 25-entity production cap cannot
be reached, no person using two addresses, no `Data Source` dimension, no planted collection
gap. `docs/REQUEST_TEMPLATE.md` is the intake form, mapping each common ask to the flag that
already serves it and listing what is not modelled.

The catalogue was indexed by volume. Nobody asks for 9,900 documents at 52% email; they ask
whether a dataset can exercise the thing they are building.

### Changed — v1.12.0 packages

Republished with the attachment records. The v1.11.0 artifacts had no `Attachment` rows at all,
so nothing that rolls up a family by attachment record could be tested against the download.

| | v1.11.0 | v1.12.0 |
|---|---|---|
| `Record Type` values | Email / EDoc / Container | + **Attachment** |
| Attachments | none | 304 across 129 emails |
| Starved documents | 195 | 210 |

### Added — typecheck in the gate

The last piece of eci-ui's `check:circular-deps`. I had assumed mypy over 5,000 untyped lines
would mean scattering `# type: ignore`; in default mode with `--ignore-missing-imports` it found
**eleven errors**, all of them real, and all now fixed:

- `fetch_manifest.py` called `element.find(tag).text` in five places. `find` returns `None` for a
  missing child, so the manifest rebuild raised `AttributeError` the first time S3 returned a
  listing without one of those tags. Now goes through a `_text` helper.
- `export_insys_documents.py` unpacked the result of `fetchone()` without checking for `None`.
- `download.py`'s `human_size` declared `n: int` and then divided it into a float.
- Two containers needed annotations the checker could not infer from an empty literal.

`make check` is now lint → typecheck → import cycles → validators → scenario matrix →
determinism, which is the full shape of the production gate.

### Added — attachments are real documents now (Rule 15)

`Has Attachments` and `Attachment Count` were rolled at random and backed by nothing. No
attachment existed as its own document, so `Record Type` never took the value `Attachment` and
nothing that rolls up a family by attachment record could be tested.

Attachments are **re-parented from existing loose documents** rather than invented, so the tier
size and the Rule 1 shares are unchanged and the files are the ones attachments really are: Word,
Excel, PDF, images. The small tier now has **304 attachments across 129 emails (16% of email)**,
with 313 documents still loose.

Rule 15 requires the parent to resolve and to be an email, the attachment to share its parent's
custodian and date, and the claim to match reality in both directions.

Edge cases had to learn about families: they now move a family as a unit rather than blanking one
side's custodian, `broken_family` never removes an attachment, and `orphan_attachment` records
what it detached from so a planted orphan is distinguishable from a broken one.

**Two bugs found on the way:**

- `Has Attachments` and `Attachment Count` each rolled `random.random() < 0.35` **independently**,
  so an email could claim no attachments and a count of three, or the reverse. 178 documents
  disagreed with themselves. One roll now.
- The first pass let attachments consume 595 of 617 loose documents, leaving 22 standalone EDocs.
  Half of each custodian's pool is now reserved.

### Changed — v1.11.0 packages

Republished so the download matches what the generator now produces. The v1.10.0 artifacts had
**4 custodians and no `Record Type`**, which meant they could not exercise either of the things
the last two releases fixed: the top-25 pair cut, and the drill baseline column.

| | v1.10.0 | v1.11.0 |
|---|---|---|
| Custodians | 4 (6 pairs) | 10 (45 pairs) |
| Distribution | flat, ~10% each | weighted, 22.7% to 2.4% |
| `Record Type` | absent | Email / EDoc / Container |

### Added — one quality gate, borrowed from how eci-ui gates a PR

eci-ui's AGENTS.md is explicit: `npm run check:circular-deps` **must pass before raising a PR**,
and that one command is lint, typecheck, a madge import cycle check and the unit tests. This repo
had 4,954 lines of Python, five separate check commands a contributor had to know about, and no
static analysis at all.

`make check` is the equivalent: lint, import cycle check, RULES.md validators, error scenario
matrix, determinism. Ordered cheapest first so a typo fails in seconds rather than after a two
minute build. Documented in CONTRIBUTING as the thing to run before a PR, and CI runs the same
set plus the package builds.

**Lint (`ruff.toml`) found a real defect on the first run.** `RELATIVITY_FIELD_MAP` in
`build_load_package.py` was dead code that declared `"Control Number"` and `"Family ID"` twice
each, so half its entries were silently dropped at parse time. Also three unused imports, an
unused variable, and a bare `except` swallowing everything around a date parse. All fixed.

The selection is about defects, not taste. The full default set produced 62 findings and a wider
one 127, of which 110 were `E701`/`E702` one-statement-per-line — the house style throughout
`generate_mock_metadata.py`. Enforcing that would rewrite hundreds of lines and bury real changes
in noise, so it is off, with the reasoning recorded in `ruff.toml`.

**`scripts/check_imports.py`** is the madge equivalent: these scripts already import each other
(`build_load_package` and `validate_load_package` both pull in `error_natives`), so the same
failure mode was available. It parses the AST rather than importing, so a missing third-party
dependency cannot cause a false failure. No cycles across 14 modules today.

### Added — Record Type, from the production drill baseline

Checked the dataset against what the ECI drill actually renders
(`docs/widgets/cross-cutting-ux.md` in eci-ui). The universal baseline is Control Number,
Custodian, Primary Date/Time, **Record Type**, Unified Title, Topic (AI) and Summary (AI). The
AI columns are produced downstream, but Record Type is a collected field and this dataset did
not have it, so a drill built against it could not fill a column it always shows.

Every document now carries one: `Email` (806), `EDoc` (617), `Container` (16). It is in
`documents.csv` and in the load file. RULES.md Rule 14 and four validator checks enforce it;
the metadata validator is now at 66 checks.

**`Attachment` never occurs, and that is a real gap rather than an oversight.** Family children
here are thread replies, which are emails. `Has Attachments` is populated but no attachment is
materialised as its own document, so nothing that rolls up families by attachment record can be
tested against this data.

### Fixed — custodian count and distribution

Production caps Key Relationships at the top 25 pairs and top 25 non-custodian entities and tells
the user that pairs below the cut are not listed. The small tier had 4 custodians, so 6 internal
pairs, and could never reach that cut. It is now **10 custodians, 45 pairs**, about 150 documents
each, spanning Mallinckrodt, Insys and McKinsey. The six added came from the medium roster rather
than being invented, so the narrative holds and the people the scripted hot documents name are
actually custodians.

**`doc_target` was decorative.** It is declared on every custodian and was never read:
`random.choice` picked uniformly, so every tier came out flat at roughly 10% each. Real
collections are heavily skewed, and a flat one hides every bug that depends on one custodian
dominating. Assignment is now weighted by `doc_target`; the small tier runs 23% down to 2.4%.

### Fixed — two bugs the custodian change surfaced

Neither was reachable before the custodian mix shifted, and both were caught by the validators
rather than by review:

- `broken_family` could delete a document another edge scenario had already claimed, leaving that
  scenario's report naming a document absent from the set. Claimed documents are now off limits.
- A container flagged with a file-level error (`Has Natives = No`) has no file to break, so it
  could never be fabricated and showed up as an undocumented gap. It is now a documented
  exclusion alongside MIP.

### Changed — v1.10.0 packages

Both packages republished, which closes the two loose ends left by the rename and the oversized
text work:

- the errored package now carries the three oversized documents, and its encrypted artefacts use
  the post-rename password (`oida`), so the published artifact and the code finally agree
- the clean package is rebuilt from the same code

The published dataset now matches the catalogue completely: import failures, processing
failures, and documents that process cleanly with something missing.

### Added — documents with more text than a model context holds

The last item from the original catalogue. Three documents carrying 300,000, 800,000 and
1,500,000 words, roughly 2 MB, 5 MB and 10 MB of extracted text. A 200k token context is
somewhere near 150k words, so all three are past it and the largest by an order of magnitude.

`Word Count` in the metadata is the contract: `build_load_package.py` writes a native holding
the number of words the row claims, so the two cannot disagree, and `validate_load_package.py`
counts the words on disk and fails if a native is short.

Two honest notes. The text is a cycled seed, which exercises a token limit properly and is
useless for topic modelling realism. And it compresses to nothing, so 16.7 MB of raw text leaves
the published zip at 9.8 MB.

This closes the "what is not in the dataset yet" list. Everything on it, no custodian, broken
families, orphan attachments, blank recipients, sentinel and missing dates, non-English, audio
and video, shipped in v1.9.1; oversized text was the only one outstanding.

### Changed — repository renamed to `oida-registry`

The archive is the **O**pioid **I**ndustry **D**ocuments **A**rchive, OIDA. The repository carried
an extra `o` from the start. Renamed to `nickmanoogian/oida-registry`, and every reference swept:
55 URLs across the README, CHANGELOG, Makefile, docs and the `.dvc` pointers, plus the
`/tmp/oida-large` export path and the health-check user agent, which carried the same typo.

GitHub redirects the old name indefinitely, so existing clones, `dvc get` calls and release asset
URLs keep working. All 38 URLs verify at the new name.

**One behaviour change came with it.** `PACKAGE_PASSWORD`, used for the encrypted artefacts in an
errored package, was `oioda` and is now `oida`. Every package documents its own password in
`IMPORT_README.txt`, so a tester reads it from the package rather than from the repo. The
published v1.9.1 artifact still uses `oioda`; anything built after this uses `oida`.

### Added — Load files that fail at import

The last gap from the 2026-08-18 standup. Everything in the repo broke during or after
processing; nothing broke at the import boundary, which is where Alex's "put in load files and
try to find all those gotchas" lands.

`scripts/build_broken_load_files.py` and `make load-broken` emit seven variants, one fault each:

| Variant | Fault |
|---|---|
| `missing-native` | `NativeFilePath` points at a file that is not in the package |
| `duplicate-control` | the same Control Number on three rows |
| `bad-date` | `13/45/2011`, and a non-numeric value, in a date field |
| `unqualified-delimiter` | a raw column separator inside a field value, so the row gains a column |
| `encoding` | Latin-1 bytes in a file read as UTF-8, no BOM |
| `short-row` | 49 fields against a 55 field header |
| `blank-required` | empty Control Number |

Only the `.dat` is written. Natives are not duplicated: every variant points at the same relative
paths as the clean package, so a tester drops one `.dat` in beside an unzipped `natives/` folder.
`manifest.csv` records each variant, the rows it affects by control number, and the expected
failure.

`--verify` asserts every variant carries the fault it claims, and runs in CI. A broken load file
that parses cleanly is the same trap as a healthy native behind an error flag.

**The clean package remains the default.** These variants are built locally, are opt in, and do
not modify any package. The README now states the three-way choice up front.

### Fixed — the edge-case manifest never shipped

`edge-cases.json` was written into the metadata tier and never copied into the load package, so
v1.9.0 shipped 190 starved documents with no map of which ones were deliberate. That is the same
hole `EXPECTED_ERRORS.csv` exists to close, and it made the starved documents nearly useless to a
tester: a missing custodian looks identical to a bug.

- `build_load_package.py` copies `edge-cases.json` into the package and adds a section to
  `IMPORT_README.txt` listing each scenario, its count, and what it starves.
- `validate_load_package.py` fails a package that has documents with no custodian but no
  manifest, and cross-checks the manifest against the load file when it is present. Confirmed
  against the v1.9.0 artifact, which fails.
- Republished as v1.9.1.

### Changed — v1.9.0 packages

Both published packages rebuilt so the downloadable artifacts match the code:

- `small-errors.zip` now carries **both** kinds of problem. It previously had only the fabricated
  processing failures; it now also carries the 190 starved documents from the edge-case tier
  (no custodian, no date, sentinel dates, no text, non-English, broken families, duplicate MD5,
  media with no text), plus `edge-cases.json`, and `_Unassigned` as a fifth data source.
- `small.zip` picks up the container linkage fix: 84 documents now carry a `Container ID` and
  `Container Name` that resolve to a real container record.

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
  dvc get https://github.com/nickmanoogian/oida-registry load-packages/small-errors.zip
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
dvc get https://github.com/nickmanoogian/oida-registry load-packages/small.zip
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
