RELATIVITY IMPORT INSTRUCTIONS — small-real (REAL OIDA DATA)
=============================================================

Every value in this package is real. Metadata comes straight from the public
OIDA index (UCSF Opioid Industry Documents Archive, Insys Litigation
Documents collection). Natives are the archive's real produced PDFs, extracted
text is the archive's real OCR output, and MD5 hashes are the archive's own
published hashes (verified at build time). There are no review fields
(Responsiveness, Privilege, Issue Tags, TAR) because a produced archive has
no review decisions — see scripts/export_insys_documents.py for the same
principle applied to the full export.

This package contains:
  natives/          — 60 real produced PDFs
  text/             — real OCR extracted text, one .txt per document
  load-file.dat     — Concordance load file (UTF-8 with BOM, CRLF)

STEP 1 — Copy the package to a path Relativity can access
  Example: \\fileserver\LoadFiles\oida-small-real\

STEP 2 — Import
  Workspace -> Import/Export -> Import -> Document Load File
  Select load-file.dat with:
    File encoding:    UTF-8
    Column separator: þ (ASCII 254)
    Quote character:  ÿ (ASCII 255)
    Newline:          ® (ASCII 174)

STEP 3 — Field mapping (all real, sourced from the OIDA index)
    Control Number         -> Control Number (OIDA document id)
    Bates Begin            -> Bates Beg (e.g. INSYS-MDL-010938771)
    Custodian              -> Custodian
    File Name / File Type  -> matching fixed-length text fields
    Email From/To/CC/Subject, Date Sent/Received -> email metadata fields
    Primary Date           -> Sort Date (yyyy-mm-dd)
    Page Count, File Size, MD5 Hash, Redacted -> matching fields
    Source URL             -> link back to the document on industrydocuments.ucsf.edu
    NativeFilePath         -> Native File Path (relative, e.g. natives\ffym0280.pdf)
    ExtractedTextFilePath  -> Extracted Text (enable "cell contains file path")

STEP 4 — Base path
  When prompted for the repository/base path for natives and extracted text,
  point it at the folder containing this README.

NOTES
  - Some fields are legitimately blank (the archive itself has no value);
    nothing has been filled in synthetically.
  - Redactions in the PDFs/OCR ([||REDACTED-NAME||]) are the archive's own.
  - Rebuild or resize with:
      .venv/bin/python scripts/build_real_load_package.py --count N
