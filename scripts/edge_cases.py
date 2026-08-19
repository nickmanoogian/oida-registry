#!/usr/bin/env python3
"""
edge_cases.py — Starve the widgets: metadata that is clean-processing but incomplete

RULES.md Rule 12 covers files that fail processing. This covers the opposite and
more dangerous case: documents that process perfectly and still leave a feature with
nothing to work with. No custodian, no date, no text, a family whose other half is
missing, a language nobody expected.

The generated dataset is uniform to a fault — every document has a custodian, a date,
extracted text, and Language = English. Any feature that aggregates over a collection
has therefore only ever been exercised against a complete input.

Applied after generation, off by default. Default output stays byte-identical, so the
committed tiers and the CI determinism check are unaffected.
"""

import random

# Scenario volumes as a fraction of the tier, floored at 1 document each.
RATES = {
    "no_custodian":        0.020,
    "missing_date":        0.010,
    "sentinel_date":       0.006,
    "no_extracted_text":   0.015,
    "non_english":         0.040,
    "mixed_language":      0.004,
    "blank_recipients":    0.010,
    "list_only_recipients":0.006,
    "orphan_attachment":   0.006,
    "broken_family":       0.004,
    "duplicate_md5":       0.008,
    "media_no_text":       0.010,
    "oversized_text":      0.002,
}

# Word counts for the oversized documents, roughly 2 MB, 5 MB and 10 MB of text.
# A 200k token context is somewhere near 150k words, so all three are past it and
# the largest is an order of magnitude past.
OVERSIZED_WORD_COUNTS = [300_000, 800_000, 1_500_000]

SENTINEL_DATES = ["1601-01-01 00:00:00", "2099-12-31 23:59:59", "1970-01-01 00:00:00"]

OTHER_LANGUAGES = ["German", "Polish", "Spanish", "French", "Japanese",
                   "Chinese (Simplified)", "Arabic", "Portuguese"]

DISTRIBUTION_LISTS = ["All Sales <all-sales@mallinckrodt.com>",
                      "Compliance Team <compliance@mallinckrodt.com>",
                      "Undisclosed recipients:;"]

MALFORMED_SMTP = ["r.nash@", "@mallinckrodt.com", "greg tyler", "<>", "noreply@localhost"]

MEDIA_TYPES = [("mp3", "Media - Audio"), ("wav", "Media - Audio"),
               ("mp4", "Media - Video"), ("mov", "Media - Video")]


def _take(pool, n):
    """Pop up to n documents off the shuffled pool so scenarios never overlap."""
    taken, pool[:] = pool[:n], pool[n:]
    return taken


