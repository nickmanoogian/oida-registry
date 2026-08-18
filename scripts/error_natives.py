#!/usr/bin/env python3
"""
error_natives.py — Fabricate native files that genuinely fail Relativity processing

mock-data/RULES.md Rule 6 specifies a processing error distribution, and
generate_mock_metadata.py honours it: 118 of the 1,439 small-tier documents carry
Processing Status = Error. Until this module existed, the natives behind those rows
were perfectly healthy files, so importing the package and running Processing
produced zero errors. Rule 12 closes that gap: a document flagged as an error must
have a file that actually errors.

Each scenario returns (bytes_or_path_written, note). Scenarios are keyed by the
Processing Error Type in documents.csv, so the metadata drives the fabrication.

Nothing here fabricates malware, EICAR strings, or zip bombs. Container scenarios
use shallow nesting with tiny payloads.
"""

import io
import json
import os
import subprocess
import zipfile

# Password applied to every encrypted artefact in a package. Documented in
# IMPORT_README.txt so testers can add it to the Relativity password bank.
PACKAGE_PASSWORD = "oioda"

TRUNCATE_FRACTION = 0.4   # keep this much of a valid file for "Corrupt File"
NEST_DEPTH        = 8     # container nesting for extraction timeout

# Minimal real format signatures for unsupported-type stubs.
UNSUPPORTED_STUBS = {
    "mdb":     b"\x00\x01\x00\x00Standard Jet DB\x00",
    "accdb":   b"\x00\x01\x00\x00Standard ACE DB\x00",
    "dwg":     b"AC1027\x00\x00\x00\x00\x00\x00",
}
IWORK_EXTS = {"numbers", "key", "pages"}


# ── individual scenarios ──────────────────────────────────────────────────

def zero_byte(path, **_):
    open(path, "wb").close()
    return "empty file, 0 bytes"


def truncated(path, healthy_bytes, **_):
    keep = max(16, int(len(healthy_bytes) * TRUNCATE_FRACTION))
    with open(path, "wb") as f:
        f.write(healthy_bytes[:keep])
    return f"valid file truncated to {keep} of {len(healthy_bytes)} bytes"


def header_corrupt(path, healthy_bytes, **_):
    data = bytearray(healthy_bytes)
    data[:8] = b"\x00" * min(8, len(data))
    with open(path, "wb") as f:
        f.write(bytes(data))
    return "magic bytes overwritten with nulls"


def extension_mismatch(path, **_):
    """PDF content living under whatever extension the metadata claims."""
    pdf = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
           b"2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n")
    with open(path, "wb") as f:
        f.write(pdf)
    return f"PDF content under a {os.path.splitext(path)[1] or 'missing'} extension"


def broken_ooxml(path, healthy_bytes, **_):
    """A structurally valid OOXML zip with its main part removed."""
    dropped = None
    try:
        src = zipfile.ZipFile(io.BytesIO(healthy_bytes))
    except zipfile.BadZipFile:
        return truncated(path, healthy_bytes)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as out:
        for item in src.infolist():
            if item.filename in ("word/document.xml", "xl/workbook.xml", "ppt/presentation.xml"):
                dropped = item.filename
                continue
            out.writestr(item, src.read(item.filename))
    return f"OOXML package with {dropped or 'its main part'} removed"


