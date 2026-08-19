"""
Generate a gzipped TSV manifest of all files in the OIDA S3 bucket.

Usage:
    python scripts/fetch_manifest.py                  # writes manifest.tsv.gz
    python scripts/fetch_manifest.py --prefix f/f/b/  # subset only
    python scripts/fetch_manifest.py --out /tmp/oida.tsv.gz
"""
import argparse
import gzip
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BUCKET_URL        = "https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com"
NS                = "http://s3.amazonaws.com/doc/2006-03-01/"
PROGRESS_INTERVAL = 100_000

# Pre-compute namespace-qualified tag names used in every iteration
_TAG_CONTENTS  = f"{{{NS}}}Contents"
_TAG_KEY       = f"{{{NS}}}Key"
_TAG_SIZE      = f"{{{NS}}}Size"
_TAG_ETAG      = f"{{{NS}}}ETag"
_TAG_TRUNCATED = f"{{{NS}}}IsTruncated"
_TAG_TOKEN     = f"{{{NS}}}NextContinuationToken"


def _text(element, tag, default=""):
    """Text of a child element, or `default`.

    ElementTree returns None for a missing child, and `.text` is None for an empty
    one, so the direct `element.find(tag).text` this used to do raised
    AttributeError the first time S3 returned a listing without the tag.
    """
    found = element.find(tag)
    if found is None or found.text is None:
        return default
    return found.text


def fetch_manifest(prefix: str = "", outfile: str = "manifest.tsv.gz") -> None:
    count = 0
    token = None

    with gzip.open(outfile, "wt", encoding="utf-8") as f:
        f.write("key\tsize\tetag\n")
        while True:
            params = {"list-type": "2", "max-keys": "1000"}
            if prefix: params["prefix"] = prefix
            if token:  params["continuation-token"] = token
            url = f"{BUCKET_URL}/?{urllib.parse.urlencode(params)}"

            req = urllib.request.Request(url, headers={"User-Agent": "python/oida-registry"})
            with urllib.request.urlopen(req, timeout=30) as r:
                root = ET.fromstring(r.read())

            for obj in root.findall(_TAG_CONTENTS):
                key  = _text(obj, _TAG_KEY)
                size = _text(obj, _TAG_SIZE)
                etag = _text(obj, _TAG_ETAG).strip('"')
                f.write(f"{key}\t{size}\t{etag}\n")
                count += 1

            if count % PROGRESS_INTERVAL == 0:
                print(f"  {count:,} objects written...", flush=True)

            if _text(root, _TAG_TRUNCATED).lower() != "true":
                break
            token = _text(root, _TAG_TOKEN)

    print(f"Done — {count:,} objects → {outfile}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="", help="S3 key prefix to filter")
    parser.add_argument("--out", default="manifest.tsv.gz", help="Output file path")
    args = parser.parse_args()
    fetch_manifest(args.prefix, args.out)
