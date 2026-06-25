#!/usr/bin/env python3
"""
export_insys_documents.py

Export the FULL, REAL Insys document set from the public OIDA index parquet
(UCSF Opioid Industry Documents Archive) for ECI — every document, every real
Relativity *processing* field that exists in the archive. No cap, no sampling,
no synthetic values.

Mapping follows Relativity's processing-field schema
(help.relativity.com → Mapping processing fields). Each emitted column comes
from a real OIDA source; fields with no archive source (review/analytics:
Responsiveness, Privilege, Issue Tags, Batches, TAR/AL) are deliberately omitted
— a raw produced archive has no review decisions.

Extracted Text is NOT baked in (avg OCR ~70 KB × ~1.63M docs ≈ ~112 GB). Instead
each row carries a deterministic `OCR Text URL` so the real text can be fetched
on demand. Language is a processing field derived from that OCR text — see
scripts/derive_language_sample.py for the (bounded) language-ID pass.

Output (default /tmp/oioda-large/):
  documents.csv.gz   — all Insys docs, real processing metadata
  custodians.json    — every real collected custodian + real doc count

Run:  python3 scripts/export_insys_documents.py [--out DIR]
Requires the duckdb CLI (httpfs autoloads; the parquet is public).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BUCKET = "https://opioid-industry-documents-archive-dataset-bucket.s3.amazonaws.com"
PARQUET = f"{BUCKET}/metadata/oida-index.parquet"
COLLECTION = "Insys Litigation Documents"

MACROS = f"""
SET lambda_syntax='ENABLE_SINGLE_ARROW';
INSTALL httpfs; LOAD httpfs; SET enable_progress_bar=false;
-- Map OIDA originalformat -> Relativity-style File Type label.
CREATE OR REPLACE MACRO ftcat(f) AS CASE upper(coalesce(f,''))
  WHEN 'MSG' THEN 'Email - MSG' WHEN 'EML' THEN 'Email - EML' WHEN 'PST' THEN 'Email Container - PST'
  WHEN 'PDF' THEN 'PDF' WHEN 'XLSX' THEN 'Spreadsheet - XLSX' WHEN 'XLS' THEN 'Spreadsheet - XLS'
  WHEN 'XLSM' THEN 'Spreadsheet - XLSX' WHEN 'DOCX' THEN 'Word - DOCX' WHEN 'DOC' THEN 'Word - DOC'
  WHEN 'PPTX' THEN 'Presentation - PPTX' WHEN 'PPT' THEN 'Presentation - PPT'
  WHEN 'JPG' THEN 'Image - JPEG' WHEN 'JPEG' THEN 'Image - JPEG' WHEN 'PNG' THEN 'Image - PNG'
  WHEN 'TIF' THEN 'Image - TIFF' WHEN 'TIFF' THEN 'Image - TIFF' WHEN '' THEN '' ELSE upper(f) END;
CREATE OR REPLACE MACRO pdate(a,b) AS coalesce(try_strptime(a,'%Y %B %d'), try_strptime(b,'%Y %B %d'));
-- Deterministic OCR text URL from the document id: id=thkd0262 -> .../t/h/k/d/thkd0262/thkd0262.ocr
CREATE OR REPLACE MACRO ocr_url(id) AS
  CASE WHEN length(id) >= 4 THEN
    '{BUCKET}/' || substr(id,1,1)||'/'||substr(id,2,1)||'/'||substr(id,3,1)||'/'||substr(id,4,1)||'/'||id||'/'||id||'.ocr'
  ELSE '' END;
"""


def run_duckdb(sql: str, json_out: bool = False) -> str:
    args = ["duckdb"] + (["-json"] if json_out else []) + ["-c", sql]
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(f"duckdb failed ({proc.returncode})")
    return proc.stdout


def s(v: str) -> str:
    return "'" + v.replace("'", "''") + "'"


def export_documents(out_csv: Path) -> None:
    sql = MACROS + f"""
    COPY (
      SELECT
        id                                                 AS "Control Number",
        bn                                                 AS "Bates Begin",
        bnalias                                            AS "Bates Alias",
        array_to_string(custodian, '; ')                   AS "Custodian",
        filename                                           AS "File Name",
        upper(regexp_extract(coalesce(filename,''), '\\.([A-Za-z0-9]+)$', 1)) AS "File Extension",
        ftcat(originalformat)                              AS "File Type",
        originalformat                                     AS "Original Format",
        array_to_string(dt, '; ')                          AS "Doc Type",
        try_cast(artifact[1].size AS BIGINT)               AS "File Size",
        artifact[1].md5                                    AS "MD5 Hash",
        artifact[1].mediatype                              AS "Media Type",
        array_to_string(filepath, '; ')                    AS "Original File Path",
        array_to_string(au, '; ')                          AS "Email From",
        array_to_string(rc, '; ')                          AS "Email To",
        array_to_string(cc, '; ')                          AS "Email CC",
        ti                                                 AS "Email Subject",
        datesent                                           AS "Date Sent",
        datereceived                                       AS "Date Received",
        coalesce(strftime(pdate(datesent, datereceived), '%Y-%m-%d'), '') AS "Primary Date",
        conversation                                       AS "Conversation",
        array_to_string(men, '; ')                         AS "Mentioned",
        try_cast(pg AS BIGINT)                             AS "Page Count",
        coalesce(redact,'')                                AS "Redacted",
        ocr_url(id)                                        AS "OCR Text URL",
        ''                                                 AS "Language"
      FROM read_parquet({s(PARQUET)})
      WHERE collection = {s(COLLECTION)}
    ) TO {s(str(out_csv))} (FORMAT CSV, HEADER, QUOTE '"', FORCE_QUOTE *, COMPRESSION GZIP);
    """
    run_duckdb(sql)


def export_custodians(out_json: Path) -> list[dict]:
    """Every real collected custodian (distinct `custodian` value) + real doc count."""
    sql = MACROS + f"""
    SELECT x AS name, count(*) AS actual_doc_count
    FROM read_parquet({s(PARQUET)}) t, UNNEST(t.custodian) u(x)
    WHERE t.collection = {s(COLLECTION)} AND x IS NOT NULL AND len(trim(x)) > 0
    GROUP BY x ORDER BY actual_doc_count DESC;
    """
    rows = json.loads(run_duckdb(sql, json_out=True))
    custs = [{"id": f"C{i + 1:04d}", "name": r["name"],
              "actual_doc_count": int(r["actual_doc_count"])} for i, r in enumerate(rows)]
    out_json.write_text(json.dumps(custs, indent=2))
    return custs


def summarize(out_csv: Path) -> None:
    sql = f"""
    INSTALL httpfs; LOAD httpfs;
    SELECT count(*) AS docs,
           count(*) FILTER (WHERE "Email From" <> '') AS with_sender,
           count(DISTINCT "Custodian") AS distinct_custodian_strings,
           min("Primary Date") AS first_date, max("Primary Date") AS last_date
    FROM read_csv_auto({s(str(out_csv))});
    """
    print(run_duckdb(sql))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/oioda-large", type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"1/3  Exporting ALL Insys docs (real processing metadata) -> {args.out/'documents.csv.gz'} ...")
    export_documents(args.out / "documents.csv.gz")
    print("2/3  Writing custodians.json (every real custodian) ...")
    custs = export_custodians(args.out / "custodians.json")
    print(f"       {len(custs)} distinct real custodians")
    print("3/3  Summary:")
    summarize(args.out / "documents.csv.gz")
    print("Done. Extracted Text is fetched on demand via the OCR Text URL column.")


if __name__ == "__main__":
    main()
