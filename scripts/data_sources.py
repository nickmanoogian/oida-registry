#!/usr/bin/env python3
"""
data_sources.py — The collection channel each document came from

RULES.md Rule 21. Collection Coverage exists to compare data sources, and the tiers
had no such axis: the only grouping available was custodian, so "sources with
genuinely different metadata profiles" was the longest-standing gap in the widget
coverage table.

The important thing about this rule is that it does not fabricate a difference. The
metadata profiles already vary, and they vary by file type:

    Email - MSG            606 documents, all with email metadata, no EXIF, no Drive
    Image - JPEG            25 documents, EXIF and OCR, no email metadata
    Chat - Teams (RSMF)     20 documents, RSMF fields, no email metadata
    Google Workspace        Drive fields populated, extension and type disagree
    PDF - Scanned           OCR required, shorter extracted text

A real collection produces those differences *because* the documents came through
different channels. This rule names the channel, so the difference becomes something
you can group by rather than something you can only infer from the file type. Every
profile claim in the manifest is measured from the tier, not asserted.

Two sources take a share of the loose-document population rather than a file type,
because in a real matter the same .docx can come from either: OneDrive for what sat
in a personal drive, Network Share for what sat on a file server.
"""

import collections
import random

# source -> (what it collects, what its metadata profile looks like)
SOURCES = {
    "Exchange Online": (
        "Mailbox collection: mail and calendar",
        "email metadata populated, no EXIF, no Drive fields"),
    "Exchange (PST export)": (
        "Archived mail handed over as container files",
        "container parents with no natives, children carry unreliable dates"),
    "OneDrive": (
        "Personal cloud drive: loose Office documents and PDFs",
        "Office properties populated, no email metadata"),
    "Network Share": (
        "File server: loose documents, archives and unsupported formats",
        "Office properties populated, no email metadata, ZIP containers. Shares a "
        "profile with OneDrive on purpose: two sources whose metadata looks the same "
        "is a real case, and a widget still has to group them separately"),
    "Google Workspace": (
        "Drive export: Docs, Sheets and Slides",
        "GoogleDrive fields populated, extension and type deliberately disagree"),
    "Microsoft Teams": (
        "Teams channel and chat export",
        "RSMF fields, placeholders for unsupported events, no email metadata"),
    "Slack Export": (
        "Slack workspace export",
        "RSMF fields keyed on the channel, no email metadata"),
    "Mobile Extraction (UFDR)": (
        "Cellebrite handset extraction: chat, photos, call logs",
        "EXIF including GPS, camera make and model, RSMF, structured call logs"),
    "Scanned Production": (
        "Paper production, scanned and OCR'd",
        "OCR required, shorter and messier extracted text, no email metadata"),
    "Bloomberg Vault": (
        "Financial messaging archive",
        "structured XML treated as a message container"),
}

# file type -> source. A tuple means the type is split across those sources, which is
# what happens to loose documents in a real collection.
BY_FILE_TYPE = {
    "Email - MSG":                      "Exchange Online",
    "Email - EML":                      "Exchange Online",
    "Calendar - ICS":                   "Exchange Online",
    "Email Container - PST":            "Exchange (PST export)",
    "Email Container - MBOX":           "Exchange (PST export)",
    "Office - Word (DOCX)":             ("OneDrive", "Network Share"),
    "Office - Word (DOC)":              ("Network Share", "OneDrive"),
    "Office - Excel (XLSX)":            ("OneDrive", "Network Share"),
    "Office - Excel (XLS)":             ("Network Share", "OneDrive"),
    "Office - PowerPoint (PPTX)":       ("OneDrive", "Network Share"),
    "Office - PowerPoint (PPT)":        ("Network Share", "OneDrive"),
    "Office - Visio":                   "Network Share",
    "PDF - Text":                       ("OneDrive", "Network Share"),
    "PDF - MIP Protected":              "OneDrive",
    "PDF - Scanned":                    "Scanned Production",
    "Image - TIFF":                     "Scanned Production",
    "Image - PNG":                      "Scanned Production",
    "Image - JPEG":                     "Mobile Extraction (UFDR)",
    "Image - HEIC":                     "Mobile Extraction (UFDR)",
    "Chat - Teams (RSMF)":              "Microsoft Teams",
    "Chat - Slack (RSMF)":              "Slack Export",
    "Chat - SMS (RSMF)":                "Mobile Extraction (UFDR)",
    "Chat - WhatsApp (RSMF)":           "Mobile Extraction (UFDR)",
    "Chat - Google Chat (RSMF)":        "Google Workspace",
    "Cellebrite Structured Excel":      "Mobile Extraction (UFDR)",
    "Google Workspace - Document":      "Google Workspace",
    "Google Workspace - Spreadsheet":   "Google Workspace",
    "Google Workspace - Presentation":  "Google Workspace",
    "Bloomberg XML":                    "Bloomberg Vault",
    "Text / Markup":                    ("Network Share", "OneDrive"),
    "Source Code":                      "Network Share",
    "Container - ZIP":                  "Network Share",
    "Audio / Video":                     ("Mobile Extraction (UFDR)", "Network Share"),
    "Unsupported":                      ("Network Share", "OneDrive"),
}

