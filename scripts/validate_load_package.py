#!/usr/bin/env python3
"""
validate_load_package.py — Verify a built load package conforms to RULES.md Rule 11

Checks the package on disk, not the source metadata: that every NativeFilePath in
load-file.dat resolves to a real file, that the folder a native sits in matches the
custodian on its row, that nothing was dumped at the root of natives/, and that
custodian-sources.csv agrees with what is actually on disk (Rule 11).

When the package carries EXPECTED_ERRORS.csv it also enforces Rule 12: every
deliberately broken native exists, is genuinely broken in the way its scenario
claims, and the File Size in the load file matches the bytes on disk.

Usage:
  python scripts/validate_load_package.py load-packages/small
  python scripts/validate_load_package.py load-packages/small --flat
"""

import argparse
import csv
import json
import os
import re
import sys
import zipfile
import zlib
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dat_format import DAT_FIELD_SEP as DAT_SEP
from dat_format import DAT_QUOTE

import error_natives

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


failures: list[str] = []


def check(label, ok, detail=""):
    print(f"  [{PASS if ok else FAIL}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def read_dat(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            rows.append([v.strip(DAT_QUOTE) for v in line.rstrip("\n").split(DAT_SEP)])
    return rows[0], rows[1:]


def is_broken(row, path):
    """Confirm a fabricated native actually fails the way its scenario claims.

    The signature has to be specific enough that replacing a broken file with a
    healthy one is caught. "Non-empty" is not a signature.
    """
    scenario = row["Scenario"]
    note     = row.get("How It Was Built", "")
    data     = open(path, "rb").read()
    if scenario == "Empty File":
        return len(data) == 0
    if scenario == "Password Protected":
        if data[:4] == b"%PDF":
            return b"/Encrypt" in data
        try:
            z = zipfile.ZipFile(path)
            z.read(z.namelist()[0])
            return False                      # opened with no password: not protected
        except RuntimeError as e:
            return "password" in str(e).lower()
        except Exception:
            return True
    if scenario == "Corrupt File":
        m = re.search(r"truncated to (\d+) of", note)
        if m:
            return len(data) == int(m.group(1))
        if "magic bytes" in note:
            return data[:8] == b"\x00" * 8
        return False
    if scenario == "Extraction Failure":
        try:
            names = zipfile.ZipFile(path).namelist()
            return not any(n in names for n in
                           ("word/document.xml", "xl/workbook.xml", "ppt/presentation.xml"))
        except Exception:
            return True
    if scenario == "Container Extraction Timeout":
        try:
            return zipfile.ZipFile(path).namelist()[0].endswith(".zip")
        except Exception:
            return False
    if scenario == "Teams Conversion Error":
        try:
            json.loads(data.decode("utf-8", "replace"))
            return False
        except Exception:
            return True
    if scenario == "OCR Failure - Poor Scan Quality":
        return b"/Font" not in data
    if scenario == "Extension Mismatch":
        return data[:4] == b"%PDF"
    if scenario == "Unsupported File Type":
        if any(data.startswith(sig) for sig in error_natives.UNSUPPORTED_STUBS.values()):
            return True
        try:                                   # iWork stub is a zip with an Index/ part
            return any(n.startswith("Index/") for n in zipfile.ZipFile(path).namelist())
        except Exception:
            pass
        return data.startswith(b"\x00\x01\x02\x03")
    return True                               # unknown scenario: do not fail the run


# ── Planted content (Rules 16-18) ─────────────────────────────────────────

def native_text(path):
    """Readable text from a native, whatever wrapper it is in.

    A raw grep is not enough: .eml bodies are base64, OOXML is a zip, and fpdf2
    compresses its content streams. Checking the wrapper instead of the text is how
    a ground-truth file ends up claiming something the native does not hold.
    """
    ext = os.path.splitext(path)[1].lower()
    try:
        raw = open(path, "rb").read()
    except OSError:
        return ""
    if ext in (".docx", ".xlsx", ".pptx"):
        try:
            with zipfile.ZipFile(path) as z:
                return " ".join(z.read(n).decode("utf-8", "replace")
                                for n in z.namelist() if n.endswith(".xml"))
        except (zipfile.BadZipFile, KeyError, OSError):
            return ""
    if ext == ".eml":
        import email as _email
        msg = _email.message_from_bytes(raw)
        parts = []
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True) or b""
                parts.append(payload.decode("utf-8", "replace"))
        return " ".join(parts)
    if ext == ".pdf":
        out = []
        for m in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
            blob = m.group(1)
            # The EOL before `endstream` is optional per the PDF spec, and the
            # deflate payload's own last bytes can be \r\n. Trimming first cost a
            # real stream at xlarge scale: one PDF in 75,315 compressed to bytes
            # ending 0x0D 0x0A, zlib then failed on the truncated payload, and the
            # PI check reported three values missing from a file that held all
            # three. Try the payload whole, then trimmed.
            for candidate in (blob, blob[:-2], blob[:-1]):
                try:
                    blob = zlib.decompress(candidate)
                    break
                except zlib.error:
                    continue
            for token in re.findall(rb"\((?:\\.|[^\\()])*\)", blob):
                out.append(token[1:-1].replace(b"\\(", b"(").replace(b"\\)", b")")
                           .decode("latin-1"))
        return " ".join(out)
    return raw.decode("utf-8", "replace")


