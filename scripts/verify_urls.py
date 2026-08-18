"""
Verify that every remote URL this registry depends on is still reachable.

Checks the `path: https://...` dependency in every .dvc file (repo root,
data-products/, metadata/, samples/, load-packages/), plus GitHub release
artifacts that the Makefile pulls directly.

A pointer may reference a release that has not been published yet: a PR that
prepares a release repoints its .dvc files at the new tag, and those assets only
exist once the release goes live. Those are reported as PENDING rather than
failures on pull_request runs, and as failures everywhere else — so a pointer
that reaches main without its release being published still gets caught by the
weekly run.

Usage:
    python scripts/verify_urls.py
    python scripts/verify_urls.py --allow-pending   # never fail on unpublished releases

Exits non-zero if any URL is unreachable. Used by `make verify` and the
weekly S3 Health Check workflow.
"""
import os
import re
import sys
import urllib.request

RELEASE_ASSET = re.compile(r"^https://github\.com/([^/]+/[^/]+)/releases/download/([^/]+)/")
_tag_cache = {}

DVC_FOLDERS = [".", "data-products", "metadata", "samples", "load-packages"]

RELEASE_URLS = [
    ("mock-data/medium documents (v1.3.0)", "https://github.com/nickmanoogian/oioda-registry/releases/download/v1.3.0/v13-medium-documents.csv"),
    ("mock-data/large documents (v1.3.0)",  "https://github.com/nickmanoogian/oioda-registry/releases/download/v1.3.0/v13-large-documents.csv.gz"),
]


def release_published(url):
    """True if the release tag behind an asset URL exists and is public.

    A draft release is invisible to an anonymous request, so its tag page 404s.
    That is exactly the signal we want: the assets are not downloadable yet.
    """
    m = RELEASE_ASSET.match(url)
    if not m:
        return True                       # not a release asset, nothing to defer
    repo, tag = m.group(1), m.group(2)
    if (repo, tag) not in _tag_cache:
        tag_url = f"https://github.com/{repo}/releases/tag/{tag}"
        try:
            req = urllib.request.Request(tag_url, method="HEAD",
                  headers={"User-Agent": "oioda-registry-healthcheck"})
            with urllib.request.urlopen(req, timeout=15) as r:
                _tag_cache[(repo, tag)] = r.status == 200
        except Exception:
            _tag_cache[(repo, tag)] = False
    return _tag_cache[(repo, tag)]


def head(url, label, failures, pending):
    def unreachable(detail):
        # A missing asset under a tag that does not exist yet is a release
        # waiting to be published, not a broken link.
        if not release_published(url):
            tag = RELEASE_ASSET.match(url).group(2)
            print(f"  ⋯ PEND {label}  (release {tag} is not published yet)")
            pending.append((label, tag))
        else:
            print(f"  ✗ {detail}  {label}")
            failures.append((label, detail))

    try:
        req = urllib.request.Request(url, method="HEAD",
              headers={"User-Agent": "oioda-registry-healthcheck"})
        with urllib.request.urlopen(req, timeout=15) as r:
            ok = r.status == 200
        if ok:
            print(f"  ✓ {r.status}  {label}")
        else:
            unreachable(str(r.status))
    except Exception as e:
        unreachable(f"ERR ({e})")


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
    allow_pending = ("--allow-pending" in sys.argv
                     or os.environ.get("GITHUB_EVENT_NAME") == "pull_request")
    failures = []
    pending  = []
    checked  = 0

    for folder in DVC_FOLDERS:
        if not os.path.isdir(folder):
            continue
        print(f"── {folder}/ .dvc URLs ──" if folder != "." else "── root .dvc URLs ──")
        for url, label in dvc_urls(folder):
            head(url, label, failures, pending)
            checked += 1

    print("\n── Release artifact URLs ──")
    for label, url in RELEASE_URLS:
        head(url, label, failures, pending)
        checked += 1

    if pending:
        verb = "tolerated" if allow_pending else "NOT tolerated outside a pull request"
        print(f"\n{len(pending)} pointer(s) awaiting an unpublished release ({verb}):")
        for name, tag in pending:
            print(f"  {name}: release {tag} is still a draft or does not exist")
        if not allow_pending:
            failures.extend((n, f"release {t} not published") for n, t in pending)

    if failures:
        print(f"\n{checked} URLs checked, {len(failures)} failure(s):")
        for name, err in failures:
            print(f"  {name}: {err}")
        sys.exit(1)

    suffix = f", {len(pending)} awaiting release" if pending else ""
    print(f"\n{checked} URLs checked, all reachable{suffix}.")


if __name__ == "__main__":
    main()
