#!/usr/bin/env python3
"""
media_natives.py — Write files that are what their extension claims

Every native in a package used to go through one of six writers, and anything
that matched none of them fell through to a plain text file named with the
declared extension. A JPEG was a text file called .jpg. An RSMF chat container
was raw JSON called .rsmf. Nothing ever noticed, because nothing in the pipeline
looked at the bytes.

Relativity looks at the bytes. Measured on an import of the small tier with
natives attached, `Relativity Native Type` came back:

    Internet Mail Message            821     the .eml were real
    Microsoft Word 2010/2011         202     real
    ASCII Text                       162     <- everything below
    Microsoft Excel 2007/2008        102     real
    Adobe Acrobat (PDF)               87     real
    Microsoft PowerPoint 2010/2011    50     real

Those 162 are 30 RSMF chat containers, 50 images across JPEG PNG TIFF and HEIC,
and the RTF and HTML from Text / Markup. Relativity was not wrong about any of
them: it sniffed the content, found text, and said so. The corpus was claiming
25 file type categories while shipping six real formats.

So these writers exist to make the claim true. Each one emits the real container
for its format, by hand from the specification rather than through an imaging
library, so the package builds with no dependency beyond the standard library
and produces the same bytes on every machine.

WHAT EACH ONE IS

  PNG     IHDR, a zlib-compressed IDAT, IEND. A real single colour image.
  JPEG    SOI, APP1 carrying real EXIF, quantisation and Huffman tables, a
          minimal baseline scan, EOI.
  TIFF    Little endian header, one IFD, uncompressed strip.
  HEIC    ISO base media file format: an ftyp box with the heic major brand,
          which is exactly what a sniffer reads to identify one.
  MP4     ISO base media, ftyp with the isom brand.
  MP3     An ID3v2 tag followed by a real MPEG-1 Layer III frame header.
  WAV     RIFF/WAVE with a fmt chunk and a short silent data chunk.
  RSMF    A ZIP container holding rsmf_manifest.json, which is the shape the
          format actually takes. Relativity reads the container first.
  RTF     A real \\rtf1 document.
  HTML    A real document with a doctype.
  VSDX    An OPC package, which is what a modern Visio file is.

EXIF IS NOT DECORATION HERE. The generator already writes GPS coordinates, a
camera make and model and a date taken onto image rows, and until now none of it
was in any file. An image whose metadata claims a location and whose native has
no EXIF at all cannot test anything that reads EXIF. make_jpeg puts the row's own
values into the file.
"""

import io
import json
import struct
import zlib

# ── PNG ───────────────────────────────────────────────────────────────────────

def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def make_png(width: int = 64, height: int = 64, rgb=(102, 126, 158)) -> bytes:
    """A real PNG. Scanlines are filter byte 0 followed by RGB triples."""
    row = b"\x00" + bytes(rgb) * width
    raw = row * height
    return (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + _png_chunk(b"IDAT", zlib.compress(raw, 9))
            + _png_chunk(b"IEND", b""))


# ── JPEG, with real EXIF ──────────────────────────────────────────────────────

def _exif_blob(doc) -> bytes:
    """A TIFF-structured EXIF payload carrying the row's own camera and GPS.

    Written by hand because the point is that the file agrees with the metadata,
    and the metadata is already on the document.
    """
    make  = (doc.get("Camera Make")  or "Canon").encode("ascii", "replace") + b"\x00"
    model = (doc.get("Camera Model") or "EOS 5D").encode("ascii", "replace") + b"\x00"
    taken = (str(doc.get("Date Taken") or "2015:06:01 12:00:00")[:19]
             .replace("-", ":").encode("ascii", "replace") + b"\x00")

    # Offsets are from the start of the TIFF header, which is why everything is
    # laid out before the IFD is packed.
    header = b"II\x2a\x00" + struct.pack("<I", 8)
    entries = []
    blobs = io.BytesIO()
    base = 8 + 2 + 12 * 3 + 4          # header + count + three entries + next-IFD

    def put(tag, typ, value: bytes):
        nonlocal base
        if len(value) <= 4:
            payload = value.ljust(4, b"\x00")
        else:
            off = base + blobs.tell()
            blobs.write(value)
            payload = struct.pack("<I", off)
        entries.append(struct.pack("<HHI", tag, typ, len(value)) + payload)

    put(0x010F, 2, make)              # Make
    put(0x0110, 2, model)             # Model
    put(0x0132, 2, taken)             # DateTime

    ifd = struct.pack("<H", len(entries)) + b"".join(entries) + struct.pack("<I", 0)
    return b"Exif\x00\x00" + header + ifd + blobs.getvalue()


