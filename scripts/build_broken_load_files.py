#!/usr/bin/env python3
"""
build_broken_load_files.py — Load files that fail at import, not at processing

Everything else in this repo breaks later in the pipeline: natives that fail
processing (Rule 12), documents that process cleanly with an input missing
(Rule 13). Nothing breaks at the import boundary itself.

This emits one mutated copy of a package's load-file.dat per scenario. Natives are
untouched and not duplicated: each variant points at the same relative paths, so a
tester unzips the clean package and drops one .dat in beside its natives/ folder.

Every variant is opt-in and lives in its own directory. The packages themselves are
never modified.

Usage:
  python scripts/build_broken_load_files.py
  python scripts/build_broken_load_files.py --package load-packages/small --out load-packages/broken-load-files
  python scripts/build_broken_load_files.py --scenario duplicate-control
"""

import argparse
import csv
import os
import shutil
import sys

DAT_SEP   = chr(254)   # þ
DAT_QUOTE = chr(255)   # ÿ

MUTATED_ROWS = 2       # keep each fault isolated and easy to find


def read_dat(path):
    with open(path, encoding="utf-8") as f:
        rows = [[v.strip(DAT_QUOTE) for v in line.rstrip("\n").split(DAT_SEP)] for line in f]
    return rows[0], rows[1:]


