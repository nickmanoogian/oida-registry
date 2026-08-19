#!/usr/bin/env python3
"""
validate_mock_data.py — Verify a mock dataset conforms to mock-data/RULES.md

Runs assertions against documents.csv, custodians.json, email-families.json,
and batches.json in the specified tier directory. Prints PASS/FAIL for each
check and exits non-zero if any check fails.

Usage:
  python scripts/validate_mock_data.py --tier small
  python scripts/validate_mock_data.py --tier medium --dir ./my-data/
  python scripts/validate_mock_data.py --tier large --verbose
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"

# RULES.md Rule 1: expected share of the tier per file type family, with the
# tolerance a seeded generator needs. Checking only "email exists" let a tier
# drift arbitrarily far from the table and still pass.
FAMILY_SHARE = {
    "email":       (0.45, 0.65),
    "word":        (0.08, 0.20),
    "excel":       (0.03, 0.12),
    "powerpoint":  (0.01, 0.08),
    "pdf":         (0.03, 0.12),
    "rsmf":        (0.005, 0.06),
    "image":       (0.01, 0.08),
    "text":        (0.01, 0.08),
    "unsupported": (0.002, 0.03),
}

MIN_FILE_TYPES = {"small": 20, "medium": 25, "large": 25}

# The ECI document drill always shows Control Number, Custodian, Primary Date/Time,
# Record Type, Unified Title, Topic (AI) and Summary (AI). The AI columns are produced
# downstream; Record Type is collected, so the dataset owes it.
# "Attachment" is absent by construction: family children here are thread replies.
RECORD_TYPES = {"Email", "EDoc", "Container"}

# Rule 6: the table's per-type counts (15 documents in the small tier) have never
# matched what the generator produces, and 1% is low for a real matter. The rule
# now states a rate band; see RULES.md Rule 6.
ERROR_RATE = (0.05, 0.12)

# RULES.md Rule 2, expressed as assertions. The old check only proved the columns
# existed, not that any value in them was right.
RULE2_TABLE = [
    ("email",       "Dedup Method",        "MD5"),
    ("email",       "Analytics Eligible?", "Yes"),
    ("container",   "Has Natives",         "No"),
    ("container",   "Analytics Eligible?", "No"),
    ("rsmf",        "Native Produced?",    "No"),
    ("rsmf",        "Dedup Method",        "EventCollectionId"),
    ("scanned pdf", "OCR Required?",       "Yes"),
    ("image",       "OCR Required?",       "Yes"),
    ("audio/video", "Images?",             "No"),
    ("audio/video", "Analytics Eligible?", "No"),
    ("audio/video", "Redactable?",         "No"),
    ("unsupported", "Analytics Eligible?", "No"),
    ("mip pdf",     "Analytics Eligible?", "No"),
]

_FAMILY_MATCH = {
    "email":       lambda c: c in ("Email - MSG", "Email - EML"),
    "word":        lambda c: "Word" in c,
    "excel":       lambda c: "Excel" in c,
    "powerpoint":  lambda c: "PowerPoint" in c,
    "pdf":         lambda c: c.startswith("PDF"),
    "scanned pdf": lambda c: c == "PDF - Scanned",
    "mip pdf":     lambda c: "MIP" in c,
    "rsmf":        lambda c: "RSMF" in c,
    "image":       lambda c: c.startswith("Image"),
    "text":        lambda c: c.startswith("Text"),
    "unsupported": lambda c: c == "Unsupported",
    "container":   lambda c: c in ("Email Container - PST", "Email Container - MBOX", "Container - ZIP"),
    "audio/video": lambda c: c.startswith(("Audio", "Video", "Media")),
}


def in_family(category, family):
    return _FAMILY_MATCH[family](category)


EMAIL_TYPES     = {"Email - MSG", "Email - EML"}
CONTAINER_TYPES = {"Email Container - PST", "Email Container - MBOX", "Container - ZIP"}
RSMF_SUBSTR     = "RSMF"


def load(tier_dir):
    docs_path = os.path.join(tier_dir, "documents.csv")
    if not os.path.exists(docs_path):
        sys.exit(f"ERROR: documents.csv not found in {tier_dir}. Run generate_mock_metadata.py first.")
    with open(docs_path, encoding="utf-8") as f:
        docs = list(csv.DictReader(f))

    data = {}
    for fname, key in [("custodians.json", "custs"), ("email-families.json", "families"), ("batches.json", "batches")]:
        path = os.path.join(tier_dir, fname)
        data[key] = json.load(open(path)) if os.path.exists(path) else []
    return docs, data["custs"], data["families"], data["batches"]


def check(label, passed, detail="", verbose=False):
    status = PASS if passed else FAIL
    line   = f"  {status}  {label}"
    if detail and (not passed or verbose):
        line += f"\n         {detail}"
    print(line)
    return passed


def run(tier_name, tier_dir, verbose):
    print(f"\n{'='*60}")
    print(f"  Validating: {tier_name.upper()} tier — {tier_dir}")
    print(f"{'='*60}\n")

    docs, custs, families, batches = load(tier_dir)
    total    = len(docs)
    failures = 0

    # Pre-compute filtered slices reused across multiple rules
    ft_counts     = Counter(d["File Type Category"] for d in docs)
    email_docs    = [d for d in docs if d.get("File Type Category") in EMAIL_TYPES]
    rsmf_docs     = [d for d in docs if RSMF_SUBSTR in d.get("File Type Category","")]
    container_docs = [d for d in docs if d.get("File Type Category","") in CONTAINER_TYPES]
    ics_docs      = [d for d in docs if d.get("File Extension","") == "ics"]
    jpg_docs      = [d for d in docs if d.get("File Extension","") in ("jpg","jpeg","heic")]
    office_pdf    = [d for d in docs if d.get("File Type Category","").startswith(("Office -","PDF"))]
    error_docs    = [d for d in docs if d.get("Processing Status","") == "Error"]
    produced      = [d for d in docs if d.get("Bates Begin","").strip()]
    privileged    = [d for d in docs if d.get("Privilege","") == "Privileged"]
    scored        = [d for d in docs if d.get("TAR Score","").strip() not in ("","None")]

    # ── Rule 1: File type distribution ────────────────────────────────────
    print("Rule 1 — File type distribution")
    email_pct = sum(ft_counts.get(t,0) for t in EMAIL_TYPES) / total
    ok = 0.45 <= email_pct <= 0.65
    if not check("Email docs are 45–65% of total", ok, f"got {email_pct:.1%}", verbose): failures += 1

    ok = any(t in ft_counts for t in CONTAINER_TYPES)
    if not check("Container file types present (PST/MBOX/ZIP)", ok, f"found: {[k for k in ft_counts if k in CONTAINER_TYPES]}", verbose): failures += 1

    ok = "Calendar - ICS" in ft_counts
    if not check("ICS calendar records present", ok, "", verbose): failures += 1

    # The point of Rule 1 is the spread. Checking only "email exists" let a tier
    # drift arbitrarily far from the table and still pass.
    ok = len(ft_counts) >= MIN_FILE_TYPES[tier_name]
    if not check(f"At least {MIN_FILE_TYPES[tier_name]} distinct file type categories", ok,
                 f"got {len(ft_counts)}", verbose): failures += 1

    for family, (lo, hi) in FAMILY_SHARE.items():
        share = sum(n for cat, n in ft_counts.items() if in_family(cat, family)) / total
        ok = lo <= share <= hi
        if not check(f"{family} is {lo:.0%}–{hi:.0%} of the tier", ok,
                     f"got {share:.1%}", verbose): failures += 1

    ok = any(in_family(cat, "audio/video") for cat in ft_counts)
    if not check("Audio/Video present (no extractable text at all)", ok, "", verbose): failures += 1

    # ── Rule 2: Workflow behavior flags ───────────────────────────────────
    print("\nRule 2 — Workflow behavior flags")
    required_flags = ["Images?","OCR Required?","Native Produced?","Redactable?","Analytics Eligible?","Dedup Method"]
    missing_flags  = [f for f in required_flags if f not in docs[0]]
    ok = not missing_flags
    if not check("All workflow behavior flags present in columns", ok, f"missing: {missing_flags}", verbose): failures += 1

    if email_docs:
        bad = [d["Control Number"] for d in email_docs if d.get("Dedup Method") != "MD5"]
        ok  = not bad
        if not check("Email docs use MD5 dedup method", ok, f"{len(bad)} violations: {bad[:3]}", verbose): failures += 1
    if rsmf_docs:
        bad = [d["Control Number"] for d in rsmf_docs if d.get("Dedup Method") != "EventCollectionId"]
        ok  = not bad
        if not check("RSMF docs use EventCollectionId dedup method", ok, f"{len(bad)} violations: {bad[:3]}", verbose): failures += 1

    # The presence check above only proves the columns exist. These assert the
    # values the Rule 2 table actually specifies, per file type family.
    for family, field, expected in RULE2_TABLE:
        sel = [d for d in docs if in_family(d.get("File Type Category",""), family)]
        if not sel:
            continue
        bad = [d["Control Number"] for d in sel if d.get(field,"") != expected]
        ok  = not bad
        if not check(f"{family}: {field} = {expected}", ok,
                     f"{len(bad)} of {len(sel)} violations: {bad[:3]}", verbose): failures += 1

    # ── Rule 3: Container records ─────────────────────────────────────────
    print("\nRule 3 — Container records")
    if container_docs:
        bad_level   = [d["Control Number"] for d in container_docs if str(d.get("Level","")) != "0"]
        bad_natives = [d["Control Number"] for d in container_docs if d.get("Has Natives","") != "No"]
        ok = not bad_level
        if not check("Container records have Level = 0", ok, f"{len(bad_level)} violations: {bad_level[:3]}", verbose): failures += 1
        ok = not bad_natives
        if not check("Container records have Has Natives = No", ok, f"{len(bad_natives)} violations: {bad_natives[:3]}", verbose): failures += 1
        # A container nothing points at is not a container. This was the gap:
        # only the 16 parents were checked, never whether any child referenced them.
        container_ids = {d["Control Number"] for d in container_docs}
        children      = [d for d in docs if d.get("Container ID","").strip()]

        dangling = [d["Control Number"] for d in children
                    if d["Container ID"] not in container_ids]
        ok = not dangling
        if not check("Container ID references an existing container record", ok,
                     f"{len(dangling)} dangling: {dangling[:3]}", verbose): failures += 1

        childless = [c["Control Number"] for c in container_docs
                     if c["Control Number"] not in {d["Container ID"] for d in children}]
        ok = not childless
        if not check("Every container has at least one child", ok,
                     f"{len(childless)} empty: {childless[:3]}", verbose): failures += 1

        no_name = [d["Control Number"] for d in children if not d.get("Container Name","").strip()]
        ok = not no_name
        if not check("Container children carry Container Name", ok,
                     f"{len(no_name)} missing: {no_name[:3]}", verbose): failures += 1

        bad_level = [d["Control Number"] for d in children if str(d.get("Level","")) != "1"]
        ok = not bad_level
        if not check("Container children are Level 1", ok,
                     f"{len(bad_level)} violations: {bad_level[:3]}", verbose): failures += 1
    else:
        print(f"  {WARN}  No container records found — skipping Rule 3 checks")

    # ── Rule 4: Special cases ─────────────────────────────────────────────
    print("\nRule 4 — Special cases")
    if ics_docs:
        bad_ics = [d["Control Number"] for d in ics_docs if d.get("Date Sent","").strip()]
        ok = not bad_ics
        if not check("ICS records have blank Date Sent", ok, f"{len(bad_ics)} violations: {bad_ics[:3]}", verbose): failures += 1
    else:
        print(f"  {WARN}  No ICS records found")

    if jpg_docs:
        gps_count = sum(1 for d in jpg_docs if d.get("GPS Latitude") and d.get("GPS Latitude") != "0")
        gps_pct   = gps_count / len(jpg_docs)
        ok = 0.08 <= gps_pct <= 0.25
        if not check("10–25% of JPEG/HEIC have GPS EXIF", ok, f"got {gps_pct:.1%} ({gps_count}/{len(jpg_docs)})", verbose): failures += 1

    # ── Rule 5: Dedup methods ─────────────────────────────────────────────
    print("\nRule 5 — Dedup methods")
    if office_pdf:
        bad = [d["Control Number"] for d in office_pdf if d.get("Dedup Method","") != "SHA256"]
        ok  = not bad
        if not check("Office/PDF docs use SHA256 dedup", ok, f"{len(bad)} violations: {bad[:3]}", verbose): failures += 1

    # ── Rule 6: Processing errors ─────────────────────────────────────────
    print("\nRule 6 — Processing errors")
    ok = bool(error_docs)
    if not check("Processing error documents present", ok, "", verbose): failures += 1
    if error_docs:
        error_types = Counter(d.get("Processing Error Type","") for d in error_docs)
        ok = len(error_types) >= 6
        if not check("At least 6 distinct processing error types", ok, f"found {len(error_types)}: {dict(error_types)}", verbose): failures += 1

        rate = len(error_docs) / total
        ok = ERROR_RATE[0] <= rate <= ERROR_RATE[1]
        if not check(f"Processing errors are {ERROR_RATE[0]:.0%}–{ERROR_RATE[1]:.0%} of the tier", ok,
                     f"got {rate:.1%} ({len(error_docs)}/{total})", verbose): failures += 1

        # An error that never reaches the error queue is not modelled, just labelled.
        staged = sum(1 for d in error_docs
                     if d.get("Workflow Stage","") == "Pre-Review: Processing Error")
        ok = staged / len(error_docs) >= 0.75
        if not check("Most error documents sit in Pre-Review: Processing Error", ok,
                     f"{staged}/{len(error_docs)}", verbose): failures += 1

    # ── Rule 7: TAR score bimodality ──────────────────────────────────────
    print("\nRule 7 — TAR score distribution (bimodal)")
    if scored:
        scores = [float(d["TAR Score"]) for d in scored]
        n      = len(scores)
        low    = sum(1 for s in scores if s < 20)  / n
        high   = sum(1 for s in scores if s > 75)  / n
        mid    = sum(1 for s in scores if 20 <= s <= 75) / n
        for label, val, lo, hi in [
            ("~40% of scored docs score 0–20 (non-responsive band)",  low,  0.30, 0.50),
            ("~35% of scored docs score 75–100 (responsive band)",    high, 0.25, 0.45),
            ("~25% in uncertain 20–75 band",                          mid,  0.15, 0.35),
        ]:
            ok = lo <= val <= hi
            if not check(label, ok, f"got {val:.1%}", verbose): failures += 1
    else:
        print(f"  {WARN}  No TAR scores found — skipping Rule 7")

    # ── Rule 8: Custodian hold statuses ───────────────────────────────────
    print("\nRule 8 — Custodian hold statuses")
    if custs:
        hold_statuses = [c.get("hold","") for c in custs]
        for expected in ("Outstanding", "Acknowledged"):
            ok = expected in hold_statuses
            if not check(f"At least one custodian with {expected} hold", ok, f"holds: {Counter(hold_statuses)}", verbose): failures += 1
    else:
        print(f"  {WARN}  custodians.json not found — skipping Rule 8")

    # ── Rule 9: Email threading ───────────────────────────────────────────
    print("\nRule 9 — Email family and threading")
    if families:
        sizes    = [f.get("family_size",1) for f in families]
        avg_size = sum(sizes) / len(sizes)
        ok = 2.0 <= avg_size <= 6.0
        if not check("Average email family size is 2–6 docs", ok, f"got {avg_size:.1f}", verbose): failures += 1

        total_email_docs    = sum(sizes)
        standalone_email_docs = sum(1 for s in sizes if s == 1)
        standalone_pct = standalone_email_docs / total_email_docs if total_email_docs else 0
        ok = 0.10 <= standalone_pct <= 0.40
        if not check("10–40% of email docs are standalone (no thread)", ok, f"got {standalone_pct:.1%} ({standalone_email_docs}/{total_email_docs} emails)", verbose): failures += 1

        ok = any(f.get("scripted") for f in families)
        if not check("Scripted story threads present (SFAM- prefix)", ok, "", verbose): failures += 1

        # A family record naming a document that is not in the set is a broken
        # rollup. Deliberate ones are declared in edge-cases.json and excused.
        declared = set()
        edge_file = os.path.join(tier_dir, "edge-cases.json")
        if os.path.exists(edge_file):
            for b in json.load(open(edge_file))["scenarios"].get("broken_family", {}).get("documents", []):
                declared.add(b.get("missing_child"))
        present = {d["Control Number"] for d in docs}
        ghosts  = sorted({m for f in families
                          for m in [f.get("parent_doc_id","")] + f.get("children", [])
                          if m and m not in present and m not in declared})
        ok = not ghosts
        if not check("Every document named in email-families.json exists", ok,
                     f"{len(ghosts)} missing: {ghosts[:3]}", verbose): failures += 1
    else:
        print(f"  {WARN}  email-families.json not found — skipping Rule 9")

    # ── Rule 10: Production / Bates ───────────────────────────────────────
    print("\nRule 10 — Production and Bates")
    ok = bool(produced)
    if not check("Produced documents with Bates numbers exist", ok, "", verbose): failures += 1
    if produced:
        priv_with_bates = [d for d in privileged if d.get("Bates Begin","").strip()]
        ok = not priv_with_bates
        if not check("Privileged docs do not have Bates numbers", ok, f"{len(priv_with_bates)} violations: {[d['Control Number'] for d in priv_with_bates[:3]]}", verbose): failures += 1

        ok = any(d.get("Redacted","") == "Yes" for d in produced)
        if not check("Redacted documents exist in production", ok, "", verbose): failures += 1

        # RULES.md: only Responsive, non-privileged documents get Bates numbers.
        # Only the privileged half of that sentence was being checked.
        non_resp = [d["Control Number"] for d in produced
                    if d.get("Responsiveness","") != "Responsive"]
        ok = not non_resp
        if not check("Only Responsive documents have Bates numbers", ok,
                     f"{len(non_resp)} violations: {non_resp[:3]}", verbose): failures += 1

        orphan_redactions = [d["Control Number"] for d in docs
                             if d.get("Redacted","") == "Yes" and not d.get("Bates Begin","").strip()]
        ok = not orphan_redactions
        if not check("Redacted documents carry Bates numbers", ok,
                     f"{len(orphan_redactions)} violations: {orphan_redactions[:3]}", verbose): failures += 1

        dupes = [b for b, n in Counter(d["Bates Begin"] for d in produced).items() if n > 1]
        ok = not dupes
        if not check("Bates Begin values are unique", ok,
                     f"{len(dupes)} duplicated: {dupes[:3]}", verbose): failures += 1

    # ── Narrative checks (MDL 2804 story) ─────────────────────────────────
    print("\nNarrative — MDL 2804 story integrity")
    ok = any(d.get("Control Number","").startswith("HOT-") for d in docs)
    if not check("Scripted hot documents present (HOT- prefix)", ok, "", verbose): failures += 1

    if "Custodian Org" in docs[0]:
        orgs = {d.get("Custodian Org","") for d in docs}
        ok   = "Mallinckrodt" in orgs
        if not check("Mallinckrodt custodians present", ok, f"orgs found: {orgs}", verbose): failures += 1

    if "Narrative Phase" in docs[0]:
        phases = {str(d.get("Narrative Phase","")) for d in docs if d.get("Narrative Phase","")}
        ok = len(phases) >= 2
        if not check("Multiple narrative phases present", ok, f"phases: {phases}", verbose): failures += 1

    # ── Rule 14 — production drill baseline ───────────────────────────────
    print("\nRule 14 — production drill baseline")
    ok = "Record Type" in docs[0]
    if not check("Record Type column present", ok, "", verbose): failures += 1
    if ok:
        blanks = [d["Control Number"] for d in docs if not d.get("Record Type","").strip()]
        if not check("Every document has a Record Type", not blanks,
                     f"{len(blanks)} blank: {blanks[:3]}", verbose): failures += 1
        bad = [d["Control Number"] for d in docs
               if d.get("Record Type","") not in RECORD_TYPES]
        if not check(f"Record Type is one of {sorted(RECORD_TYPES)}", not bad,
                     f"{len(bad)} unexpected: {bad[:3]}", verbose): failures += 1
        containers_typed = [d for d in docs if str(d.get("Level","")) == "0"
                            and d.get("Record Type") != "Container"]
        if not check("Container records are typed as Container", not containers_typed,
                     f"{len(containers_typed)} mistyped", verbose): failures += 1

    # ── Rule 13 — edge cases, when the tier carries them ──────────────────
    edge_path = os.path.join(tier_dir, "edge-cases.json")
    if os.path.exists(edge_path):
        print("\nRule 13 — edge cases")
        report   = json.load(open(edge_path))["scenarios"]
        by_ctrl  = {d["Control Number"]: d for d in docs}

        # A scenario is only real if the documents it names are actually starved.
        PROBES = {
            "no_custodian":       lambda d: not d.get("Custodian","").strip(),
            "missing_date":       lambda d: not d.get("Primary Date","").strip(),
            "sentinel_date":      lambda d: d.get("Primary Date","")[:4] in ("1601","1970","2099"),
            "no_extracted_text":  lambda d: not d.get("Extracted Text Preview","").strip(),
            "non_english":        lambda d: d.get("Language","") not in ("", "English"),
            "mixed_language":     lambda d: ";" in d.get("Language",""),
            "blank_recipients":   lambda d: not d.get("Email To","").strip(),
            "media_no_text":      lambda d: d.get("File Type Category","").startswith("Media"),
        }
        for name, probe in PROBES.items():
            listed = report.get(name, {}).get("documents", [])
            if not listed:
                continue
            bad = [c for c in listed if c in by_ctrl and not probe(by_ctrl[c])]
            if not check(f"{name}: every listed document is actually starved",
                         not bad, f"{len(bad)} not starved: {bad[:3]}", verbose): failures += 1

        # A broken family must genuinely reference a document that is absent.
        missing = report.get("broken_family", {}).get("documents", [])
        if missing:
            still_here = [b["missing_child"] for b in missing if b["missing_child"] in by_ctrl]
            if not check("broken_family: the named child is absent from documents.csv",
                         not still_here, f"{len(still_here)} still present", verbose): failures += 1

        counts_ok = all(len(v.get("documents", [])) == v.get("count")
                        for v in report.values())
        if not check("edge-cases.json counts match its own document lists",
                     counts_ok, "", verbose): failures += 1

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    if failures == 0:
        print(f"  {PASS}  All checks passed — {tier_dir} is a valid {tier_name} dataset")
    else:
        print(f"  {FAIL}  {failures} check(s) failed — see above for details")
    print(f"{'='*60}\n")
    return failures


def main():
    p = argparse.ArgumentParser(description="Validate OIDA mock data against RULES.md")
    p.add_argument("--tier",    required=True, choices=["small","medium","large"])
    p.add_argument("--dir",     default=None, help="Path to tier directory (default: mock-data/{tier}/)")
    p.add_argument("--verbose", action="store_true", help="Show detail on passing checks too")
    args = p.parse_args()
    tier_dir = args.dir or os.path.join("mock-data", args.tier)
    sys.exit(1 if run(args.tier, tier_dir, args.verbose) else 0)

if __name__ == "__main__":
    main()
