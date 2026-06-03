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

BUCKET_URL = "https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com"
NS = "http://s3.amazonaws.com/doc/2006-03-01/"


def fetch_manifest(prefix: str = "", outfile: str = "manifest.tsv.gz") -> None:
    count = 0
    token = None

    with gzip.open(outfile, "wt", encoding="utf-8") as f:
        f.write("key\tsize\tetag\n")
        while True:
            url = f"{BUCKET_URL}/?list-type=2&max-keys=1000"
            if prefix:
                url += f"&prefix={urllib.parse.quote(prefix)}"
            if token:
                url += f"&continuation-token={urllib.parse.quote(token)}"

            req = urllib.request.Request(url, headers={"User-Agent": "python/oioda-registry"})
            with urllib.request.urlopen(req, timeout=30) as r:
                root = ET.fromstring(r.read())

            for obj in root.findall(f"{{{NS}}}Contents"):
                key  = obj.find(f"{{{NS}}}Key").text
                size = obj.find(f"{{{NS}}}Size").text
                etag = obj.find(f"{{{NS}}}ETag").text.strip('"')
                f.write(f"{key}\t{size}\t{etag}\n")
                count += 1

            if count % 100_000 == 0:
                print(f"  {count:,} objects written...", flush=True)

            if root.find(f"{{{NS}}}IsTruncated").text.lower() != "true":
                break
            token = root.find(f"{{{NS}}}NextContinuationToken").text

    print(f"Done — {count:,} objects → {outfile}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="", help="S3 key prefix to filter")
    parser.add_argument("--out", default="manifest.tsv.gz", help="Output file path")
    args = parser.parse_args()
    fetch_manifest(args.prefix, args.out)