def write_dat(path, header, rows, encoding="utf-8", raw_lines=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    def fmt(values):
        return DAT_SEP.join(DAT_QUOTE + str(v) + DAT_QUOTE for v in values) + "\n"
    with open(path, "w", encoding=encoding, errors="replace", newline="") as f:
        f.write(fmt(header))
        for i, row in enumerate(rows):
            f.write(raw_lines[i] if raw_lines and raw_lines[i] is not None else fmt(row))


# ── scenarios ─────────────────────────────────────────────────────────────
# Each returns (rows, raw_lines, encoding, note, affected control numbers).

def missing_native(header, rows):
    i = header.index("NativeFilePath")
    hit = [r for r in rows if r[i]][:MUTATED_ROWS]
    for r in hit:
        r[i] = "natives\\Michael_Brennan\\2099\\01\\DOC-9999999.eml"
    return rows, None, "utf-8", "NativeFilePath points at a file that is not in the package", hit


def duplicate_control(header, rows):
    i = header.index("BegDoc#")
    donor, victims = rows[0], rows[1:1 + MUTATED_ROWS]
    for r in victims:
        r[i] = donor[i]
    return rows, None, "utf-8", f"Control Number {donor[i]} appears on {MUTATED_ROWS + 1} rows", victims


def bad_date(header, rows):
    i = header.index("Date")
    hit = rows[:MUTATED_ROWS]
    for n, r in enumerate(hit):
        r[i] = "13/45/2011" if n == 0 else "not a date"
    return rows, None, "utf-8", "impossible and non-numeric values in a date field", hit


def unqualified_delimiter(header, rows):
    i = header.index("Email Subject") if "Email Subject" in header else header.index("Subject")
    hit = rows[:MUTATED_ROWS]
    for r in hit:
        r[i] = f"Q4 numbers {DAT_SEP} see attached"     # raw column separator inside a value
    return rows, None, "utf-8", "raw column separator inside a field value, so the row gains a column", hit


def encoding_mismatch(header, rows):
    i = header.index("Custodian")
    hit = rows[:MUTATED_ROWS]
    for r in hit:
        r[i] = "Michał Surówka"
    return rows, None, "latin-1", "non-ASCII names written as Latin-1 in a file read as UTF-8, no BOM", hit


def short_row(header, rows):
    hit = rows[:MUTATED_ROWS]
    raw = [None] * len(rows)
    for r in hit:
        idx = rows.index(r)
        trimmed = r[: max(1, len(header) - 6)]
        raw[idx] = DAT_SEP.join(DAT_QUOTE + str(v) + DAT_QUOTE for v in trimmed) + "\n"
    return rows, raw, "utf-8", f"row carries {max(1, len(header) - 6)} fields against a {len(header)} field header", hit


def blank_required(header, rows):
    i = header.index("BegDoc#")
    hit = rows[:MUTATED_ROWS]
    for r in hit:
        r[i] = ""
    return rows, None, "utf-8", "Control Number is empty", hit


SCENARIOS = {
    "missing-native":        (missing_native,        "Native file not found at the specified path"),
    "duplicate-control":     (duplicate_control,     "Duplicate identifier, the import should reject or overwrite"),
    "bad-date":              (bad_date,              "Date parse failure on the mapped date field"),
    "unqualified-delimiter": (unqualified_delimiter, "Column count mismatch on the affected row"),
    "encoding":              (encoding_mismatch,     "Mojibake, or a decode error on load"),
    "short-row":             (short_row,             "Column count mismatch, fewer fields than the header"),
    "blank-required":        (blank_required,        "Missing required identifier"),
}

README = """LOAD FILES THAT FAIL AT IMPORT
==============================

Each folder holds one load-file.dat with a single deliberate fault. Natives are not
duplicated: every variant points at the same relative paths as the clean package.

HOW TO USE ONE
  1. Unzip the clean package (load-packages/small.zip).
  2. Copy one variant's load-file.dat over the clean one, or point the import at
     the variant directly with the package's natives/ folder as the native root.
  3. Import. Record what Relativity says, and how far it gets.

manifest.csv lists every variant: the scenario, the fault, the rows affected by
control number, and the failure that is expected.

WHAT TO REPORT
  Not that the import failed. That is the point. Report whether the error told you
  which row was at fault, whether a partial import left the workspace in a usable
  state, and whether anything downstream noticed.

THE CLEAN PACKAGE IS STILL THE DEFAULT
  load-packages/small.zip imports without complaint. These variants are opt in and
  exist only for failure path testing.

VARIANTS
"""


def build(package, out_dir, only):
    dat = os.path.join(package, "load-file.dat")
    if not os.path.exists(dat):
        sys.exit(f"ERROR: {dat} not found. Build the package first (make load-small).")

    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    manifest = []
    names = [only] if only else list(SCENARIOS)
    print(f"\n  Source package: {package}")
    print(f"  Output:         {out_dir}\n")

    for name in names:
        fn, expected = SCENARIOS[name]
        header, rows = read_dat(dat)                       # fresh copy per scenario
        rows, raw, encoding, note, hit = fn(header, rows)
        target = os.path.join(out_dir, name, "load-file.dat")
        write_dat(target, header, rows, encoding=encoding, raw_lines=raw)
        ctrls = [r[header.index("BegDoc#")] or "(blanked)" for r in hit]
        manifest.append({
            "Scenario": name,
            "Load File": os.path.join(name, "load-file.dat"),
            "Fault": note,
            "Rows Affected": len(hit),
            "Control Numbers": "; ".join(ctrls),
            "Expected Failure": expected,
        })
        print(f"  [{name:<22}] {note}")

    man_path = os.path.join(out_dir, "manifest.csv")
    with open(man_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        w.writeheader(); w.writerows(manifest)

    with open(os.path.join(out_dir, "README.txt"), "w") as f:
        f.write(README)
        for m in manifest:
            f.write(f"  {m['Scenario']:<22} {m['Fault']}\n")

    print(f"\n  {len(manifest)} variants + manifest.csv written to {out_dir}\n")


# ── verification ──────────────────────────────────────────────────────────
# A "broken" load file that parses cleanly is the same trap as a healthy native
# behind an error flag, so each variant is checked against its own signature.

def verify(out_dir, package):
    man = os.path.join(out_dir, "manifest.csv")
    if not os.path.exists(man):
        sys.exit(f"ERROR: {man} not found. Build the variants first.")
    rows_ok, failures = 0, []

    print(f"\n  Verifying {out_dir}\n")
    for m in csv.DictReader(open(man, encoding="utf-8")):
        name = m["Scenario"]
        path = os.path.join(out_dir, m["Load File"])
        raw  = open(path, "rb").read()
        ok, detail = True, ""

        if name == "encoding":
            try:
                raw.decode("utf-8")
                ok, detail = False, "file still decodes as UTF-8"
            except UnicodeDecodeError:
                detail = "undecodable as UTF-8, as intended"
        else:
            text   = raw.decode("utf-8", "replace")
            lines  = [l for l in text.split("\n") if l]
            fields = [l.split(DAT_SEP) for l in lines]
            header, body = fields[0], fields[1:]
            widths = {len(r) for r in body}

            if name == "missing-native":
                i = header.index(DAT_QUOTE + "NativeFilePath" + DAT_QUOTE)
                claimed = [r[i].strip(DAT_QUOTE) for r in body]
                gone = [c for c in claimed
                        if c and not os.path.exists(os.path.join(package, c.replace("\\", os.sep)))]
                ok, detail = bool(gone), f"{len(gone)} rows point at a file that is not there"
            elif name == "duplicate-control":
                i = header.index(DAT_QUOTE + "BegDoc#" + DAT_QUOTE)
                ctrls = [r[i] for r in body]
                dupes = len(ctrls) - len(set(ctrls))
                ok, detail = dupes > 0, f"{dupes} duplicated control numbers"
            elif name == "bad-date":
                i = header.index(DAT_QUOTE + "Date" + DAT_QUOTE)
                bad = [r[i].strip(DAT_QUOTE) for r in body
                       if r[i].strip(DAT_QUOTE) and not r[i].strip(DAT_QUOTE)[:4].isdigit()]
                ok, detail = bool(bad), f"{len(bad)} unparseable dates, e.g. {bad[:1]}"
            elif name in ("unqualified-delimiter", "short-row"):
                off = [w for w in widths if w != len(header)]
                ok, detail = bool(off), f"row widths present: {sorted(widths)} against a {len(header)} field header"
            elif name == "blank-required":
                i = header.index(DAT_QUOTE + "BegDoc#" + DAT_QUOTE)
                blanks = [r for r in body if r[i].strip(DAT_QUOTE) == ""]
                ok, detail = bool(blanks), f"{len(blanks)} rows with an empty control number"

        print(f"  [{'ok  ' if ok else 'FAIL'}] {name:<22} {detail}")
        rows_ok += ok
        if not ok:
            failures.append(name)

    print()
    if failures:
        print(f"  {len(failures)} variant(s) are not actually broken: {failures}\n")
        sys.exit(1)
    print(f"  All {rows_ok} variants carry the fault they claim\n")


def main():
    p = argparse.ArgumentParser(description="Build load files that fail at import")
    p.add_argument("--package", default=os.path.join("load-packages", "small"),
                   help="Built package to take the clean load-file.dat from")
    p.add_argument("--out", default=os.path.join("load-packages", "broken-load-files"))
    p.add_argument("--scenario", choices=sorted(SCENARIOS), default=None,
                   help="Build a single variant instead of all of them")
    p.add_argument("--verify", action="store_true",
                   help="Check that every built variant carries the fault it claims")
    args = p.parse_args()
    if args.verify:
        verify(args.out, args.package)
    else:
        build(args.package, args.out, args.scenario)


if __name__ == "__main__":
    main()