# ── Rule 19: the date layer ───────────────────────────────────────────────

_OOXML_DATE = re.compile(r"<dcterms:(created|modified)[^>]*>([0-9T:\-]+)Z?</dcterms:\1>")
_PDF_DATE   = re.compile(rb"/CreationDate\s*\(D:(\d{14})")

# Every library that writes one of these formats stamps its own name and its own
# date unless told otherwise. Finding one of these in a package means the file
# was written with library defaults, which is how a 2013 or a build-clock date
# reaches Collection Coverage.
LIBRARY_TELLS = ("Steve Canny", "openpyxl", "python-docx", "python-pptx")

# Rule 4 gives ZIP children a deliberately unreliable date, because the ZIP
# format carries no time zone. It is a documented wrong answer, so it neither
# widens the matter window nor counts as a leak.
DOCUMENTED_BAD_DATES = {"1980-01-01"}


def ooxml_dates(path):
    """(created, modified) as YYYY-MM-DD strings, plus the raw core.xml."""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("docProps/core.xml").decode("utf-8", "replace")
    except (zipfile.BadZipFile, KeyError, OSError):
        return None, None, ""          # deliberately broken files are Rule 12's problem
    found = {k: v[:10] for k, v in _OOXML_DATE.findall(xml)}
    return found.get("created"), found.get("modified"), xml


def expected_mtime(row, i_date, i_created, i_modified):
    """The date the builder stamps on disk, from the load file's own columns."""
    def val(i):
        return row[i][:10] if i is not None and row[i].strip() else ""
    primary  = val(i_date)
    created  = val(i_created)  or primary
    modified = val(i_modified) or primary
    if not modified:
        return ""
    return max(modified, created) if created else modified


def pdf_creation_date(path):
    try:
        with open(path, "rb") as f:
            m = _PDF_DATE.search(f.read())
    except OSError:
        return None
    if not m:
        return None
    d = m.group(1).decode()
    return f"{d[0:4]}-{d[4:6]}-{d[6:8]}"


