#!/usr/bin/env python3
"""
validate_load_package.py — Verify a built load package conforms to RULES.md Rule 11

Checks the package on disk, not the source metadata: that every NativeFilePath in
load-file.dat resolves to a real file, that the folder a native sits in matches the
custodian on its row, that nothing was dumped at the root of natives/, and that
custodian-sources.csv agrees with what is actually on disk.

Usage:
  python scripts/validate_load_package.py load-packages/small
  python scripts/validate_load_package.py load-packages/small --flat
"""

import argparse, csv, os, sys

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

    print()
    if failures:
        print(f"  {len(failures)} check(s) failed\n")
        sys.exit(1)
    print(f"  All checks passed — {len(rows):,} documents, {len(sheet)} custodians\n")


if __name__ == "__main__":
    main()
