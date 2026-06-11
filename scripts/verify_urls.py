"""
Verify that every remote URL this registry depends on is still reachable.

Checks the `path: https://...` dependency in every .dvc file (repo root,
data-products/, metadata/, samples/, load-packages/), plus GitHub release
artifacts that the Makefile pulls directly.

Usage:
    python scripts/verify_urls.py

Exits non-zero if any URL is unreachable. Used by `make verify` and the
weekly S3 Health Check workflow.
"""
import os
import sys
import urllib.request

DVC_FOLDERS = [".", "data-products", "metadata", "samples", "load-packages"]

RELEASE_URLS = [
    ("mock-data/medium documents (v1.3.0)", "https://github.com/nickmanoogian/oioda-registry/releases/download/v1.3.0/v13-medium-documents.csv"),
    ("mock-data/large documents (v1.3.0)",  "https://github.com/nickmanoogian/oioda-registry/releases/download/v1.3.0/v13-large-documents.csv.gz"),
]


def head(url, label, failures):
    try:
        req = urllib.request.Request(url, method="HEAD",
              headers={"User-Agent": "oioda-registry-healthcheck"})
        with urllib.request.urlopen(req, timeout=15) as r:
            ok = r.status == 200
        print(f"  {'✓' if ok else '✗'} {r.status}  {label}")
        if not ok:
            failures.append((label, r.status))
    except Exception as e:
        print(f"  ✗ ERR  {label}  ({e})")
        failures.append((label, str(e)))


def dvc_urls(folder):
    for fname in sorted(os.listdir(folder)):
        if not fname.endswith(".dvc") or not os.path.isfile(os.path.join(folder, fname)):
            continue
        with open(os.path.join(folder, fname)) as f:
            for line in f:
                line = line.strip().lstrip("- ")
                if line.startswith("path: https://"):
                    label = fname if folder == "." else f"{folder}/{fname}"
                    yield line.split("path: ", 1)[1], label


def main():
    failures = []
    checked = 0

    for folder in DVC_FOLDERS:
        if not os.path.isdir(folder):
            continue
        print(f"── {folder}/ .dvc URLs ──" if folder != "." else "── root .dvc URLs ──")
        for url, label in dvc_urls(folder):
            head(url, label, failures)
            checked += 1

    print("\n── Release artifact URLs ──")
    for label, url in RELEASE_URLS:
        head(url, label, failures)
        checked += 1

    if failures:
        print(f"\n{checked} URLs checked, {len(failures)} failure(s):")
        for name, err in failures:
            print(f"  {name}: {err}")
        sys.exit(1)
    print(f"\n{checked} URLs checked, all reachable.")


if __name__ == "__main__":
    main()
