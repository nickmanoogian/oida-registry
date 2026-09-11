# Requesting a Test Corpus

This is the intake form for a synthetic e-discovery corpus, and the map from each thing
people ask for to the thing this repo already does.

Read the second table first. Most of a request like this is a flag on an existing tier, not
a build from scratch, and the parts that are not are worth knowing before you start.

---

## What already exists

| What you would ask for | What serves it |
|---|---|
| A size, and a realistic file type mix | `--tier small\|medium\|large`, Rules 1 and 2 |
| Containers with real children | Rule 3, enforced: every `Container ID` resolves and every container has a child |
| Documents that fail processing, with a manifest | `--with-errors`, Rule 12, `EXPECTED_ERRORS.csv` |
| Documents that process cleanly and still starve a widget | `--edge-cases`, Rule 13, `edge-cases.json` |
| Personal information, distributed, all non-issuable | on by default, Rule 16, `pi-ground-truth.csv` |
| A second language slice, irrelevant to the matter | on by default, Rule 17, `language-mix.json` |
| Known-answer findings and a decoy | on by default, Rule 18, `findings.json` |
| Real dates on every native, not the library's | Rule 19, asserted by `validate_load_package.py` |
| Per-custodian folders and a data source sheet | Rule 11, `custodian-sources.csv` |
| Ground truth emitted at generation time | all of the above; nothing is reconstructed afterward |
| Build-time assertions that fail loudly | `make check`, `validate_mock_data.py`, `validate_load_package.py` |
| Fixed calendar dates, deterministic output | seed 42 by default; two runs are byte-identical |
| An entity population past the production cap of 25, with a real singleton tail | on by default, Rule 20, `entities.json`. 44 non-custodian entities in the small tier, 28 on one document |
| One person using two addresses, to test name normalisation | on by default, Rule 20. 2 aliased people in the small tier, up to 5 in the big ones |
| A size above a quarter of a million documents | `--tier xlarge`, 275,273 documents. `make mock-xlarge` pulls it |

## What does not exist yet

| What you would ask for | Status |
|---|---|
| A `Data Source` dimension: Exchange vs OneDrive vs a mobile extraction, with different metadata profiles per source | Not modelled. The data source axis is custodian (Rule 11). |
| Per-source folders with custodian folders inside them | Not modelled. The tree is `natives/{custodian}/{year}/{month}`. |
| A communicator pair with deliberately zero topical overlap | Not modelled. |
| A deliberate collection gap or spike in the date distribution | Not modelled. Dates have a real shape but no planted anomaly. |
| A population straddling two obvious document categories | Not modelled. |
| Custodian Entity load files for Import/Export | Not produced. `custodian-sources.csv` is a setup sheet, not an Entity object load file. |
| MIP-protected natives | Cannot be fabricated without a real tenant to apply the label. Rule 12 says so out loud rather than pretending coverage exists. |

---

## The template

> Fill in the brackets. Delete any section the repo already covers, and say which flag you
> want instead.

I need a synthetic e-discovery test corpus for RelativityOne. I am testing the Early
Insights / ECI dashboard, and this set is for exercising the six widgets and finding bugs
in them.

**Matter:** [PARTY A] v. [PARTY B] — [one line on the dispute]

**What I am testing:** [the six Early Insights widgets / the Update Early Insights re-run
path / the Repository to Review handoff via Integration Points / processing behaviour under
specific conditions]

**Workspace type:** [Repository/ECA / Review / both]

### Size

- Collected: [N] items
- Published: [N] items, so a [X]% reduction
- Reduction from [global deduplication and container expansion only — no NIST, since
  synthetic system files will not hash-match the real NIST RDS]
- Custodians: [N]

Stay under the 250,000 document limit unless I am specifically testing behaviour near the
cap.

### What each widget needs from the data

Design deliberately for all six, not just the ones that are easy:

