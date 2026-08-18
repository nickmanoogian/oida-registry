#!/usr/bin/env python3
"""
build_real_load_package.py — Build a small, fully REAL Relativity load package
from the public OIDA index (UCSF Opioid Industry Documents Archive).

Unlike build_load_package.py (mock MDL 2804 narrative data), every value here
is real: metadata comes straight from the public OIDA index parquet, natives
are the archive's real produced PDFs, extracted text is the archive's real OCR
output, and MD5 hashes are the archive's own. No synthetic fields, no review
decisions (a produced archive has none).

Output (default load-packages/small-real/):
  natives/{id}.pdf        — real produced PDF for each document
  text/{id}.txt           — real OCR extracted text
  load-file.dat           — Concordance load file (UTF-8 with BOM)
  IMPORT_README.txt       — Relativity import instructions

Usage:
  .venv/bin/python scripts/build_real_load_package.py [--count 60] [--out DIR]
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

try:
    import duckdb
except ModuleNotFoundError:
    raise SystemExit("Missing 'duckdb'. Run: pip install -r requirements.txt")

BUCKET = "https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com"
PARQUET = f"{BUCKET}/metadata/oida-index.parquet"
COLLECTION = "Insys Litigation Documents"
MAX_PDF_BYTES = 400_000  # keep the package small

DAT_SEP = chr(254)   # þ
DAT_QUOTE = chr(255) # ÿ
DAT_NL = chr(174)    # ® — replaces newlines inside a field value

COLUMNS = [
    "Control Number", "Bates Begin", "Bates Alias", "Custodian",
    "File Name", "File Type", "Original Format", "Doc Type",
    "File Size", "MD5 Hash", "Email From", "Email To", "Email CC",
    "Email Subject", "Date Sent", "Date Received", "Primary Date",
    "Page Count", "Redacted", "Collection", "Source URL",
    "NativeFilePath", "ExtractedTextFilePath",
]

QUERY = f"""
WITH docs AS (
  SELECT
    id,
    coalesce(bn, '')                                        AS bates_begin,
    coalesce(bnalias, '')                                   AS bates_alias,
    array_to_string(custodian, '; ')                        AS custodian,
    coalesce(filename, id || '.pdf')                        AS file_name,
    CASE upper(coalesce(originalformat,''))
      WHEN 'MSG' THEN 'Email - MSG' WHEN 'EML' THEN 'Email - EML'
      WHEN 'PDF' THEN 'PDF' WHEN 'XLSX' THEN 'Spreadsheet - XLSX'
      WHEN 'XLS' THEN 'Spreadsheet - XLS' WHEN 'DOCX' THEN 'Word - DOCX'
      WHEN 'DOC' THEN 'Word - DOC' WHEN 'PPTX' THEN 'Presentation - PPTX'
      WHEN 'PPT' THEN 'Presentation - PPT'
      ELSE upper(coalesce(originalformat,'')) END           AS file_type,
    coalesce(originalformat, '')                            AS original_format,
    array_to_string(dt, '; ')                               AS doc_type,
    list_filter(artifact, a -> a.name = id || '.pdf')[1]    AS pdf,
    list_filter(artifact, a -> a.name = id || '.ocr')[1]    AS ocr,
    array_to_string(au, '; ')                               AS email_from,
    array_to_string(rc, '; ')                               AS email_to,
    array_to_string(cc, '; ')                               AS email_cc,
    coalesce(ti, '')                                        AS subject,
    coalesce(datesent, '')                                  AS date_sent,
    coalesce(datereceived, '')                              AS date_received,
    coalesce(strftime(coalesce(
      try_strptime(datesent, '%Y %B %d'),
      try_strptime(datereceived, '%Y %B %d')), '%Y-%m-%d'), '') AS primary_date,
    coalesce(try_cast(pg AS BIGINT), 0)                     AS page_count,
    coalesce(redact, '')                                    AS redacted,
    collection
  FROM read_parquet('{PARQUET}')
  WHERE collection = '{COLLECTION}'
    AND list_contains(availability, 'public')
    AND len(custodian) > 0
)
SELECT * FROM (
  SELECT *, row_number() OVER (PARTITION BY original_format ORDER BY id) AS rn
  FROM docs
  WHERE pdf IS NOT NULL AND ocr IS NOT NULL
    AND pdf.size BETWEEN 10000 AND {MAX_PDF_BYTES}
)
WHERE rn <= {{per_format}}
ORDER BY original_format, id
LIMIT {{count}}
"""


def doc_url(doc_id: str, ext: str) -> str:
    p = "/".join(doc_id[:4])
    return f"{BUCKET}/{p}/{doc_id}/{doc_id}.{ext}"


def dat_field(value) -> str:
    text = str(value if value is not None else "")
    text = text.replace(DAT_QUOTE, "").replace(DAT_SEP, "")
    text = text.replace("\r\n", DAT_NL).replace("\n", DAT_NL).replace("\r", DAT_NL)
    return f"{DAT_QUOTE}{text}{DAT_QUOTE}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--count", type=int, default=60)
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parent.parent / "load-packages" / "small-real")
    args = ap.parse_args()

    natives = args.out / "natives"
    textdir = args.out / "text"
    natives.mkdir(parents=True, exist_ok=True)
    textdir.mkdir(parents=True, exist_ok=True)

    per_format = max(6, args.count // 5)
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    print(f"1/3  Querying real {COLLECTION} docs from the public OIDA index ...")
    cur = con.execute(QUERY.format(per_format=per_format, count=args.count))
    names = [d[0] for d in cur.description]
    rows = [dict(zip(names, rec)) for rec in cur.fetchall()]
    print(f"     selected {len(rows)} docs "
          f"({len({r['original_format'] for r in rows})} formats, "
          f"{len({r['custodian'] for r in rows})} distinct custodian strings)")

    print("2/3  Downloading real natives (.pdf) and OCR text (.ocr) from public S3 ...")
    dat_rows = []
    for i, r in enumerate(rows):
        doc_id = r["id"]
        pdf_path = natives / f"{doc_id}.pdf"
        txt_path = textdir / f"{doc_id}.txt"
        if not pdf_path.exists():
            urllib.request.urlretrieve(doc_url(doc_id, "pdf"), pdf_path)
        if not txt_path.exists():
            urllib.request.urlretrieve(doc_url(doc_id, "ocr"), txt_path)
        expected = int(r["pdf"]["size"])
        actual = pdf_path.stat().st_size
        if actual != expected:
            sys.exit(f"Size mismatch for {doc_id}.pdf: index says {expected}, got {actual}")
        dat_rows.append([
            doc_id, r["bates_begin"], r["bates_alias"], r["custodian"],
            r["file_name"], r["file_type"], r["original_format"], r["doc_type"],
            expected, r["pdf"]["md5"], r["email_from"], r["email_to"], r["email_cc"],
            r["subject"], r["date_sent"], r["date_received"], r["primary_date"],
            int(r["page_count"]), r["redacted"], r["collection"],
            f"https://www.industrydocuments.ucsf.edu/opioids/docs/#id={doc_id}",
            f"natives\\{doc_id}.pdf", f"text\\{doc_id}.txt",
        ])
        if (i + 1) % 10 == 0:
            print(f"     {i + 1}/{len(rows)} downloaded")

    print("3/3  Writing load-file.dat ...")
    lines = [DAT_SEP.join(dat_field(v) for v in row)
             for row in [COLUMNS, *dat_rows]]
    (args.out / "load-file.dat").write_text("﻿" + "\r\n".join(lines) + "\r\n",
                                            encoding="utf-8", newline="")

    total_mb = sum(f.stat().st_size for f in args.out.rglob("*") if f.is_file()) / 1e6
    print(f"Done. {len(dat_rows)} real documents, {total_mb:.1f} MB -> {args.out}")


if __name__ == "__main__":
    main()