def malformed_json(path, healthy_bytes, **_):
    """Truncated mid-object: valid enough to identify, invalid to parse."""
    text = healthy_bytes.decode("utf-8", "replace")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text[: max(20, len(text) // 3)])
    return "RSMF JSON truncated mid-object, will not parse"


def password_pdf(path, doc, **_):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_encryption(owner_password=PACKAGE_PASSWORD, user_password=PACKAGE_PASSWORD)
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    pdf.multi_cell(0, 6, f"Control Number: {doc.get('Control Number','')}\n"
                         "This document is password protected.")
    pdf.output(path)
    return f"encrypted PDF, user password '{PACKAGE_PASSWORD}'"


def password_zip(path, doc, healthy_bytes, **_):
    """Password protected container, built with Info-ZIP so the encryption is real."""
    work    = path + ".payload"
    inner   = f"{doc.get('Control Number','DOC')}.txt"
    payload = os.path.join(os.path.dirname(path), inner)
    with open(payload, "wb") as f:
        f.write(healthy_bytes[:4000] or b"payload")
    if os.path.exists(path):
        os.remove(path)
    try:
        subprocess.run(["zip", "-q", "-j", "-P", PACKAGE_PASSWORD, path, payload],
                       check=True, capture_output=True)
    finally:
        os.path.exists(payload) and os.remove(payload)
        os.path.exists(work) and os.remove(work)
    return f"password protected container, password '{PACKAGE_PASSWORD}', 1 child"


def nested_container(path, **_):
    """NEST_DEPTH single-entry zips, innermost payload a few bytes."""
    blob = b"innermost payload\n"
    name = "payload.txt"
    for level in range(NEST_DEPTH):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(name, blob)
        blob = buf.getvalue()
        name = f"level{NEST_DEPTH - level}.zip"
    with open(path, "wb") as f:
        f.write(blob)
    return f"{NEST_DEPTH} levels of nested containers"


def unsupported_stub(path, **_):
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    if ext in UNSUPPORTED_STUBS:
        with open(path, "wb") as f:
            f.write(UNSUPPORTED_STUBS[ext] + b"\x00" * 64)
        return f"real .{ext} signature, no extractable content"
    if ext in IWORK_EXTS:
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("Index/Document.iwa", b"\x00\x01\x02\x03")
            z.writestr("Metadata/Properties.plist", b"<plist/>")
        return f"iWork .{ext} package, no extractable content"
    with open(path, "wb") as f:
        f.write(b"\x00\x01\x02\x03" * 32)
    return f"unrecognised binary under .{ext}"


def text_free_pdf(path, doc, **_):
    """A PDF whose page carries only vector marks. Nothing to extract, OCR must run."""
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(40, 40, 40)
    for i in range(28):                      # noisy bars, no text objects at all
        pdf.rect(12 + (i % 7) * 26, 20 + (i // 7) * 58, 20 + (i % 5) * 3, 40, style="F")
    pdf.output(path)
    return "PDF with no text layer, extraction yields nothing"


# ── dispatch ──────────────────────────────────────────────────────────────

# Processing Error Type -> (scenario, expected Relativity outcome)
SCENARIOS = {
    "Password Protected":                 (password_pdf,      "Password protected / encrypted"),
    "Corrupt File":                       (truncated,         "Corrupt or unreadable file"),
    "Unsupported File Type":              (unsupported_stub,  "File type not supported for extraction"),
    "Extraction Failure":                 (broken_ooxml,      "Text extraction failure"),
    "Container Extraction Timeout":       (nested_container,  "Container extraction failure or timeout"),
    "Teams Conversion Error":             (malformed_json,    "Conversion failure"),
    "OCR Failure - Poor Scan Quality":    (text_free_pdf,     "No extractable text, OCR required"),
    "Empty File":                         (zero_byte,         "Empty file"),
    "Extension Mismatch":                 (extension_mismatch,"File type differs from extension"),
}

# Errors we deliberately do not fabricate. The native stays healthy and
# EXPECTED_ERRORS.csv records why, rather than pretending coverage exists.
NOT_FABRICABLE = {
    "MIP Protected - Limited Extraction":
        "needs a real Microsoft 365 tenant to apply the sensitivity label",
}

# Outcomes that depend on the environment rather than the file.
NOT_DETERMINISTIC = {
    "OCR Failure - Poor Scan Quality":
        "a capable OCR engine may still extract something",
    "Container Extraction Timeout":
        "depends on worker configuration; may complete instead of timing out",
    "Teams Conversion Error":
        "Relativity chooses the error label; may report as an extraction failure",
}


def scenario_for(doc):
    """Return (fn, expected_error, note) for a document, or None to leave it healthy."""
    err = (doc.get("Processing Error Type") or "").strip()
    if not err or err in NOT_FABRICABLE:
        return None
    entry = SCENARIOS.get(err)
    if entry is None:
        return None
    fn, expected = entry
    # Password Protected on a non-PDF is stood in for by an encrypted container:
    # a genuinely encrypted OOXML file cannot be written without a heavy dependency.
    if err == "Password Protected" and not (doc.get("File Extension","").lower() == "pdf"):
        fn = password_zip
    return fn, expected, NOT_DETERMINISTIC.get(err, "")


# What each scenario actually writes, so a mismatch with the claimed extension can
# be reported honestly rather than glossed over. Rule 6 assigns error types without
# regard to file type, so an .eml row can be flagged "Unsupported File Type".
PRODUCES = {
    nested_container:  "zip",
    password_zip:      "zip",
    password_pdf:      "pdf",
    text_free_pdf:     "pdf",
    extension_mismatch:"pdf",
    unsupported_stub:  "stub",
}


def _extension_caveat(fn, doc):
    produced = PRODUCES.get(fn)
    if produced in (None, "stub"):
        return ""
    ext = (doc.get("File Extension") or "").lower()
    if ext == produced:
        return ""
    return (f"content is a {produced}, the row claims .{ext}; Relativity may report a "
            f"file identification mismatch instead of the expected error")


def fabricate(doc, path, healthy_bytes):
    """Overwrite `path` with a file that fails the way the metadata claims.

    Returns a dict for EXPECTED_ERRORS.csv, or None if nothing was fabricated.
    """
    chosen = scenario_for(doc)
    if chosen is None:
        return None
    fn, expected, caveat = chosen
    note = fn(path=path, doc=doc, healthy_bytes=healthy_bytes or b"")
    ext_caveat = _extension_caveat(fn, doc)
    if ext_caveat:
        caveat = f"{caveat}; {ext_caveat}" if caveat else ext_caveat
    return {
        "Control Number":  doc.get("Control Number",""),
        "Custodian":       doc.get("Custodian",""),
        "Scenario":        (doc.get("Processing Error Type") or "").strip(),
        "How It Was Built": note,
        "Expected Relativity Error": expected,
        "Guaranteed": "no" if caveat else "yes",
        "Caveat": caveat,
    }


EXPECTED_ERROR_COLUMNS = [
    "Control Number","Custodian","Native File","Scenario","How It Was Built",
    "Expected Relativity Error","Guaranteed","Caveat",
]
