#!/usr/bin/env python3
"""
chunk_load_package.py — Split a built package into import-sized batches

Import/Export takes a load file and one ZIP of natives and text through the
browser. That path has a ceiling, and the ceiling is not documented anywhere we
could find. What we measured on one instance:

    small     1.2 MB dat +  11 MB zip    completed in minutes
    medium    8.3 MB dat + 5.4 MB zip    completed
    large     107 MB dat +  90 MB zip    completed
    xlarge    199 MB dat + 168 MB zip    FAILED after 24.6 hours of retries

The xlarge failure came back as "The job failed after reaching maximum number of
retry attempts. The system was unable to retrieve the last job error." Relativity
could not name its own error, which is why the size pattern is the evidence rather
than the message.

So: split the package into batches that each land inside the range that works.
Each batch is a complete, self consistent import. The critical part is that the
rows and the files move together. A batch whose load file references
text/DOC-0123456.txt and whose ZIP does not contain it imports a document with no
text and reports success, which is the quietest possible way to lose data.

    python3 scripts/chunk_load_package.py --in load-packages/xlarge --out batches --rows 55000

Each batch directory holds a load-file.dat and the text/ and natives/ trees for
exactly its own rows, ready to zip and import Append Only.
"""

import argparse
import csv
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dat_format import DAT_FIELD_SEP, DAT_QUOTE  # noqa: E402


def _split(line):
    return [c.strip(DAT_QUOTE) for c in line.split(DAT_FIELD_SEP)]


def _join(values):
    return DAT_FIELD_SEP.join(DAT_QUOTE + str(v) + DAT_QUOTE for v in values) + "\n"


