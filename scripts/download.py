"""
Download OIDA files directly from the public S3 bucket without DVC.

Usage:
    # list available datasets
    python scripts/download.py --list

    # download one file
    python scripts/download.py pennsaid_bydates.csv

    # download multiple files
    python scripts/download.py prescribers.csv mnk_customer_orders.csv

    # download to a specific directory
    python scripts/download.py pennsaid_bydates.csv --out ./data/
"""
import argparse
import os
import urllib.request

BUCKET = "https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com"

DATASETS = {
    "duexis_bydates.csv":                              ("data-products/duexis_bydates.csv",                            104_867_213),
    "exalgo_bydates.csv":                              ("data-products/exalgo_bydates.csv",                          1_265_140_167),
    "image_collection_version_1.zip":                  ("data-products/image_collection_version_1.zip",               1_453_563_446),
    "insys_authorized_rx.csv":                         ("data-products/insys_authorized_rx.csv",                     4_925_627_086),
    "insys_authorized_rx.csv.zip":                     ("data-products/insys_authorized_rx.csv.zip",                   726_615_967),
    "insys_full_dedup.zip":                            ("data-products/insys_full_dedup.zip",                         2_847_899_042),
    "mallinckrodt_full_dedup.zip":                     ("data-products/mallinckrodt_full_dedup.zip",                65_677_698_529),
    "mckinsey_full_dedup.zip":                         ("data-products/mckinsey_full_dedup.zip",                      4_289_111_988),
    "mnk_customer_orders.csv":                         ("data-products/mnk_customer_orders.csv",                        40_150_478),
    "mnk_customer_orders.csv.zip":                     ("data-products/mnk_customer_orders.csv.zip",                    3_748_041),
    "mnk_prescriber_records.zip":                      ("data-products/mnk_prescriber_records.zip",                   315_828_602),
    "oida-image-collection-metadata-version-1.csv.gz": ("data-products/oida-image-collection-metadata-version-1.csv.gz", 1_785_651),
    "pennsaid_bydates.csv":                            ("data-products/pennsaid_bydates.csv",                         1_936_985_191),
    "prescribers.csv":                                 ("data-products/prescribers.csv",                                30_878_462),
    "sumavel_bydates.csv":                             ("data-products/sumavel_bydates.csv",                            86_697_876),
    "xartemis_bydates.csv":                            ("data-products/xartemis_bydates.csv",                          168_545_925),
}


def human_size(n: int) -> str:
    size = float(n)          # the running value stops being an int on the first divide
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def download(name: str, out_dir: str = ".") -> None:
    if name not in DATASETS:
        raise ValueError(f"Unknown dataset '{name}'. Run --list to see available files.")
    key, size = DATASETS[name]
    url = f"{BUCKET}/{key}"
    dest = os.path.join(out_dir, name)
    os.makedirs(out_dir, exist_ok=True)

    print(f"Downloading {name} ({human_size(size)})...")

    def progress(count, block, total):
        pct = min(count * block / total * 100, 100)
        mb_done = count * block / 1e6
        mb_total = total / 1e6
        print(f"  {pct:5.1f}%  {mb_done:.0f} / {mb_total:.0f} MB", end="\r", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=progress)
    print(f"\n  Saved to {dest}")


def list_datasets() -> None:
    print(f"{'Name':<50} {'Size':>10}")
    print("-" * 62)
    for name, (_, size) in sorted(DATASETS.items()):
        print(f"{name:<50} {human_size(size):>10}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download OIDA datasets")
    parser.add_argument("files", nargs="*", help="Dataset filename(s) to download")
    parser.add_argument("--list", action="store_true", help="List available datasets")
    parser.add_argument("--out", default=".", help="Output directory (default: current dir)")
    args = parser.parse_args()

    if args.list or not args.files:
        list_datasets()
    else:
        for name in args.files:
            download(name, args.out)