def apply(all_docs, families, custodians, seed=42):
    """Mutate `all_docs` in place. Returns a report keyed by scenario.

    Every scenario draws from a disjoint pool, so no document carries two faults and
    each one can be reasoned about on its own.
    """
    rng   = random.Random(seed ^ 0x3D6E)      # own stream: never perturbs default output
    total = len(all_docs)
    report = {}

    # Scripted hot documents carry the narrative; leave them intact. Container
    # records are excluded too: rewriting one's file type or custodian would leave
    # its children pointing at something that is no longer a container (Rule 3).
    pool = [d for d in all_docs
            if not d["Control Number"].startswith("HOT-")
            and str(d.get("Level","")) != "0"]
    rng.shuffle(pool)

    def count(key):
        return max(1, int(total * RATES[key]))

    # ── nobody owns these documents ───────────────────────────────────────
    docs = _take(pool, count("no_custodian"))
    for d in docs:
        d["Custodian"] = d["Custodian Email"] = ""
        d["Custodian Department"] = d["Custodian Org"] = ""
        # Keep the year/month tail so the folder tree stays well formed; only the
        # custodian segment becomes _Unassigned (build_load_package Rule 11).
        tail = d.get("Processing Folder Path", "").split("\\")[-2:]
        d["Processing Folder Path"] = "\\".join(["\\\\Collection", "_Unassigned"] + tail)
    report["no_custodian"] = [d["Control Number"] for d in docs]

    # ── no date at all, and dates no human ever typed ─────────────────────
    docs = _take(pool, count("missing_date"))
    for d in docs:
        d["Primary Date"] = d["Sort Date"] = ""
        d["Date Sent"] = d["Date Received"] = ""
    report["missing_date"] = [d["Control Number"] for d in docs]

    docs = _take(pool, count("sentinel_date"))
    for d in docs:
        stamp = rng.choice(SENTINEL_DATES)
        d["Primary Date"] = d["Sort Date"] = stamp
    report["sentinel_date"] = [d["Control Number"] for d in docs]

    # ── processed fine, nothing to read ───────────────────────────────────
    docs = _take(pool, count("no_extracted_text"))
    for d in docs:
        d["Extracted Text Preview"] = ""
        d["Word Count"] = "0"
        d["OCR Required?"] = "Yes"
    report["no_extracted_text"] = [d["Control Number"] for d in docs]

    # ── the collection is not monolingual ─────────────────────────────────
    docs = _take(pool, count("non_english"))
    for d in docs:
        d["Language"] = rng.choice(OTHER_LANGUAGES)
    report["non_english"] = [d["Control Number"] for d in docs]

    docs = _take(pool, count("mixed_language"))
    for d in docs:
        pair = rng.sample(OTHER_LANGUAGES, 2)
        d["Language"] = f"English; {pair[0]}; {pair[1]}"
    report["mixed_language"] = [d["Control Number"] for d in docs]

    # ── emails with nobody, or only a list, on the other end ──────────────
    emails = [d for d in pool if d.get("Email From","")]
    rng.shuffle(emails)

    docs = _take(emails, count("blank_recipients"))
    for d in docs:
        d["Email To"] = d["Email To SMTP"] = ""
        d["Email CC"] = d["Email CC SMTP"] = ""
        if rng.random() < 0.5:
            d["Email From SMTP"] = rng.choice(MALFORMED_SMTP)
    report["blank_recipients"] = [d["Control Number"] for d in docs]

    docs = _take(emails, count("list_only_recipients"))
    for d in docs:
        listed = rng.choice(DISTRIBUTION_LISTS)
        d["Email To"] = listed
        d["Email To SMTP"] = listed.split("<")[-1].rstrip(">") if "<" in listed else ""
    report["list_only_recipients"] = [d["Control Number"] for d in docs]

    # ── families missing their other half ─────────────────────────────────
    docs = _take(pool, count("orphan_attachment"))
    for d in docs:
        d["Parent Document ID"] = f"DOC-{rng.randint(9_000_000, 9_999_999)}"
        d["Family ID"] = d["Parent Document ID"]
    report["orphan_attachment"] = [d["Control Number"] for d in docs]

    # Anything an earlier scenario already claimed is off limits: deleting it would
    # leave that scenario's report naming a document that is not in the set.
    claimed = set()
    for name, entries in report.items():
        for e in entries:
            claimed.add(e.get("control_number") if isinstance(e, dict) else e)

    broken = []
    for fam in families:
        if len(broken) >= count("broken_family"):
            break
        kids = fam.get("children", [])
        if len(kids) < 2:
            continue
        lost = kids[-1]
        if lost.startswith("HOT-") or lost in claimed:
            continue                          # scripted, or already spoken for
        kids.pop()                            # the family record still references it
        broken.append({"parent": fam.get("parent_doc_id",""), "missing_child": lost})
    ids = {b["missing_child"] for b in broken}
    all_docs[:] = [d for d in all_docs if d["Control Number"] not in ids]
    report["broken_family"] = broken

    # ── the same document under two custodians ────────────────────────────
    docs  = _take(pool, count("duplicate_md5"))
    donors = [d for d in all_docs
              if d.get("MD5 Hash") and d.get("Custodian") and d not in docs]
    dupes = []
    for d in docs:
        donor = rng.choice(donors)
        if donor.get("Custodian") == d.get("Custodian"):
            continue
        d["MD5 Hash"] = donor["MD5 Hash"]
        dupes.append({"control_number": d["Control Number"],
                      "duplicate_of": donor["Control Number"],
                      "md5": donor["MD5 Hash"]})
    report["duplicate_md5"] = dupes

    # ── more text than anything downstream expects to read ────────────────
    # Word Count is the contract: build_load_package writes a native with this
    # much text, so the metadata and the file agree without a second lookup.
    docs = _take(pool, max(len(OVERSIZED_WORD_COUNTS), count("oversized_text")))
    oversized = []
    for n, d in enumerate(docs):
        words = OVERSIZED_WORD_COUNTS[n % len(OVERSIZED_WORD_COUNTS)]
        d["Word Count"] = str(words)
        d["File Type Category"] = "Text / Markup"
        d["File Extension"]     = "txt"
        d["File Name"]          = f"{d['Control Number']}.txt"
        d["Dedup Method"]       = "SHA256"
        oversized.append({"control_number": d["Control Number"], "word_count": words})
    report["oversized_text"] = oversized

    # ── files with no text to extract, ever ───────────────────────────────
    docs = _take(pool, count("media_no_text"))
    for d in docs:
        ext, category = rng.choice(MEDIA_TYPES)
        d["File Extension"]         = ext
        d["File Type Category"]     = category
        d["File Name"]              = f"{d['Control Number']}.{ext}"
        d["Extracted Text Preview"] = ""
        d["Word Count"]             = "0"
        d["Supported by Viewer"]    = "No"
        d["Analytics Eligible?"]    = "No"
        d["OCR Required?"]          = "No"
        d["Images?"]                = "No"        # RULES.md Rule 2, Audio/Video row
        d["Redactable?"]            = "No"
        d["Dedup Method"]           = "SHA256"
    report["media_no_text"] = [d["Control Number"] for d in docs]

    return report


# What each scenario starves, for the report header and the docs.
STARVES = {
    "no_custodian":         "Key Relationships, Collection Coverage, any per-custodian rollup",
    "missing_date":         "timelines and date range filters",
    "sentinel_date":        "timelines: an axis stretched to 1601 or 2099",
    "no_extracted_text":    "Topics, Summaries, PI Detect, anything reading document text",
    "non_english":          "Primary Language, and any English-only text analysis",
    "mixed_language":       "Primary Language: no single right answer",
    "blank_recipients":     "Key Relationships: an email with no edge to draw",
    "list_only_recipients": "Key Relationships: an edge to a list rather than a person",
    "orphan_attachment":    "family rollups: a child whose parent is not in the set",
    "broken_family":        "family rollups: a family record naming a document that is absent",
    "duplicate_md5":        "dedup and Collection Coverage",
    "media_no_text":        "Topics, Summaries, Document Categories: no text, ever",
    "oversized_text":       "summarisation and topic extraction: more text than a model context holds",
}