def _rewrite_custodian_sources(src, bdir, header, part):
    """Recount custodian-sources.csv against this batch's rows only.

    The sheet carries one row per data source and custodian pair with three
    numbers: Documents, Natives Written and Native Bytes. Copied verbatim into a
    batch, all three describe a corpus the batch does not contain, and
    validate_load_package compares the last two against what is actually on
    disk. Recount them from the files this batch really holds, and drop the pairs
    that contributed no rows to it.
    """
    src_csv = os.path.join(src, "custodian-sources.csv")
    if not os.path.exists(src_csv):
        return
    with open(src_csv, newline="", encoding="utf-8") as f:
        sheet = list(csv.DictReader(f))
    if not sheet:
        return
    fields = list(sheet[0].keys())

    def col(name):
        return header.index(name) if name in header else None

    ci_cust, ci_src = col("Custodian"), col("Data Source")
    ci_nat = col("NativeFilePath")

    counts: dict = {}
    for r in part:
        key = (r[ci_src] if ci_src is not None else "",
               r[ci_cust] if ci_cust is not None else "")
        agg = counts.setdefault(key, {"docs": 0, "natives": 0, "bytes": 0})
        agg["docs"] += 1
        if ci_nat is None or not r[ci_nat]:
            continue
        # Measured off the batch directory, because that is what the validator
        # walks. A native the copy step could not find is not in either number.
        on_disk = os.path.join(bdir, r[ci_nat].replace("\\", os.sep))
        if os.path.exists(on_disk):
            agg["natives"] += 1
            agg["bytes"] += os.path.getsize(on_disk)

    out_rows = []
    for row in sheet:
        key = (row.get("Data Source", ""), row.get("Custodian", ""))
        agg = counts.get(key)
        if not agg:
            continue          # this pair contributed nothing to this batch
        if "Documents" in row:
            row["Documents"] = str(agg["docs"])
        if "Natives Written" in row:
            row["Natives Written"] = str(agg["natives"])
        if "Native Bytes" in row:
            row["Native Bytes"] = str(agg["bytes"])
        out_rows.append(row)

    with open(os.path.join(bdir, "custodian-sources.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", required=True, help="a built package directory")
    ap.add_argument("--out", dest="dst", required=True, help="where to write the batches")
    ap.add_argument("--rows", type=int, default=55000, help="rows per batch (default 55000)")
    args = ap.parse_args()

    dat = os.path.join(args.src, "load-file.dat")
    if not os.path.exists(dat):
        sys.exit(f"No load-file.dat in {args.src}")

    with open(dat, encoding="utf-8") as f:
        header_line = f.readline().rstrip("\n")
        header = _split(header_line)
        rows = [r for r in (_split(l.rstrip("\n")) for l in f if l.strip())
                if len(r) == len(header)]

    # The path columns are what makes a batch self consistent: every file a row
    # names has to travel in that row's batch.
    path_cols = [header.index(c) for c in ("NativeFilePath", "ExtractedTextFilePath")
                 if c in header]
    ctrl_col = header.index("Control Number")

    os.makedirs(args.dst, exist_ok=True)
    total = len(rows)
    batches = (total + args.rows - 1) // args.rows
    print(f"  {total:,} rows -> {batches} batches of up to {args.rows:,}\n")

    for i in range(batches):
        part = rows[i * args.rows:(i + 1) * args.rows]
        bdir = os.path.join(args.dst, f"batch-{i+1:02d}")
        os.makedirs(bdir, exist_ok=True)

        with open(os.path.join(bdir, "load-file.dat"), "w",
                  encoding="utf-8", newline="") as out:
            out.write(_join(header))
            for r in part:
                out.write(_join(r))

        copied = missing = 0
        for r in part:
            for ci in path_cols:
                rel = r[ci].replace("\\", os.sep)
                if not rel:
                    continue
                src = os.path.join(args.src, rel)
                if not os.path.exists(src):
                    missing += 1
                    continue
                dest = os.path.join(bdir, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                # copy2, not copyfile: build_load_package dates every native and
                # sidecar to its document's date and validate_load_package checks
                # it, so a batch built with copyfile fails its own validator.
                shutil.copy2(src, dest)
                copied += 1

        # Everything that is not a row: the field creation script a reader is told
        # to run, the import instructions, the ground truth. A batch without these
        # is a pile of documents rather than a package, and the script in
        # particular is the difference between 60 mapped columns and 35.
        for name in ("scripts", "IMPORT_README.txt",
                     "pi-ground-truth.csv", "entities.json", "findings.json",
                     "language-mix.json", "data-sources.json", "collection-shape.json",
                     "mail-direction.json", "edge-cases.json", "EXPECTED_ERRORS.csv"):
            s_path = os.path.join(args.src, name)
            if not os.path.exists(s_path):
                continue
            d_path = os.path.join(bdir, name)
            if os.path.isdir(s_path):
                shutil.copytree(s_path, d_path, dirs_exist_ok=True)
            else:
                shutil.copy2(s_path, d_path)

        # custodian-sources.csv is the one ancillary file that cannot be copied.
        # Its document counts and byte totals describe the whole corpus, and the
        # validator compares them against what is on disk, so a copied sheet
        # fails every batch with "disk 15 vs sheet 40". Recount it per batch.
        _rewrite_custodian_sources(args.src, bdir, header, part)

        # A batch is a slice, so the ground truth it inherits describes documents
        # that live in other batches. Record the slice so the validator can scope
        # its whole-corpus checks to the rows actually present.
        with open(os.path.join(bdir, "batch-manifest.json"), "w") as bm:
            json.dump({"batch": i + 1, "of": batches, "rows": len(part),
                       "source_package": os.path.abspath(args.src),
                       "control_numbers": [r[ctrl_col] for r in part]}, bm)

        size = os.path.getsize(os.path.join(bdir, "load-file.dat"))
        note = f"   {missing} referenced files MISSING" if missing else ""
        print(f"  batch-{i+1:02d}  {len(part):>7,} rows  "
              f"{size/1e6:6.1f} MB dat  {copied:>7,} files{note}")

    print(f"\n  written to {args.dst}")
    print("  zip each batch's text/ and natives/ together, then import Append Only")


if __name__ == "__main__":
    sys.exit(main())
