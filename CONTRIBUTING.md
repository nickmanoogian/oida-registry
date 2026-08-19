# Contributing

This repo has two distinct areas that can be updated independently.

---

## Before you raise a PR

Run the gate:

```bash
make check
```

That is lint, typecheck, an import cycle check, the RULES.md validators against both the default and
the edge-case tier, the error scenario matrix and the determinism check, ordered cheapest first so a typo fails in seconds rather than after a two
minute build. CI runs the same things plus the package builds; `make check` is what keeps you
from finding out on GitHub.

The idea is borrowed from eci-ui, which gates every PR on a single composite command
(`npm run check:circular-deps`: lint, typecheck, madge, unit tests). One command a contributor
can remember beats five they have to look up.

Typecheck runs mypy in its default mode with `--ignore-missing-imports`. It is not strict and
it is not asking for annotations; it found eleven real problems on its first run, including
`element.find(tag).text` in `fetch_manifest.py`, which raises `AttributeError` the first time S3
returns a listing without that tag.

Lint is deliberately about defects rather than taste. The selection is in `ruff.toml` with the
reasoning; notably `E701`/`E702` are off, because one-statement-per-line would rewrite hundreds
of lines of the existing house style and bury real changes in noise.

If you change the generator, the committed small tier must be regenerated and committed with it.
`make check` will tell you.

## 1. Mock data rules and generator

Rules live in `mock-data/RULES.md`. The generator lives in `scripts/generate_mock_metadata.py`. Validation lives in `scripts/validate_mock_data.py`.

### Updating distributions or adding file types

Edit `TIER_FILE_COUNTS` in the generator. Run validation after:

```bash
python scripts/generate_mock_metadata.py --tier small
python scripts/validate_mock_data.py --tier small
```

If the numbers look right, regenerate all three tiers and open a PR. Medium and large will need to be uploaded as a new GitHub Release (bump to the next minor version).

### Adding a custodian

Add to `CUSTODIANS["small"]`, `["medium"]`, and/or `["large"]` in the generator. Required fields:

```python
{
    "id": "C0XX",
    "name": "Full Name",
    "email": "email@org.com",
    "role": "Job Title",
    "dept": "Department",
    "doc_target": 500,           # approximate document count
    "org": "Mallinckrodt",       # or Insys / McKinsey / Outside Counsel
    "phases_active": [2, 3, 4],  # which narrative phases they appear in
    "narrative": "One-sentence role in the MDL story",
    "hold": "Acknowledged",      # or Outstanding / Escalated
    "hold_date": "2018-08-20",   # or None if Outstanding
}
```

### Adding a scripted hot document

Add to `SCRIPTED_HOT_DOCS` in the generator:

```python
{
    "control_number": "HOT-0000014",
    "subject": "Email subject line",          # for email types
    "title": "Document title",                # for office/PDF types
    "file_type": "Email - MSG",               # must match a FILE_TYPES key
    "phase": 2,                               # 1-4
    "date": "2014-06-15",
    "custodian_by_tier": {
        "small": "Michael Brennan",
        "medium": "Robert Ashton",
        "large": "Robert Ashton",
    },
    "org": "Mallinckrodt",
    "issue_tags": "SOM Override; DEA Correspondence",
    "privilege": None,                        # or "Attorney-Client Communication" etc.
    "why_hot": "One sentence explaining why this document is evidentiary",
    "tiers": ["medium", "large"],             # omit to include in all tiers
}
```

### Adding an email subject to a phase pool

Edit `EMAIL_SUBJECTS_BY_ORG_PHASE` in the generator. Keys are `(org, phase)` tuples. Subjects support template variables: `{product}`, `{territory}`, `{month}`, `{year}`, `{q}`, `{account}`, `{n}`, `{speaker}`, `{role}`.

### Updating RULES.md

Rules are intentionally written to be readable by non-engineers. When updating:
- Lead with the rule itself (what to do)
- Explain *why* the rule exists (what breaks without it)
- Include a concrete example
- Update the validation assertions at the bottom of RULES.md
- Update `scripts/validate_mock_data.py` to match

---

## 2. Raw OIDA data registry

### Adding a new dataset pointer

If new files appear in the S3 bucket, add a `.dvc` file:

```yaml
deps:
- path: https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com/data-products/newfile.csv
  etag: <etag from S3 listing>
  size: <size in bytes>
outs:
- path: newfile.csv
  hash: etag
  etag: <etag>
  size: <size in bytes>
  isexec: false
```

Run `make verify` to confirm the URL is reachable, then open a PR.

### Updating SCHEMA.md

If a dataset's column structure changes, update `data-products/SCHEMA.md`. Include:
- Column name
- Description (what it means, not just what it's called)
- Data type and example values where helpful

---

## Release versioning

| Change type | Version bump |
|-------------|-------------|
| New datasets, new `.dvc` pointers, schema updates | patch (v1.3.x) |
| New rules, generator changes, new fields in documents.csv | minor (v1.x.0) |
| Breaking changes to documents.csv schema or tier structure | major (vx.0.0) |

When releasing a new minor/major version:
1. Regenerate all three tiers
2. Create a GitHub Release with the new medium/large artifacts
3. Update `.dvc` pointers in `mock-data/medium/` and `mock-data/large/`
4. Update `CHANGELOG.md`
5. Open a PR

---

## Getting help

Open a GitHub Issue. Use the broken-link template for S3 URL failures and the general template for everything else.
