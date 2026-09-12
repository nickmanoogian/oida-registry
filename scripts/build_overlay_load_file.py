#!/usr/bin/env python3
"""Project a load file down to just the columns that needed a field creating.

Use this to populate the 24 fields from workspace_fields.py in a workspace whose
documents are already imported. Re-importing the whole load file would work, but
on the extra large tier that means re-extracting 274,158 text files, which is
hours. An overlay keyed on Control Number carries metadata only, so it has no
extraction stage at all and lands in minutes.

    python3 scripts/build_overlay_load_file.py \
        --in  load-packages/xlarge/load-file.dat \
        --out overlay.dat

Then import it in Overlay Only mode with Control Number as the overlay
identifier, and map only the columns it contains.

WHY IT IS ONLY THESE COLUMNS. In Overlay and Append/Overlay modes a blank cell
overwrites the existing value instead of being skipped, so an overlay that maps
more than it means to erases the pass before it. Emitting a narrow file makes
that mistake hard to make: there is nothing else in the file to map.

It also repairs the two renames for a load file generated before them, so an
already-built package does not have to be regenerated to be overlaid:

    Privilege Reason -> Privilege              (the stock multiple-choice field)
    Batch Name       -> Review Batch Name      ("Batch Status" is reserved)
    Batch Status     -> Review Batch Status
    Privileged       -> Yes/No                 (was ""/"Privileged")

This rewrites a column on every document, so do not run it underneath an import.

If an analysis over the result fails afterwards, see the note in
create_workspace_fields.py before suspecting the overlay: an Early Insights run
on our workspace failed twice at RunningStructuredAnalytics while its own
readiness check reported ready, and the same failure was reachable in a
workspace that had never held any of this data.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dat_format import DAT_FIELD_SEP, DAT_QUOTE  # noqa: E402
from workspace_fields import WORKSPACE_FIELDS  # noqa: E402

IDENTIFIER = "Control Number"

# Column names as a pre-rename load file spells them, and what they are now.
RENAMES = {
    "Privilege Reason": "Privilege",
    "Batch Name": "Review Batch Name",
    "Batch Status": "Review Batch Status",
}

# Columns that land in a field the template already had, so there is nothing to
# create, which is precisely why they would otherwise be missed here: they are
# not in WORKSPACE_FIELDS.
#
#   Privilege               was "Privilege Reason", which matched nothing, so its
#                           four reasons never imported at all.
#   File Type               used to carry the extension. The field's own
#                           description asks for "Adobe Portable Document
#                           Format", so it now carries the category.
#   File Extension          never in the load file.
#
# "Relativity Native Type" is NOT here on purpose. Relativity reserves it, and
# Import/Export does not offer it as a mapping target, so no load file and no
# overlay can populate it. Only processing writes that field.
STOCK_FIELDS_TO_BACKFILL = [
    "Privilege",
    "File Type",
    "File Extension",
]

# Named column sets, so a targeted repair does not mean hand-typing a column list
# and getting one of them subtly wrong. "fields" is the default and carries
# everything a stock template lacks; the rest are one rule each.
COLUMN_SETS = {
    # Everything from workspace_fields.py, plus the stock fields the load file
    # started addressing by the wrong name.
    "fields": [name for name, _t, _l, _why in WORKSPACE_FIELDS] + STOCK_FIELDS_TO_BACKFILL,

    # Rule 24. The four columns the direction pass rewrites, and only those: it is
    # the whole of what changed, verified by diffing the tier against a build with
    # --no-direction. Email CC is deliberately absent because Rule 20 set it and
    # Rule 24 does not touch it, and in Overlay mode a column you did not mean to
    # map is a column you erase.
    "direction": [
        "Email From",
        "Email From (SMTP Address)",
        "Email To",
        "Email To (SMTP Address)",
    ],
}


def _split(line):
    return [c.strip(DAT_QUOTE) for c in line.split(DAT_FIELD_SEP)]


def _join(values):
    return DAT_FIELD_SEP.join(DAT_QUOTE + str(v) + DAT_QUOTE for v in values) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", required=True, help="the full load-file.dat")
    ap.add_argument("--out", dest="dst", required=True, help="overlay .dat to write")
    ap.add_argument("--columns", default="fields", choices=sorted(COLUMN_SETS),
                    help="which column set to project (default: fields)")
    args = ap.parse_args()

    wanted = COLUMN_SETS[args.columns]

    with open(args.src, encoding="utf-8") as f:
        header = _split(f.readline().rstrip("\n"))
        # A pre-rename file is understood by mapping its old spelling forward.
        renamed = [RENAMES.get(c, c) for c in header]
        index = {c: i for i, c in enumerate(renamed)}

        missing = [c for c in wanted if c not in index]
        if IDENTIFIER not in index:
            sys.exit(f"No {IDENTIFIER} column in {args.src}")
        if missing:
            print(f"  not in this load file, skipping: {', '.join(missing)}")

        cols = [IDENTIFIER] + [c for c in wanted if c in index]
        # "Privileged" is emitted by older builds as "" or the word "Privileged".
        # A Relativity Yes/No field rejects the word, so normalise on the way out.
        priv = cols.index("Privileged") if "Privileged" in cols else -1

        with open(args.dst, "w", encoding="utf-8", newline="") as out:
            out.write(_join(cols))
            rows = 0
            for line in f:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                fields = _split(line)
                if len(fields) != len(header):
                    continue
                values = [fields[index[c]] for c in cols]
                if priv >= 0 and values[priv] not in ("Yes", "No"):
                    values[priv] = "Yes" if values[priv] else "No"
                out.write(_join(values))
                rows += 1

    size = os.path.getsize(args.dst)
    print(f"  {rows:,} rows x {len(cols)} columns -> {args.dst} ({size/1e6:.1f} MB)")
    print(f"  columns: {', '.join(cols)}")


if __name__ == "__main__":
    sys.exit(main())