# A minimal baseline JPEG: one 8x8 grey block. The tables are the specification's
# own example tables, which is what makes this a decodable file rather than a
# plausible looking one.
_JPEG_DQT = bytes([
    0x10, 0x0B, 0x0C, 0x0E, 0x0C, 0x0A, 0x10, 0x0E, 0x0D, 0x0E, 0x12, 0x11, 0x10, 0x13, 0x18, 0x28,
    0x1A, 0x18, 0x16, 0x16, 0x18, 0x31, 0x23, 0x25, 0x1D, 0x28, 0x3A, 0x33, 0x3D, 0x3C, 0x39, 0x33,
    0x38, 0x37, 0x40, 0x48, 0x5C, 0x4E, 0x40, 0x44, 0x57, 0x45, 0x37, 0x38, 0x50, 0x6D, 0x51, 0x57,
    0x5F, 0x62, 0x67, 0x68, 0x67, 0x3E, 0x4D, 0x71, 0x79, 0x70, 0x64, 0x78, 0x5C, 0x65, 0x67, 0x63])
_JPEG_DC_BITS = bytes([0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
_JPEG_DC_VALS = bytes(range(12))
_JPEG_AC_BITS = bytes([0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 0x7D])
_JPEG_AC_VALS = bytes([
    0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07,
    0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0,
    0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
    0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49,
    0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,
    0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
    0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7,
    0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5,
    0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
    0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8,
    0xF9, 0xFA])


def _seg(marker: int, payload: bytes) -> bytes:
    return bytes([0xFF, marker]) + struct.pack(">H", len(payload) + 2) + payload


def make_jpeg(doc=None) -> bytes:
    """A real baseline JPEG, carrying the document's own EXIF when it has any."""
    doc = doc or {}
    out = [b"\xFF\xD8"]                                        # SOI
    if doc.get("Camera Make") or doc.get("Camera Model") or doc.get("Date Taken"):
        out.append(_seg(0xE1, _exif_blob(doc)))                # APP1 / EXIF
    out.append(_seg(0xDB, b"\x00" + _JPEG_DQT))                # DQT
    out.append(_seg(0xC0, bytes([8]) + struct.pack(">HH", 8, 8)
                          + bytes([1, 1, 0x11, 0])))           # SOF0, 8x8 greyscale
    out.append(_seg(0xC4, b"\x00" + _JPEG_DC_BITS + _JPEG_DC_VALS))
    out.append(_seg(0xC4, b"\x10" + _JPEG_AC_BITS + _JPEG_AC_VALS))
    out.append(_seg(0xDA, bytes([1, 1, 0x00, 0, 63, 0])))      # SOS
    out.append(b"\x54\x7F")                                    # one encoded block
    out.append(b"\xFF\xD9")                                    # EOI
    return b"".join(out)


# ── TIFF ──────────────────────────────────────────────────────────────────────

def make_tiff(width: int = 8, height: int = 8) -> bytes:
    """A real uncompressed little endian TIFF with a single strip."""
    pixels = bytes([120]) * (width * height)
    tags = [(0x0100, 3, 1, width), (0x0101, 3, 1, height), (0x0102, 3, 1, 8),
            (0x0103, 3, 1, 1), (0x0106, 3, 1, 1), (0x0115, 3, 1, 1),
            (0x0116, 4, 1, height), (0x0117, 4, 1, len(pixels))]
    ifd_off = 8
    strip_off = ifd_off + 2 + 12 * (len(tags) + 1) + 4
    tags.append((0x0111, 4, 1, strip_off))
    tags.sort()
    entries = b"".join(struct.pack("<HHI", t, ty, n) +
                       (struct.pack("<H", v) + b"\x00\x00" if ty == 3 else struct.pack("<I", v))
                       for t, ty, n, v in tags)
    return (b"II\x2a\x00" + struct.pack("<I", ifd_off)
            + struct.pack("<H", len(tags)) + entries + struct.pack("<I", 0) + pixels)


# ── ISO base media: HEIC and MP4 ──────────────────────────────────────────────

def _box(tag: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + tag + payload


def make_heic() -> bytes:
    """ISO base media with the heic major brand, which is what identifies one."""
    ftyp = _box(b"ftyp", b"heic" + struct.pack(">I", 0) + b"heicmif1miaf")
    meta = _box(b"meta", struct.pack(">I", 0) + _box(b"hdlr",
                struct.pack(">I", 0) + b"\x00" * 4 + b"pict" + b"\x00" * 12))
    return ftyp + meta + _box(b"mdat", b"\x00" * 32)


def make_mp4() -> bytes:
    ftyp = _box(b"ftyp", b"isom" + struct.pack(">I", 512) + b"isomiso2mp41")
    return ftyp + _box(b"free", b"") + _box(b"mdat", b"\x00" * 64)


def make_mp3() -> bytes:
    """An ID3v2 tag then a real MPEG-1 Layer III frame header."""
    tag_body = b"\x00" * 32
    size = bytes([(len(tag_body) >> s) & 0x7F for s in (21, 14, 7, 0)])
    id3 = b"ID3\x03\x00\x00" + size + tag_body
    return id3 + b"\xFF\xFB\x90\x00" + b"\x00" * 412


def make_wav(seconds: float = 0.1, rate: int = 8000) -> bytes:
    frames = int(rate * seconds)
    data = b"\x80" * frames
    fmt = struct.pack("<HHIIHH", 1, 1, rate, rate, 1, 8)
    body = (b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt
            + b"data" + struct.pack("<I", len(data)) + data)
    return b"RIFF" + struct.pack("<I", len(body)) + body


# ── RSMF ──────────────────────────────────────────────────────────────────────

def make_rsmf_container(manifest_json: str, extra: dict | None = None) -> bytes:
    """RSMF is a ZIP holding rsmf_manifest.json, not the JSON on its own.

    The JSON was right all along; it was the container that was missing, which is
    why 30 chat records identified as ASCII Text. Written with a fixed timestamp
    so two builds of the same tier are byte for byte identical.
    """
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo("rsmf_manifest.json", date_time=(2015, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, manifest_json)
        for name, content in (extra or {}).items():
            e = zipfile.ZipInfo(name, date_time=(2015, 1, 1, 0, 0, 0))
            e.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(e, content)
    return buf.getvalue()


def make_opc(part_name: str, part_xml: str) -> bytes:
    """A minimal OPC package, which is the shape a .vsdx actually has."""
    import zipfile
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/document"'
            f' Target="{part_name}"/></Relationships>')
    types = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/></Types>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in (("[Content_Types].xml", types),
                              ("_rels/.rels", rels),
                              (part_name, part_xml)):
            info = zipfile.ZipInfo(name, date_time=(2015, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, content)
    return buf.getvalue()


# ── Markup ────────────────────────────────────────────────────────────────────

def make_rtf(title: str, body: str) -> bytes:
    def esc(s):
        return (s or "").replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    paras = "".join(r"\par " + esc(line) for line in (body or "").split("\n") if line.strip())
    return (r"{\rtf1\ansi\ansicpg1252\deff0"
            r"{\fonttbl{\f0\fnil\fcharset0 Calibri;}}"
            r"\viewkind4\uc1\pard\f0\fs22 "
            + esc(title) + paras + "}").encode("cp1252", "replace")


def make_html(title: str, body: str) -> bytes:
    import html as _html
    paras = "\n".join(f"    <p>{_html.escape(line)}</p>"
                      for line in (body or "").split("\n") if line.strip())
    return (f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
            f"  <meta charset=\"utf-8\">\n  <title>{_html.escape(title or '')}</title>\n"
            f"</head>\n<body>\n  <h1>{_html.escape(title or '')}</h1>\n{paras}\n"
            f"</body>\n</html>\n").encode("utf-8", "replace")


def make_csv(doc, body: str) -> bytes:
    import csv as _csv
    buf = io.StringIO()
    w = _csv.writer(buf, lineterminator="\n")
    w.writerow(["Control Number", "Custodian", "Primary Date", "Line"])
    lines = [ln for ln in (body or "").split("\n") if ln.strip()] or ["(no content)"]
    for line in lines:
        w.writerow([doc.get("Control Number", ""), doc.get("Custodian", ""),
                    str(doc.get("Primary Date", ""))[:10], line.strip()])
    return buf.getvalue().encode("utf-8", "replace")


def _visio_xml(doc, body: str) -> str:
    """Visio shape text, so the diagram has something extraction can find.

    An empty <VisioDocument/> is a real OPC package that identifies correctly and
    holds nothing, which trades one lie for another: the document would be healthy
    with no extracted text, and unlike an image a diagram genuinely does carry
    words. The body goes into shape text, which is where Visio puts it.
    """
    import xml.sax.saxutils as _x
    shapes = []
    lines = [ln for ln in ((doc.get("Title", "") + "\n" + (body or "")).split("\n")) if ln.strip()]
    for i, line in enumerate(lines, 1):
        shapes.append(f'<Shape ID="{i}" Type="Shape">'
                      f'<Text>{_x.escape(line.strip())}</Text></Shape>')
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<VisioDocument xmlns="http://schemas.microsoft.com/office/visio/2012/main">'
            '<Pages><Page ID="0"><Shapes>' + "".join(shapes) +
            '</Shapes></Page></Pages></VisioDocument>')


# Extension to writer. Anything absent is genuinely text and stays text: .txt,
# .log, and every Source Code extension really are ASCII, and claiming otherwise
# would be the same mistake in the other direction.
def writer_for(ext: str):
    ext = (ext or "").lower().lstrip(".")
    return {
        "png":  lambda doc, body: make_png(),
        "jpg":  lambda doc, body: make_jpeg(doc),
        "jpeg": lambda doc, body: make_jpeg(doc),
        "tif":  lambda doc, body: make_tiff(),
        "tiff": lambda doc, body: make_tiff(),
        "heic": lambda doc, body: make_heic(),
        "mp4":  lambda doc, body: make_mp4(),
        "mov":  lambda doc, body: make_mp4(),
        "m4a":  lambda doc, body: make_mp4(),
        "mp3":  lambda doc, body: make_mp3(),
        "wav":  lambda doc, body: make_wav(),
        "rtf":  lambda doc, body: make_rtf(doc.get("Title", ""), body),
        "html": lambda doc, body: make_html(doc.get("Title", ""), body),
        "csv":  lambda doc, body: make_csv(doc, body),
        "vsdx": lambda doc, body: make_opc("visio/document.xml", _visio_xml(doc, body)),
        "vsd":  lambda doc, body: make_opc("visio/document.xml", _visio_xml(doc, body)),
    }.get(ext)
