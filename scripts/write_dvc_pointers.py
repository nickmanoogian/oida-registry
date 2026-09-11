#!/usr/bin/env python3
"""
write_dvc_pointers.py — Point the tier pointers at a release, from the release

The `.dvc` pointers under `mock-data/` were hand maintained, and hand maintained
means they drift: they sat on the v1.3.0 assets for ten releases, so
`make mock-medium` handed people a tier that predated the custodian folder
structure, the attachment records, `Record Type` and every seeded field. Nothing
caught it because a pointer is just a URL and a byte count, and both were
internally consistent.

This writes every pointer from the files that are about to be published, so the
URL, the byte count and the tier they describe cannot disagree. Run it after
staging the assets and before creating the release; the sizes come from the local
files, which are the same bytes GitHub will serve.

Usage:
  python scripts/write_dvc_pointers.py --tag v1.14.0 --assets /path/to/staged
  python scripts/write_dvc_pointers.py --tag v1.14.0 --assets DIR --check
"""

import argparse
import os
import sys

from tier_files import TIER_FILES

REPO = "https://github.com/nickmanoogian/oida-registry"


TEMPLATE = """deps:
- path: {url}
  size: {size}
outs:
- path: {name}
  size: {size}
  isexec: false
"""


def main():
    ap = argparse.ArgumentParser(description="Write mock-data .dvc pointers for a release")
    ap.add_argument("--tag", required=True, help="Release tag, e.g. v1.14.0")
    ap.add_argument("--assets", required=True,
                    help="Directory holding the staged assets, named {tier}-{file}")
    ap.add_argument("--check", action="store_true",
                    help="Report what would change without writing anything")
    args = ap.parse_args()

    missing, written, unchanged = [], [], []
    for tier, names in TIER_FILES.items():
        for name in names:
            asset = f"{tier}-{name}"
            src   = os.path.join(args.assets, asset)
            if not os.path.exists(src):
                missing.append(asset)
                continue
            body = TEMPLATE.format(url=f"{REPO}/releases/download/{args.tag}/{asset}",
                                   size=os.path.getsize(src), name=name)
            dest = os.path.join("mock-data", tier, f"{name}.dvc")
            before = open(dest).read() if os.path.exists(dest) else ""
            if before == body:
                unchanged.append(dest)
                continue
            if not args.check:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w") as f:
                    f.write(body)
            written.append(dest)

    if missing:
        print(f"  ERROR: {len(missing)} asset(s) not staged: {missing}")
        sys.exit(1)

    verb = "would change" if args.check else "written"
    for path in written:
        print(f"  {verb}: {path}")
    if unchanged:
        print(f"  unchanged: {len(unchanged)}")
    print(f"\n  {len(written)} pointer(s) {verb}, all at {args.tag}\n")


if __name__ == "__main__":
    main()
