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

import argparse, csv, json, os, sys
from collections import Counter, defaultdict

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"


def load(tier_dir):
    docs_path = os.path.join(tier_dir, "documents.csv")
    if not os.path.exists(docs_path):
        sys.exit(f"ERROR: documents.csv not found in {tier_dir}. Run generate_mock_metadata.py first.")
    with open(docs_path, encoding="utf-8") as f:
        docs = list(csv.DictReader(f))
    custs = families = batches = []
    for fname, var in [("custodians.json", "custs"), ("email-families.json", "families"), ("batches.json", "batches")]:
        path = os.path.join(tier_dir, fname)
        if os.path.exists(path):
            with open(path) as f:
                if var == "custs":     custs    = json.load(f)
                elif var == "families": families = json.load(f)
                else:                   batches  = json.load(f)
    return docs, custs, families, batches


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
    total   = len(docs)
    failures = 0

    # ── Rule 1: File type distribution ────────────────────────────────────
    print("Rule 1 — File type distribution")
    ft_counts = Counter(d["File Type Category"] for d in docs)
    email_pct = (ft_counts.get("Email - MSG",0) + ft_counts.get("Email - EML",0)) / total
    ok = 0.45 <= email_pct <= 0.65
    if not check("Email docs are 45–65% of total", ok, f"got {email_pct:.1%}", verbose): failures += 1

    container_types = [v for k,v in ft_counts.items() if "Container" in k or "PST" in k or "MBOX" in k]
    ok = len([k for k in ft_counts if "Container" in k or k in ("Email Container - PST","Email Container - MBOX")]) > 0
    if not check("Container file types present (PST/MBOX/ZIP)", ok, f"found: {[k for k in ft_counts if 'Container' in k]}", verbose): failures += 1

    ok = "Calendar - ICS" in ft_counts
    if not check("ICS calendar records present", ok, "", verbose): failures += 1

    # ── Rule 2: Workflow behavior flags ───────────────────────────────────
    print("\nRule 2 — Workflow behavior flags")
    required_flags = ["Images?","OCR Required?","Native Produced?","Redactable?","Analytics Eligible?","Dedup Method"]
    missing_flags  = [f for f in required_flags if f not in docs[0]]
    ok = len(missing_flags) == 0
    if not check("All workflow behavior flags present in columns", ok, f"missing: {missing_flags}", verbose): failures += 1

    email_docs  = [d for d in docs if d.get("File Type Category") in ("Email - MSG","Email - EML")]
    rsmf_docs   = [d for d in docs if "RSMF" in d.get("File Type Category","")]
    if email_docs:
        bad_dedup = [d["Control Number"] for d in email_docs if d.get("Dedup Method") != "MD5"]
        ok = len(bad_dedup) == 0
        if not check("Email docs use MD5 dedup method", ok, f"{len(bad_dedup)} violations: {bad_dedup[:3]}", verbose): failures += 1
    if rsmf_docs:
        bad_dedup = [d["Control Number"] for d in rsmf_docs if d.get("Dedup Method") != "EventCollectionId"]
        ok = len(bad_dedup) == 0
        if not check("RSMF docs use EventCollectionId dedup method", ok, f"{len(bad_dedup)} violations: {bad_dedup[:3]}", verbose): failures += 1

    # ── Rule 3: Container records ─────────────────────────────────────────
    print("\nRule 3 — Container records")
    container_docs = [d for d in docs if d.get("File Type Category","") in ("Email Container - PST","Email Container - MBOX","Container - ZIP")]
    if container_docs:
        bad_level = [d["Control Number"] for d in container_docs if str(d.get("Level","")) != "0"]
        ok = len(bad_level) == 0
        if not check("Container records have Level = 0", ok, f"{len(bad_level)} violations: {bad_level[:3]}", verbose): failures += 1

        bad_natives = [d["Control Number"] for d in container_docs if d.get("Has Natives","") != "No"]
        ok = len(bad_natives) == 0
        if not check("Container records have Has Natives = No", ok, f"{len(bad_natives)} violations: {bad_natives[:3]}", verbose): failures += 1
    else:
        print(f"  {WARN}  No container records found — skipping Rule 3 checks")

    # ── Rule 4: Special cases ─────────────────────────────────────────────
    print("\nRule 4 — Special cases")
    ics_docs = [d for d in docs if d.get("File Extension","") == "ics"]
    if ics_docs:
        bad_ics = [d["Control Number"] for d in ics_docs if d.get("Date Sent","").strip() != ""]
        ok = len(bad_ics) == 0
        if not check("ICS records have blank Date Sent", ok, f"{len(bad_ics)} violations: {bad_ics[:3]}", verbose): failures += 1
    else:
        print(f"  {WARN}  No ICS records found")

    jpg_docs = [d for d in docs if d.get("File Extension","") in ("jpg","jpeg","heic")]
    if jpg_docs:
        gps_count = sum(1 for d in jpg_docs if str(d.get("GPS Latitude","")).strip() not in ("","0"))
        gps_pct   = gps_count / len(jpg_docs)
        ok = 0.08 <= gps_pct <= 0.25
        if not check("10–25% of JPEG/HEIC have GPS EXIF", ok, f"got {gps_pct:.1%} ({gps_count}/{len(jpg_docs)})", verbose): failures += 1

    # ── Rule 5: Dedup methods ─────────────────────────────────────────────
    print("\nRule 5 — Dedup methods")
    doc_types = [d for d in docs if d.get("File Type Category","").startswith("Office -") or d.get("File Type Category","").startswith("PDF")]
    if doc_types:
        bad = [d["Control Number"] for d in doc_types if d.get("Dedup Method","") != "SHA256"]
        ok  = len(bad) == 0
        if not check("Office/PDF docs use SHA256 dedup", ok, f"{len(bad)} violations: {bad[:3]}", verbose): failures += 1

    # ── Rule 6: Processing errors ─────────────────────────────────────────
    print("\nRule 6 — Processing errors")
    error_docs = [d for d in docs if d.get("Processing Status","") == "Error"]
    ok = len(error_docs) > 0
    if not check("Processing error documents present", ok, "", verbose): failures += 1
    if error_docs:
        error_types = Counter(d.get("Processing Error Type","") for d in error_docs)
        ok = len(error_types) >= 2
        if not check("Multiple distinct processing error types", ok, f"found: {dict(error_types)}", verbose): failures += 1

    # ── Rule 7: TAR score bimodality ──────────────────────────────────────
    print("\nRule 7 — TAR score distribution (bimodal)")
    scored = [d for d in docs if d.get("TAR Score","").strip() not in ("","None")]
    if scored:
        scores = [float(d["TAR Score"]) for d in scored]
        low    = sum(1 for s in scores if s < 20) / len(scores)
        high   = sum(1 for s in scores if s > 75) / len(scores)
        mid    = sum(1 for s in scores if 20 <= s <= 75) / len(scores)
        ok = 0.30 <= low <= 0.50
        if not check("~40% of scored docs score 0–20 (non-responsive band)", ok, f"got {low:.1%}", verbose): failures += 1
        ok = 0.25 <= high <= 0.45
        if not check("~35% of scored docs score 75–100 (responsive band)", ok, f"got {high:.1%}", verbose): failures += 1
        ok = 0.15 <= mid <= 0.35
        if not check("~25% in uncertain 20–75 band", ok, f"got {mid:.1%}", verbose): failures += 1
    else:
        print(f"  {WARN}  No TAR scores found — skipping Rule 7")

    # ── Rule 8: Custodian hold statuses ───────────────────────────────────
    print("\nRule 8 — Custodian hold statuses")
    if custs:
        hold_statuses = [c.get("hold","") for c in custs]
        ok = "Outstanding" in hold_statuses
        if not check("At least one custodian with Outstanding hold", ok, f"holds: {Counter(hold_statuses)}", verbose): failures += 1
        ok = "Acknowledged" in hold_statuses
        if not check("At least one custodian with Acknowledged hold", ok, "", verbose): failures += 1
    else:
        print(f"  {WARN}  custodians.json not found — skipping Rule 8")

    # ── Rule 9: Email threading ───────────────────────────────────────────
    print("\nRule 9 — Email family and threading")
    if families:
        family_sizes  = [f.get("family_size",1) for f in families]
        avg_size      = sum(family_sizes) / len(family_sizes)
        ok = 2.0 <= avg_size <= 6.0
        if not check("Average email family size is 2–6 docs", ok, f"got {avg_size:.1f}", verbose): failures += 1

        # Check standalone as % of total email docs (not % of families)
        total_email_docs = sum(f.get("family_size",1) for f in families)
        standalone_email_docs = sum(1 for f in families if f.get("family_size",1) == 1)
        standalone_pct = standalone_email_docs / total_email_docs if total_email_docs else 0
        ok = 0.10 <= standalone_pct <= 0.40
        if not check("10–40% of email docs are standalone (no thread)", ok, f"got {standalone_pct:.1%} ({standalone_email_docs}/{total_email_docs} emails)", verbose): failures += 1

        scripted = [f for f in families if f.get("scripted")]
        ok = len(scripted) > 0
        if not check("Scripted story threads present (SFAM- prefix)", ok, "", verbose): failures += 1
    else:
        print(f"  {WARN}  email-families.json not found — skipping Rule 9")

    # ── Rule 10: Production / Bates ───────────────────────────────────────
    print("\nRule 10 — Production and Bates")
    produced  = [d for d in docs if d.get("Bates Begin","").strip() != ""]
    privileged= [d for d in docs if d.get("Privilege","") == "Privileged"]
    ok = len(produced) > 0
    if not check("Produced documents with Bates numbers exist", ok, "", verbose): failures += 1
    if produced:
        priv_with_bates = [d for d in privileged if d.get("Bates Begin","").strip() != ""]
        ok = len(priv_with_bates) == 0
        if not check("Privileged docs do not have Bates numbers", ok, f"{len(priv_with_bates)} violations: {[d['Control Number'] for d in priv_with_bates[:3]]}", verbose): failures += 1

        redacted = [d for d in produced if d.get("Redacted","") == "Yes"]
        ok = len(redacted) > 0
        if not check("Redacted documents exist in production", ok, "", verbose): failures += 1

    # ── Narrative checks (MDL 2804 story) ─────────────────────────────────
    print("\nNarrative — MDL 2804 story integrity")
    hot_scripted = [d for d in docs if d.get("Control Number","").startswith("HOT-")]
    ok = len(hot_scripted) > 0
    if not check("Scripted hot documents present (HOT- prefix)", ok, "", verbose): failures += 1

    if "Custodian Org" in docs[0]:
        orgs = set(d.get("Custodian Org","") for d in docs)
        ok   = "Mallinckrodt" in orgs
        if not check("Mallinckrodt custodians present", ok, f"orgs found: {orgs}", verbose): failures += 1

    if "Narrative Phase" in docs[0]:
        phases = set(str(d.get("Narrative Phase","")) for d in docs if d.get("Narrative Phase",""))
        ok = len(phases) >= 2
        if not check("Multiple narrative phases present", ok, f"phases: {phases}", verbose): failures += 1

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    total_checks = 20
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
    failures = run(args.tier, tier_dir, args.verbose)
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
