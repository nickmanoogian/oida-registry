#!/usr/bin/env python3
"""
test_error_scenarios.py — Drive every error scenario against every file extension

The generator picks scenarios from metadata, so which extension meets which scenario
depends on the seed and the tier. A scenario that works on .eml and crashes on .txt
stays hidden until the day it does not: password_zip staged its payload beside the
output, so on a .txt row the payload and the archive were the same path and zip
exited 12.

This walks the whole matrix so that class of bug fails here rather than mid-build.

Usage:
  python scripts/test_error_scenarios.py
"""

import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import error_natives

FALLBACK_EXTS = ["eml", "msg", "docx", "doc", "xlsx", "pdf", "rsmf", "txt", "csv",
                 "jpg", "png", "tiff", "zip", "pst", "numbers", "mdb", "ics", "mp3"]


def extensions(tier_dir):
    docs = os.path.join(tier_dir, "documents.csv")
    if not os.path.exists(docs):
        return FALLBACK_EXTS
    with open(docs, encoding="utf-8") as f:
        found = {r["File Extension"] for r in csv.DictReader(f) if r["File Extension"]}
    return sorted(found | set(FALLBACK_EXTS))


def main():
    tier_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join("mock-data", "small")
    exts     = extensions(tier_dir)
    failures = []
    checked  = 0

    print(f"\n  Error scenarios x file extensions"
          f"  ({len(error_natives.SCENARIOS)} x {len(exts)})\n")

    with tempfile.TemporaryDirectory() as tmp:
        for err in sorted(error_natives.SCENARIOS):
            broke = []
            for ext in exts:
                doc = {"Control Number": "DOC-TEST", "File Extension": ext,
                       "Processing Error Type": err, "Custodian": "Test",
                       "File Type Category": "Test"}
                path = os.path.join(tmp, f"probe.{ext}")
                with open(path, "wb") as f:
                    f.write(b"healthy content " * 64)
                try:
                    record = error_natives.fabricate(doc, path, b"healthy content " * 64)
                    if record is None:
                        broke.append(f"{ext}: no record returned")
                    elif not os.path.exists(path):
                        broke.append(f"{ext}: no file written")
                except Exception as e:
                    broke.append(f"{ext}: {type(e).__name__} {e}")
                checked += 1
            status = "ok  " if not broke else "FAIL"
            print(f"  [{status}] {err}" + (f"  — {broke[:2]}" if broke else ""))
            failures.extend(broke)

    print()
    if failures:
        print(f"  {len(failures)} of {checked} combinations failed\n")
        sys.exit(1)
    print(f"  All {checked} combinations produced a broken file\n")


if __name__ == "__main__":
    main()
