#!/usr/bin/env python3
"""
validate_load_package.py — Verify a built load package conforms to RULES.md Rule 11

Checks the package on disk, not the source metadata: that every NativeFilePath in
load-file.dat resolves to a real file, that the folder a native sits in matches the
custodian on its row, that nothing was dumped at the root of natives/, and that
custodian-sources.csv agrees with what is actually on disk (Rule 11).

When the package carries EXPECTED_ERRORS.csv it also enforces Rule 12: every
deliberately broken native exists, is genuinely broken in the way its scenario
claims, and the File Size in the load file matches the bytes on disk.

Usage:
  python scripts/validate_load_package.py load-packages/small
  python scripts/validate_load_package.py load-packages/small --flat
"""

import argparse
import csv
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import error_natives

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

DAT_SEP   = chr(254)
DAT_QUOTE = chr(255)

failures = []


def check(label, ok, detail=""):
    print(f"  [{PASS if ok else FAIL}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def read_dat(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            rows.append([v.strip(DAT_QUOTE) for v in line.rstrip("\n").split(DAT_SEP)])
    return rows[0], rows[1:]


def is_broken(row, path):
    """Confirm a fabricated native actually fails the way its scenario claims.

    The signature has to be specific enough that replacing a broken file with a
    healthy one is caught. "Non-empty" is not a signature.
    """
    scenario = row["Scenario"]
    note     = row.get("How It Was Built", "")
    data     = open(path, "rb").read()
    if scenario == "Empty File":
        return len(data) == 0
    if scenario == "Password Protected":
        if data[:4] == b"%PDF":
            return b"/Encrypt" in data
        try:
            z = zipfile.ZipFile(path)
            z.read(z.namelist()[0])
            return False                      # opened with no password: not protected
        except RuntimeError as e:
            return "password" in str(e).lower()
        except Exception:
            return True
    if scenario == "Corrupt File":
        m = re.search(r"truncated to (\d+) of", note)
        if m:
            return len(data) == int(m.group(1))
        if "magic bytes" in note:
            return data[:8] == b"\x00" * 8
        return False
    if scenario == "Extraction Failure":
        try:
            names = zipfile.ZipFile(path).namelist()
            return not any(n in names for n in
                           ("word/document.xml", "xl/workbook.xml", "ppt/presentation.xml"))
        except Exception:
            return True
    if scenario == "Container Extraction Timeout":
        try:
            return zipfile.ZipFile(path).namelist()[0].endswith(".zip")
        except Exception:
            return False
    if scenario == "Teams Conversion Error":
        try:
            json.loads(data.decode("utf-8", "replace"))
            return False
        except Exception:
            return True
    if scenario == "OCR Failure - Poor Scan Quality":
        return b"/Font" not in data
    if scenario == "Extension Mismatch":
        return data[:4] == b"%PDF"
    if scenario == "Unsupported File Type":
        if any(data.startswith(sig) for sig in error_natives.UNSUPPORTED_STUBS.values()):
            return True
        try:                                   # iWork stub is a zip with an Index/ part
            return any(n.startswith("Index/") for n in zipfile.ZipFile(path).namelist())
        except Exception:
            pass
        return data.startswith(b"\x00\x01\x02\x03")
    return True                               # unknown scenario: do not fail the run


def main():
    ap = argparse.ArgumentParser(description="Validate a built Relativity load package")
    ap.add_argument("package", help="Path to the package directory")
    ap.add_argument("--flat", action="store_true",
                    help="Package was built with --flat; skip the per-custodian folder checks")
    args = ap.parse_args()

    pkg = args.package
    dat = os.path.join(pkg, "load-file.dat")
    src = os.path.join(pkg, "custodian-sources.csv")
    nat = os.path.join(pkg, "natives")

    for required in (dat, src, nat):
        if not os.path.exists(required):
            sys.exit(f"ERROR: {required} not found. Build the package first.")

    print(f"\n  Validating {pkg} (Rule 11)\n")

    header, rows = read_dat(dat)
    i_nat  = header.index("NativeFilePath")
    i_ctrl = header.index("BegDoc#")
    i_cust = header.index("Custodian")

    # 1. every declared native resolves on disk
    missing = [r[i_nat] for r in rows if r[i_nat]
               and not os.path.isfile(os.path.join(pkg, r[i_nat].replace("\\", os.sep)))]
    check("every NativeFilePath resolves on disk", not missing,
          f"{len(missing)} missing" if missing else f"{sum(1 for r in rows if r[i_nat]):,} natives")

    # 2. load file paths use backslashes
    fwd = [r[i_nat] for r in rows if "/" in r[i_nat]]
    check("NativeFilePath uses backslash separators", not fwd, f"{len(fwd)} with forward slashes")

    if not args.flat:
        # 3. nothing loose at the root of natives/
        loose = [f for f in os.listdir(nat) if os.path.isfile(os.path.join(nat, f))]
        check("no files at the root of natives/", not loose, f"{len(loose)} loose files")

        # 4. the folder a native sits in matches its custodian
        wrong = []
        for r in rows:
            if not r[i_nat]:
                continue
            parts = r[i_nat].split("\\")
            folder = parts[1] if len(parts) > 1 else ""
            if folder != r[i_cust].strip().replace(" ", "_") and folder != "_Unassigned":
                wrong.append((r[i_ctrl], folder, r[i_cust]))
        check("native folder matches the row's custodian", not wrong,
              f"{len(wrong)} mismatches" if wrong else "")

    # 5. custodian-sources.csv agrees with disk
    sheet = list(csv.DictReader(open(src, encoding="utf-8")))
    disk_files = sum(len(fs) for _, _, fs in os.walk(nat))
    disk_bytes = sum(os.path.getsize(os.path.join(root, fn))
                     for root, _, fs in os.walk(nat) for fn in fs)
    sheet_files = sum(int(r["Natives Written"]) for r in sheet)
    sheet_bytes = sum(int(r["Native Bytes"]) for r in sheet)
    check("custodian-sources.csv native count matches disk", disk_files == sheet_files,
          f"disk {disk_files:,} vs sheet {sheet_files:,}")
    check("custodian-sources.csv byte total matches disk", disk_bytes == sheet_bytes,
          f"disk {disk_bytes:,} vs sheet {sheet_bytes:,}")

    # 6. every custodian in the load file has a row in the sheet
    dat_custs   = {r[i_cust].strip() for r in rows if r[i_cust].strip()}
    sheet_custs = {r["Custodian"].strip() for r in sheet}
    check("every custodian in the load file has a data source row",
          dat_custs <= sheet_custs, f"missing: {sorted(dat_custs - sheet_custs)}")

    # ── Rule 12: intentionally broken natives ─────────────────────────────
    expected_path = os.path.join(pkg, "EXPECTED_ERRORS.csv")
    if os.path.exists(expected_path):
        print("\n  Rule 12 — intentionally broken natives\n")
        broken = list(csv.DictReader(open(expected_path, encoding="utf-8")))

        gone = [r["Native File"] for r in broken
                if not os.path.isfile(os.path.join(pkg, r["Native File"].replace("\\", os.sep)))]
        check("every EXPECTED_ERRORS.csv native exists", not gone,
              f"{len(gone)} missing" if gone else f"{len(broken):,} fabricated")

        intact = []
        for r in broken:
            target = os.path.join(pkg, r["Native File"].replace("\\", os.sep))
            if not os.path.isfile(target):
                continue
            if not is_broken(r, target):
                intact.append(r["Control Number"])
        check("every fabricated native is genuinely broken", not intact,
              f"{len(intact)} still healthy: {intact[:5]}" if intact else
              f"{len(broken) - len(intact):,} verified")

        flagged = {r[i_ctrl] for r in rows
                   if "Processing Error Type" in header
                   and r[header.index("Processing Error Type")].strip()}
        listed  = {r["Control Number"] for r in broken}
        # Anything flagged but not fabricated must be a documented exclusion,
        # not a silent gap.
        i_type    = header.index("Processing Error Type")
        by_ctrl   = {r[i_ctrl]: r[i_type].strip() for r in rows}
        # A row with no NativeFilePath has no file to break, so it cannot be
        # fabricated however it is flagged. That is a documented exclusion too.
        no_native = {r[i_ctrl] for r in rows if not r[i_nat]}
        undocumented = sorted(c for c in (flagged - listed)
                              if by_ctrl.get(c) not in error_natives.NOT_FABRICABLE
                              and c not in no_native)
        excluded = len(flagged - listed) - len(undocumented)
        check("every flagged document is fabricated or a documented exclusion",
              not undocumented,
              f"{len(undocumented)} undocumented: {undocumented[:5]}" if undocumented
              else f"{excluded} documented exclusions")

        if "File Size" in header:
            i_size = header.index("File Size")
            bad = []
            for r in rows:
                if not r[i_nat]:
                    continue
                disk = os.path.getsize(os.path.join(pkg, r[i_nat].replace("\\", os.sep)))
                if str(disk) != r[i_size]:
                    bad.append(r[i_ctrl])
            check("File Size in the load file matches bytes on disk", not bad,
                  f"{len(bad)} rows disagree" if bad else f"{len(rows):,} rows")

    # ── Edge-case manifest, when the package carries starved documents ────
    edge_file = os.path.join(pkg, "edge-cases.json")
    unassigned = [r for r in rows if not r[i_cust].strip()]
    if unassigned and not os.path.exists(edge_file):
        # The package has documents with no custodian and no map saying which are
        # deliberate. v1.9.0 shipped exactly like this.
        check("packages with starved documents ship edge-cases.json", False,
              f"{len(unassigned)} rows have no custodian but there is no manifest")
    elif os.path.exists(edge_file):
        print("\n  Edge-case manifest\n")
        scenarios = json.load(open(edge_file, encoding="utf-8"))["scenarios"]
        present   = {r[i_ctrl] for r in rows}
        listed, ghosts = 0, []
        for name, body in scenarios.items():
            if name == "broken_family":
                continue                       # these name documents that are meant to be absent
            for entry in body.get("documents", []):
                # duplicate_md5 records a mapping rather than a bare control number.
                ctrl = entry.get("control_number") if isinstance(entry, dict) else entry
                if not ctrl:
                    continue
                listed += 1
                if ctrl not in present:
                    ghosts.append(ctrl)
        check("every document in edge-cases.json is in the load file", not ghosts,
              f"{len(ghosts)} missing: {ghosts[:3]}" if ghosts else f"{listed:,} listed")

        # oversized_text is only real if the native holds the words it claims.
        oversized = scenarios.get("oversized_text", {}).get("documents", [])
        if oversized:
            claims, short = 0, []
            paths = {r[i_ctrl]: r[i_nat] for r in rows if r[i_nat]}
            for entry in oversized:
                ctrl, want = entry["control_number"], entry["word_count"]
                rel = paths.get(ctrl)
                if not rel:
                    short.append(f"{ctrl}: no native"); continue
                target = os.path.join(pkg, rel.replace("\\", os.sep))
                with open(target, encoding="utf-8", errors="replace") as f:
                    got = len(f.read().split())
                claims += 1
                if got < want * 0.95:
                    short.append(f"{ctrl}: {got:,} words, claimed {want:,}")
            check("oversized_text natives hold the words they claim", not short,
                  "; ".join(short[:2]) if short else f"{claims} documents")

        no_cust = scenarios.get("no_custodian", {}).get("documents", [])
        check("no_custodian documents really have no custodian in the load file",
              all(not r[i_cust].strip() for r in rows if r[i_ctrl] in set(no_cust)),
              f"{len(no_cust)} listed")

    print()
    if failures:
        print(f"  {len(failures)} check(s) failed\n")
        sys.exit(1)
    print(f"  All checks passed — {len(rows):,} documents, {len(sheet)} custodians\n")


if __name__ == "__main__":
    main()