FALLBACK = "Network Share"

# How a split type divides. 70/30 rather than 50/50, because a personal drive and a
# file server do not hold equal shares of the same document type.
SPLIT_WEIGHTS = (0.7, 0.3)

# The measured columns that make one source's profile differ from another's. The
# manifest reports these per source, from the data, so a reader can see the profiles
# are real rather than take the description on trust.
PROFILE_FIELDS = {
    "email metadata":  lambda d: bool(d.get("Email From SMTP", "").strip()),
    "EXIF GPS":        lambda d: bool(str(d.get("GPS Latitude", "")).strip()),
    "camera model":    lambda d: bool(d.get("Camera Model", "").strip()),
    "Drive fields":    lambda d: bool(d.get("GoogleDrive/DocID", "").strip()),
    "RSMF fields":     lambda d: bool(d.get("Rsmf/Application", "").strip()),
    "OCR required":    lambda d: d.get("OCR Flag", "") == "Yes",
    "container":       lambda d: str(d.get("Level", "")) == "0",
    "Office properties": lambda d: bool(d.get("Author", "").strip()
                                        or d.get("Title", "").strip()),
}

SLUG = {name: name.replace(" (", "_").replace(")", "").replace(" ", "_")
        for name in SOURCES}

NOTE = ("The collection channel each document came through. The metadata profiles "
        "already varied by file type; this names the source that produced them, so "
        "the difference is something you can group by.")


def source_for(file_type, rng):
    """Which source a file type came from. Split types divide deterministically."""
    mapped = BY_FILE_TYPE.get(file_type, FALLBACK)
    if isinstance(mapped, tuple):
        return mapped[0] if rng.random() < SPLIT_WEIGHTS[0] else mapped[1]
    return mapped


def apply(all_docs, seed=42):
    """Set `Data Source` on every document. Returns the manifest.

    Runs before the other passes, because `Processing Folder Path` depends on it and
    Rule 11 makes that path a contract with the package on disk.
    """
    rng = random.Random(seed ^ 0x6D3F)        # own stream: never perturbs the narrative
    for d in all_docs:
        d["Data Source"] = source_for(d.get("File Type Category", ""), rng)
    return manifest(all_docs)


def manifest(all_docs):
    """Measure each source's profile from the data rather than describing it."""
    by_source = collections.defaultdict(list)
    for d in all_docs:
        by_source[d.get("Data Source", FALLBACK)].append(d)

    out = {}
    for name, docs in sorted(by_source.items(), key=lambda kv: -len(kv[1])):
        collects, profile = SOURCES.get(name, ("", ""))
        measured = {}
        for label, probe in PROFILE_FIELDS.items():
            n = sum(1 for d in docs if probe(d))
            if n:
                measured[label] = round(n / len(docs), 3)
        out[name] = {
            "collects": collects,
            "profile": profile,
            "folder": SLUG.get(name, name),
            "documents": len(docs),
            "custodians": len({d.get("Custodian", "") for d in docs if d.get("Custodian")}),
            "file_types": sorted({d.get("File Type Category", "") for d in docs}),
            "measured_share_of_its_documents": measured,
        }
    return {"note": NOTE, "sources": out}