- **Key Relationships** — communicator pairs with a wide volume spread, plus at least one
  entity carrying a single document so the long tail is testable. At least one person using
  multiple addresses, to test whether name normalisation resolves them.
- **Collection Coverage** — [N] data sources with genuinely different metadata profiles, and
  a date distribution with a real shape rather than a flat line. Include a deliberate gap or
  spike so there is something to detect.
- **File Types** — a mix that includes things likely to classify poorly: containers and their
  children, chat, audio and video, and at least one format that may land in Unidentified.
- **Document Categories** — enough topical separation that categorisation has something to
  work with, and at least one population that straddles two obvious categories.
- **PI Detect** — a PI layer distributed where it realistically lives rather than concentrated
  in one file. Include PII pasted into email bodies, not only in spreadsheets, since that is
  the harder catch. Include a high-sensitivity file that is entirely irrelevant to the matter,
  so the widget has to flag something nobody asked about.
- **Primary Language Composition** — a second language slice sized [under 1% / a meaningful
  fraction], deliberately unrelated to the matter so nobody has to wonder whether the
  foreign-language documents are secretly relevant.

### Pathologies to seed

Plant known-answer problems so I can tell a product bug from a data artifact:

- Documents with no extractable text at all — image-only PDFs, an encrypted container — so I
  can see how the LLM-driven widgets handle nothing to read
- At least one document where the relevant content is buried deep, for example on a late tab
  of a long workbook, to test extraction depth
- Nested containers, to test expansion depth
- A communicator pair with zero topical overlap, so a negative result is expected rather than
  a gap
- [Any specific pathology I am chasing]

### Findings to plant

Two findings that are each invisible to the other method, so I can tell what ECA surfaces
versus what only a reader catches:

1. One findable on metadata alone and unreadable by content analysis — for example a single
   outbound message to an address appearing exactly once in the corpus, carrying an encrypted
   attachment.
2. One findable only by reading it, with zero keyword hits — naming no company, no file, and
   no person in full.

Plus a decoy: someone matching the same filters as the principal but innocent, with the
distinguisher buried in the record rather than stated.

### Personal information

All values must be non-issuable or industry-standard test data: SSN area numbers 900-999
which the SSA has never issued, standard test card numbers, the 555-01xx phone block,
`.invalid` email domains. Make the SSN range a config toggle, because some detectors score
the never-issued block as low confidence and the widget may under-report.

### Non-negotiables

- **Real dates on every file.** Set Office core properties and file system mtimes from the
  manifest. python-docx and python-pptx ship templates dated 2013, and that default silently
  leaks into Collection Coverage.
- **Ground truth emitted at generation time**, not reconstructed afterward.
- **Fixed calendar dates**, all in the past.
- **Story-critical correspondents must not appear in random volume mail.** One stray email
  shifts an entity's Active Range and invalidates a planted finding.
- **Check both party names against real businesses** before building.

### Build-time assertions

The build must fail loudly rather than silently produce a broken corpus. At minimum: any
address that is supposed to be unique appears exactly once, no Office file carries a date
outside the matter window, and no planted correspondent appears before its seeded date.

### Deliverables

1. The corpus, in per-custodian folders under per-source folders
2. Custodian Entity load files for Import/Export

### Working style

Be direct and brief. Push back when I am wrong. Verify claims against the built artifact
rather than asserting them — read files back, count things, test the scripts. Say plainly
when something cannot be done in your environment rather than shipping an untested guess.

---

## Why the template is worth keeping

The three demands that carry the most weight are the three easiest to skip: ground truth at
generation time, assertions that fail the build, and dates that come from the manifest rather
than from whichever library wrote the file.

Every one of them exists here because it was missing. `EXPECTED_ERRORS.csv` exists because a
package once claimed 106 processing errors while sitting on 106 healthy files. Rule 19 exists
because the shipped package stamped every spreadsheet with the build date and every deck with
python-pptx's 2013 template date. A corpus that cannot be scored is not a test corpus.