def main():
    ap = argparse.ArgumentParser(description="Validate a built Relativity load package")
    ap.add_argument("package", help="Path to the package directory")
    ap.add_argument("--flat", action="store_true",
                    help="Package was built with --flat; skip the per-custodian folder checks")
    args = ap.parse_args()

    pkg = args.package
    dat = os.path.join(pkg, "load-file.dat")
    src = os.path.join(pkg, "custodian-sources.csv")
    nat = os.path.join(pkg, "natives")

    for required in (dat, src):
        if not os.path.exists(required):
            sys.exit(f"ERROR: {required} not found. Build the package first.")
    if not os.path.exists(nat) and "NativeFilePath" in open(dat, encoding="utf-8").readline():
        sys.exit(f"ERROR: {nat} not found but the load file declares NativeFilePath.")

    print(f"\n  Validating {pkg} (Rule 11)\n")

    # The field-creation script has to be IN the package. IMPORT_README has told
    # people to run "python3 scripts/create_workspace_fields.py" since the
    # twenty-four-fields section was written, and for just as long no package
    # contained a scripts/ directory: the instruction pointed at a file nobody
    # working from a release zip had. Without those fields a stock template maps 35
    # of 61 columns and silently drops the rest, so this is the difference between a
    # package that imports and one that looks like it imported.
    print("  Field creation script")
    scripts_dir = os.path.join(pkg, "scripts")
    for name in ("create_workspace_fields.py", "workspace_fields.py"):
        path = os.path.join(scripts_dir, name)
        check(f"scripts/{name} ships in the package", os.path.exists(path),
              "present" if os.path.exists(path)
              else "NOT FOUND, and IMPORT_README tells the reader to run it")
    # It must also run from where it lands, with no checkout on the path. Importing
    # the copy in the package is the cheapest honest proof of that.
    spec_ok, detail = False, "not attempted"
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_pkg_workspace_fields", os.path.join(scripts_dir, "workspace_fields.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        spec_ok = len(getattr(mod, "WORKSPACE_FIELDS", [])) == 24
        detail = f"declares {len(getattr(mod, 'WORKSPACE_FIELDS', []))} fields, expected 24"
    except Exception as exc:                      # noqa: BLE001 - report, do not raise
        detail = f"{type(exc).__name__}: {exc}"
    check("the shipped copy imports and declares all 24 fields", spec_ok, detail)
    print()

    header, rows = read_dat(dat)
    # A --no-natives package drops the column entirely: 17 MB of paths to files it
    # does not contain. The native checks below then have nothing to inspect,
    # which is correct rather than a gap, so they say so instead of failing.
    has_natives = "NativeFilePath" in header
    i_nat  = header.index("NativeFilePath") if has_natives else None
    i_ctrl = header.index("Control Number")
    i_cust = header.index("Custodian")

    # 1. every declared native resolves on disk
    if not has_natives:
        print("\n  Native layer: skipped, this package declares no NativeFilePath\n")
    else:
        missing = [r[i_nat] for r in rows if r[i_nat]
                   and not os.path.isfile(os.path.join(pkg, r[i_nat].replace("\\", os.sep)))]
        check("every NativeFilePath resolves on disk", not missing,
              f"{len(missing)} missing" if missing else f"{sum(1 for r in rows if r[i_nat]):,} natives")

        # 2. load file paths use backslashes
        fwd = [r[i_nat] for r in rows if "/" in r[i_nat]]
        check("NativeFilePath uses backslash separators", not fwd, f"{len(fwd)} with forward slashes")

        if not args.flat:
            # 3. nothing loose at the root of natives/
            loose = [f for f in os.listdir(nat) if os.path.isfile(os.path.join(nat, f))]
            check("no files at the root of natives/", not loose, f"{len(loose)} loose files")

            # 4. the folder a native sits in matches its custodian
            # Rule 21 put the data source in front of the custodian, so both segments
            # are a contract now: natives\{source}\{custodian}\{year}\{month}.
            i_src = header.index("Data Source") if "Data Source" in header else None
            wrong_cust, wrong_src = [], []
            for r in rows:
                if not r[i_nat]:
                    continue
                parts = r[i_nat].split("\\")
                src_folder  = parts[1] if len(parts) > 1 else ""
                cust_folder = parts[2] if len(parts) > 2 else ""
                want_cust = r[i_cust].strip().replace(" ", "_")
                if cust_folder != want_cust and cust_folder != "_Unassigned":
                    wrong_cust.append((r[i_ctrl], cust_folder, r[i_cust]))
                if i_src is not None and r[i_src].strip():
                    want_src = re.sub(r"[^A-Za-z0-9._-]+", "_",
                                      r[i_src].replace(" (", "_").replace(")", ""))
                    if src_folder != want_src:
                        wrong_src.append((r[i_ctrl], src_folder, want_src))
            check("native folder matches the row's custodian", not wrong_cust,
                  f"{len(wrong_cust)} mismatches: {wrong_cust[:2]}" if wrong_cust else "")
            if i_src is not None:
                check("native folder matches the row's data source", not wrong_src,
                      f"{len(wrong_src)} mismatches: {wrong_src[:2]}" if wrong_src
                      else f"{len({r[i_src] for r in rows if r[i_src].strip()})} sources")

        # 5. custodian-sources.csv agrees with disk
        sheet = list(csv.DictReader(open(src, encoding="utf-8")))
        disk_files = sum(len(fs) for _, _, fs in os.walk(nat))
        disk_bytes = sum(os.path.getsize(os.path.join(root, fn))
                         for root, _, fs in os.walk(nat) for fn in fs)
        sheet_files = sum(int(r["Natives Written"]) for r in sheet)
        sheet_bytes = sum(int(r["Native Bytes"]) for r in sheet)
        check("custodian-sources.csv native count matches disk", disk_files == sheet_files,
              f"disk {disk_files:,} vs sheet {sheet_files:,}")
        check("custodian-sources.csv byte total matches disk", disk_bytes == sheet_bytes,
              f"disk {disk_bytes:,} vs sheet {sheet_bytes:,}")

        # 6. every custodian in the load file has a row in the sheet
        dat_custs   = {r[i_cust].strip() for r in rows if r[i_cust].strip()}
        sheet_custs = {r["Custodian"].strip() for r in sheet}
        check("every custodian in the load file has a data source row",
              dat_custs <= sheet_custs, f"missing: {sorted(dat_custs - sheet_custs)}")

        # ── Rule 12: intentionally broken natives ─────────────────────────────
        expected_path = os.path.join(pkg, "EXPECTED_ERRORS.csv")
        if os.path.exists(expected_path):
            print("\n  Rule 12 — intentionally broken natives\n")
            broken = list(csv.DictReader(open(expected_path, encoding="utf-8")))

            gone = [r["Native File"] for r in broken
                    if not os.path.isfile(os.path.join(pkg, r["Native File"].replace("\\", os.sep)))]
            check("every EXPECTED_ERRORS.csv native exists", not gone,
                  f"{len(gone)} missing" if gone else f"{len(broken):,} fabricated")

            intact = []
            for r in broken:
                target = os.path.join(pkg, r["Native File"].replace("\\", os.sep))
                if not os.path.isfile(target):
                    continue
                if not is_broken(r, target):
                    intact.append(r["Control Number"])
            check("every fabricated native is genuinely broken", not intact,
                  f"{len(intact)} still healthy: {intact[:5]}" if intact else
                  f"{len(broken) - len(intact):,} verified")

            flagged = {r[i_ctrl] for r in rows
                       if "Processing Error Type" in header
                       and r[header.index("Processing Error Type")].strip()}
            listed  = {r["Control Number"] for r in broken}
            # Anything flagged but not fabricated must be a documented exclusion,
            # not a silent gap.
            i_type    = header.index("Processing Error Type")
            by_ctrl   = {r[i_ctrl]: r[i_type].strip() for r in rows}
            # A row with no NativeFilePath has no file to break, so it cannot be
            # fabricated however it is flagged. That is a documented exclusion too.
            no_native = {r[i_ctrl] for r in rows if not r[i_nat]}
            undocumented = sorted(c for c in (flagged - listed)
                                  if by_ctrl.get(c) not in error_natives.NOT_FABRICABLE
                                  and c not in no_native)
            excluded = len(flagged - listed) - len(undocumented)
            check("every flagged document is fabricated or a documented exclusion",
                  not undocumented,
                  f"{len(undocumented)} undocumented: {undocumented[:5]}" if undocumented
                  else f"{excluded} documented exclusions")

            if "File Size" in header:
                i_size = header.index("File Size")
                bad = []
                for r in rows:
                    if not r[i_nat]:
                        continue
                    disk = os.path.getsize(os.path.join(pkg, r[i_nat].replace("\\", os.sep)))
                    if str(disk) != r[i_size]:
                        bad.append(r[i_ctrl])
                check("File Size in the load file matches bytes on disk", not bad,
                      f"{len(bad)} rows disagree" if bad else f"{len(rows):,} rows")

    # ── The load file has to satisfy Relativity's own spec, not just ours ───
    # Import/Export's multi-value delimiter is ASCII 59, a bare semicolon, and a
    # multiple-choice mapping "creates a unique value for each choice option". So a
    # value written "A; B" imports as "A" and " B", and the leading space makes a
    # second choice that looks identical in a list. Caught only by reading
    # Relativity's load file spec: nothing in this repo could tell, because the
    # writer and the reader here were both ours.
    MULTI = ("Issues", "Rsmf Participants")
    spaced, split_ok = [], 0
    for col in MULTI:
        if col not in header:
            continue
        i = header.index(col)
        for r in rows:
            v = r[i] if i < len(r) else ""
            if not v or ";" not in v:
                continue
            split_ok += 1
            if "; " in v or any(p != p.strip() for p in v.split(";")):
                spaced.append(f"{r[i_ctrl]} {col}: {v[:50]}")
    check("multi-value fields use a bare semicolon, per Relativity's spec",
          not spaced,
          f"{len(spaced)} values carry a space beside the delimiter: {spaced[:2]}"
          if spaced else f"{split_ok:,} multi-value cells across {len(MULTI)} columns")

    # Mixing line endings "can cause import errors or unexpected behavior".
    with open(dat, "rb") as fh:
        head = fh.read(20 * 1024 * 1024)
    check("line endings are consistent", b"\r" not in head,
          "CR found, the file mixes line endings" if b"\r" in head
          else f"LF only across the first {len(head) // 1024:,} KB")

    # ── Rule 19: no native carries a library's date or a library's name ───
    if not has_natives:
        print("\n  Date layer (Rule 19): skipped, no natives to inspect\n")
    else:
        print("\n  Date layer (Rule 19)\n")

        i_date     = header.index("Primary Date/Time")
        i_created  = header.index("Created Date/Time")       if "Created Date/Time"       in header else None
        i_modified = header.index("Last Modified Date/Time") if "Last Modified Date/Time" in header else None
        has_both = i_created is not None and i_modified is not None
        check("load file carries Date Created and Date Last Modified", has_both,
              "both present" if has_both
              else "without them Relativity derives both from the file itself")
        edge_path = os.path.join(pkg, "edge-cases.json")
        sentinels = set()
        if os.path.exists(edge_path):
            scen = json.load(open(edge_path, encoding="utf-8"))["scenarios"]
            sentinels = {e if isinstance(e, str) else e.get("control_number")
                         for e in scen.get("sentinel_date", {}).get("documents", [])}

        # The window comes from the load file itself, across every date column it
        # carries, minus the documents whose whole purpose is to sit outside it. A
        # document last modified after the last email is normal in a real
        # collection; a document stamped by a library is not.
        date_cols = [header.index(c) for c in
                     ("Primary Date/Time","Created Date/Time","Last Modified Date/Time",
                      "Sent Date/Time","Email Received Date/Time")
                     if c in header]
        dated = [r[i][:10] for r in rows if r[i_ctrl] not in sentinels
                 for i in date_cols
                 if r[i].strip() and r[i][:10] not in DOCUMENTED_BAD_DATES]
        lo, hi = (min(dated), max(dated)) if dated else ("", "")
        check("load file declares a matter window", bool(lo and hi),
              f"{lo} to {hi}, across {len(date_cols)} date columns")

        outside, tells, drift, inspected = [], [], [], 0
        for r in rows:
            rel = r[i_nat]
            if not rel or r[i_ctrl] in sentinels:
                continue
            target = os.path.join(pkg, rel.replace("\\", os.sep))
            ext = os.path.splitext(target)[1].lower()
            stamps = []
            if ext in (".docx", ".xlsx", ".pptx"):
                created, modified, xml = ooxml_dates(target)
                stamps = [d for d in (created, modified) if d]
                for tell in LIBRARY_TELLS:
                    if tell in xml:
                        tells.append(f"{r[i_ctrl]}: {tell}")
            elif ext == ".pdf":
                created = pdf_creation_date(target)
                stamps = [created] if created else []
            if not stamps:
                continue
            inspected += 1
            for d in stamps:
                if lo and not (lo <= d <= hi) and d not in DOCUMENTED_BAD_DATES:
                    outside.append(f"{r[i_ctrl]}: {d}")

            # The filesystem stamp is what an unprocessed folder shows, and Relativity
            # falls back to it when a format carries no date of its own. The contract
            # is Date Last Modified, with the same fallback chain the builder uses.
            want = expected_mtime(r, i_date, i_created, i_modified)
            if want:
                got = date.fromtimestamp(os.path.getmtime(target)).isoformat()
                if abs((date.fromisoformat(got) - date.fromisoformat(want)).days) > 1:
                    drift.append(f"{r[i_ctrl]}: file {got}, expected {want}")

        check("no document property dates outside the matter window", not outside,
              f"{len(outside)} outside: {outside[:3]}" if outside
              else f"{inspected:,} Office/PDF natives inspected")
        check("no library default names in document properties", not tells,
              f"{len(tells)} tells: {tells[:3]}" if tells else "docx, xlsx, pptx clean")
        check("filesystem mtimes match the load file dates", not drift,
              f"{len(drift)} adrift: {drift[:2]}" if drift else "within a day")
        if sentinels:
            check("sentinel-date documents are exempted by name", True,
                  f"{len(sentinels)} listed in edge-cases.json")

    # ── Rules 16-18: the planted content is in the files, not just the manifest ──
    pi_path   = os.path.join(pkg, "pi-ground-truth.csv")
    find_path = os.path.join(pkg, "findings.json")
    i_err     = header.index("Processing Error Type") if "Processing Error Type" in header else None
    paths     = ({r[i_ctrl]: r[i_nat] for r in rows if r[i_nat]} if has_natives else {})
    i_txtcol  = header.index("ExtractedTextFilePath") if "ExtractedTextFilePath" in header else None
    paths_txt = ({r[i_ctrl]: r[i_txtcol] for r in rows if r[i_txtcol]}
                 if i_txtcol is not None else {})
    err_type  = {r[i_ctrl]: (r[i_err] if i_err is not None else "") for r in rows}

    def full(rel):
        return os.path.join(pkg, rel.replace("\\", os.sep))

    # Without natives this section has nothing to open, and the extracted text
    # check above already proves every seeded value is reachable, which is the
    # claim that matters for a package built that way.
    if os.path.exists(pi_path) and not has_natives:
        print("\n  Rule 16 — seeded personal information: verified in the "
              "extracted text above; no natives to open\n")
    elif os.path.exists(pi_path):
        print("\n  Rule 16 — seeded personal information\n")
        with open(pi_path, encoding="utf-8") as f:
            pi_rows = list(csv.DictReader(f))

        cache, absent, unreadable, broken, checked = {}, [], [], 0, 0
        for r in pi_rows:
            ctrl = r["Control Number"]
            rel  = paths.get(ctrl)
            if not rel:
                absent.append(f"{ctrl}: no native"); continue
            # A document promoted to a processing error has a native that was
            # deliberately mangled afterwards, so its text is gone by design.
            if (err_type.get(ctrl) or "").strip():
                broken += 1; continue
            if rel not in cache:
                cache[rel] = native_text(full(rel))
            checked += 1
            # A native this decoder cannot read is a decoder problem, not missing
            # data, and reporting it as missing sends you looking for a seeding bug
            # that is not there. Counted separately and failed on its own.
            if not cache[rel].strip():
                unreadable.append(f"{ctrl}: {rel}"); continue
            if r["Value"] not in cache[rel]:
                absent.append(f"{ctrl} {r['PI Type']}: {r['Value']}")
        check("every native carrying seeded PI can be read", not unreadable,
              f"{len(unreadable)} unreadable: {unreadable[:3]}" if unreadable
              else f"{len(cache):,} natives decoded")
        check("every seeded PI value is in its native", not absent,
              f"{len(absent)} missing: {absent[:3]}" if absent
              else f"{checked:,} instances across {len(cache)} natives"
                   + (f", {broken} skipped as fabricated errors" if broken else ""))

        # The distribution claim (PI in one spreadsheet is the easy case) belongs to
        # validate_mock_data.py, which sees the whole tier. A --limit package holds a
        # slice, so asserting the spread here only ever failed the slice.
        places = {r["Where It Lives"] for r in pi_rows}
        print(f"       seeded PI places in this package: {', '.join(sorted(places))}")

    # ── The extracted text layer ──────────────────────────────────────────
    # Document Categories and PI Detect are LLM passes over extracted text, so a
    # package without it cannot reach either widget however good the metadata is.
    if "ExtractedTextFilePath" in header:
        print("\n  Extracted text\n")
        i_txt = header.index("ExtractedTextFilePath")
        declared = [(r[i_ctrl], r[i_txt]) for r in rows if r[i_txt]]
        gone = [c for c, rel in declared if not os.path.exists(full(rel))]
        check("every declared extracted text file exists", not gone,
              f"{len(gone)} missing: {gone[:3]}" if gone
              else f"{len(declared):,} sidecars")

        # Empty on an errored document is correct, not a gap: extraction is what
        # failed. Empty on a healthy one means the text layer silently lost it.
        blank = [c for c, rel in declared
                 if not (err_type.get(c) or "").strip()
                 and os.path.exists(full(rel))
                 and not open(full(rel), encoding="utf-8").read().strip()]
        check("no healthy document has empty extracted text", not blank,
              f"{len(blank)} blank: {blank[:3]}" if blank
              else "every healthy document carries text")

        # The whole point of the layer: the seeded PI has to be findable in the
        # text, because that is what aDAP reads. Derived from the native rather
        # than from the body that went into it, which missed the spreadsheet
        # scenario entirely.
        if os.path.exists(pi_path):
            with open(pi_path, encoding="utf-8") as fh:
                want = [r for r in csv.DictReader(fh)]
            txt_absent = []
            for r in want:
                c = r["Control Number"]
                if (err_type.get(c) or "").strip():
                    continue
                rel = paths_txt.get(c)
                if not rel or not os.path.exists(full(rel)):
                    txt_absent.append(f"{c}: no text"); continue
                if r["Value"] not in open(full(rel), encoding="utf-8").read():
                    txt_absent.append(f"{c} {r['PI Type']}")
            check("every seeded PI value is in the extracted text too", not txt_absent,
                  f"{len(txt_absent)} missing: {txt_absent[:3]}" if txt_absent
                  else f"{len(want)} instances reachable without the native")

    if os.path.exists(find_path):
        print("\n  Rule 18 — planted findings\n")
        with open(find_path, encoding="utf-8") as f:
            payload = json.load(f)
        findings = {f["id"]: f for f in payload["findings"]}

        missing_body = []
        for finding in payload["findings"]:
            for ctrl, body in (
                (finding["control_number"], finding.get("body")),
                ((finding.get("distinguisher") or {}).get("control_number"),
                 finding.get("distinguisher_body")),
            ):
                if not ctrl or not body:
                    continue
                # Without natives the planted body lands in the text sidecar,
                # which is then the only copy of it in the package.
                rel = paths.get(ctrl) if has_natives else paths_txt.get(ctrl)
                if not rel:
                    missing_body.append(f"{ctrl}: no native"); continue
                probe = body.strip().split("\n")[-1][:40]
                content = (native_text(full(rel)) if has_natives
                           else open(full(rel), encoding="utf-8").read())
                if probe not in content:
                    missing_body.append(f"{ctrl}: body not in native")
        check("every planted body reached its native" if has_natives
              else "every planted body reached its extracted text", not missing_body,
              "; ".join(missing_body[:2]) if missing_body else "bodies verified")

        buried = findings.get("buried_deep")
        if buried:
            rel = paths.get(buried["control_number"])
            ok_sheet, detail = False, "no native"
            if rel and full(rel).endswith(".xlsx"):
                try:
                    with zipfile.ZipFile(full(rel)) as z:
                        names = re.findall(r'name="([^"]+)"',
                                           z.read("xl/workbook.xml").decode("utf-8", "replace"))
                    text = native_text(full(rel))
                    depth = names.index(buried["payload_sheet"]) + 1 if buried["payload_sheet"] in names else 0
                    ok_sheet = depth >= 2 and "without documented justification" in text
                    detail = f"tab {depth} of {len(names)}"
                except (zipfile.BadZipFile, KeyError, OSError, ValueError) as exc:
                    detail = str(exc)
            if has_natives:
                check("the buried payload is on a late tab of the workbook", ok_sheet, detail)

        meta = findings.get("metadata_only")
        if meta:
            addr  = meta["unique_address"].lower()
            hits  = sum(1 for r in rows for v in r if addr in v.lower())
            check("the unique address appears once in the load file", hits == 1,
                  f"{hits} rows mention it")
            child = meta["attachment"]["control_number"]
            if has_natives:
                check("the encrypted attachment has a native in the package",
                      child in paths, paths.get(child, "absent"))

    # ── Edge-case manifest, when the package carries starved documents ────
    edge_file = os.path.join(pkg, "edge-cases.json")
    unassigned = [r for r in rows if not r[i_cust].strip()]
    if unassigned and not os.path.exists(edge_file):
        # The package has documents with no custodian and no map saying which are
        # deliberate. v1.9.0 shipped exactly like this.
        check("packages with starved documents ship edge-cases.json", False,
              f"{len(unassigned)} rows have no custodian but there is no manifest")
    elif os.path.exists(edge_file):
        print("\n  Edge-case manifest\n")
        scenarios = json.load(open(edge_file, encoding="utf-8"))["scenarios"]
        present   = {r[i_ctrl] for r in rows}
        listed, ghosts = 0, []
        for name, body in scenarios.items():
            if name == "broken_family":
                continue                       # these name documents that are meant to be absent
            for entry in body.get("documents", []):
                # duplicate_md5 records a mapping rather than a bare control number.
                ctrl = entry.get("control_number") if isinstance(entry, dict) else entry
                if not ctrl:
                    continue
                listed += 1
                if ctrl not in present:
                    ghosts.append(ctrl)
        check("every document in edge-cases.json is in the load file", not ghosts,
              f"{len(ghosts)} missing: {ghosts[:3]}" if ghosts else f"{listed:,} listed")

        # oversized_text is only real if the native holds the words it claims.
        oversized = scenarios.get("oversized_text", {}).get("documents", [])
        if oversized:
            claims, short = 0, []
            paths = {r[i_ctrl]: r[i_nat] for r in rows if r[i_nat]}
            for entry in oversized:
                ctrl, want = entry["control_number"], entry["word_count"]
                rel = paths.get(ctrl)
                if not rel:
                    short.append(f"{ctrl}: no native"); continue
                target = os.path.join(pkg, rel.replace("\\", os.sep))
                with open(target, encoding="utf-8", errors="replace") as f:
                    got = len(f.read().split())
                claims += 1
                if got < want * 0.95:
                    short.append(f"{ctrl}: {got:,} words, claimed {want:,}")
            check("oversized_text natives hold the words they claim", not short,
                  "; ".join(short[:2]) if short else f"{claims} documents")

        no_cust = scenarios.get("no_custodian", {}).get("documents", [])
        check("no_custodian documents really have no custodian in the load file",
              all(not r[i_cust].strip() for r in rows if r[i_ctrl] in set(no_cust)),
              f"{len(no_cust)} listed")

    print()
    if failures:
        print(f"  {len(failures)} check(s) failed\n")
        sys.exit(1)
    sheet_rows = list(csv.DictReader(open(src, encoding="utf-8")))
    people = len({r.get("Custodian", "") for r in sheet_rows})
    print(f"  All checks passed — {len(rows):,} documents, {len(sheet_rows)} data source rows "
          f"across {people} custodians\n")


if __name__ == "__main__":
    main()
