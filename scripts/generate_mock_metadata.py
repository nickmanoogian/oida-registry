#!/usr/bin/env python3
"""
generate_mock_metadata.py — OIDA Relativity Mock Data Generator

Generates realistic Relativity workspace metadata conforming to the rules
defined in mock-data/RULES.md. Uses content patterns from the Opioid
Industry Documents Archive.

Usage:
  python scripts/generate_mock_metadata.py --tier small
  python scripts/generate_mock_metadata.py --tier medium
  python scripts/generate_mock_metadata.py --tier large
  python scripts/generate_mock_metadata.py --tier small --out ./custom/ --seed 99
"""

import argparse, csv, json, os, random
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_SEED = 42

# ── File Type Definitions ─────────────────────────────────────────────────
# Each entry encodes all workflow behavior per RULES.md Rule 2.

FILE_TYPES = {
    # ── Email ──
    "Email - MSG": {
        "extensions": ["msg"], "size_range": (15_000, 300_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "MD5",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
    },
    "Email - EML": {
        "extensions": ["eml"], "size_range": (10_000, 200_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "MD5",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
    },
    "Email Container - PST": {
        "extensions": ["pst"], "size_range": (50_000_000, 4_000_000_000),
        "images": "No", "ocr_required": "No", "native_produced": "No",
        "redactable": "No", "analytics_eligible": "No", "dedup_method": "N/A",
        "is_container": True, "supported": True,
        "has_natives": "No", "has_images": "No",
    },
    "Email Container - MBOX": {
        "extensions": ["mbox"], "size_range": (10_000_000, 2_000_000_000),
        "images": "No", "ocr_required": "No", "native_produced": "No",
        "redactable": "No", "analytics_eligible": "No", "dedup_method": "N/A",
        "is_container": True, "supported": True,
        "has_natives": "No", "has_images": "No",
    },
    "Calendar - ICS": {
        "extensions": ["ics"], "size_range": (2_000, 20_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
        "blank_date_sent": True,   # Rule 4 — ICS blank date
    },
    # ── Office ──
    "Office - Word (DOCX)": {
        "extensions": ["docx"], "size_range": (25_000, 800_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
    },
    "Office - Word (DOC)": {
        "extensions": ["doc"], "size_range": (20_000, 600_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
    },
    "Office - Excel (XLSX)": {
        "extensions": ["xlsx"], "size_range": (20_000, 5_000_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
    },
    "Office - Excel (XLS)": {
        "extensions": ["xls"], "size_range": (15_000, 3_000_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
    },
    "Office - PowerPoint (PPTX)": {
        "extensions": ["pptx"], "size_range": (100_000, 8_000_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
        "high_responsiveness": True,
    },
    "Office - PowerPoint (PPT)": {
        "extensions": ["ppt"], "size_range": (80_000, 6_000_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
        "high_responsiveness": True,
    },
    "Office - Visio": {
        "extensions": ["vsdx", "vsd"], "size_range": (50_000, 2_000_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "No", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
        "extraction_note": "Embedded images/objects not extracted",
    },
    # ── PDF ──
    "PDF - Text": {
        "extensions": ["pdf"], "size_range": (50_000, 3_000_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
    },
    "PDF - Scanned": {
        "extensions": ["pdf"], "size_range": (200_000, 8_000_000),
        "images": "Yes", "ocr_required": "Yes", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "After OCR", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
    },
    "PDF - MIP Protected": {
        "extensions": ["pdf"], "size_range": (50_000, 2_000_000),
        "images": "Limited", "ocr_required": "No", "native_produced": "Limited",
        "redactable": "No", "analytics_eligible": "No", "dedup_method": "SHA256",
        "is_container": False, "supported": False,
        "has_natives": "Yes", "has_images": "No",
        "processing_error": "MIP Protected - Limited Extraction",
    },
    # ── Chat / RSMF ──
    "Chat - Teams (RSMF)": {
        "extensions": ["rsmf"], "size_range": (10_000, 800_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "No",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "EventCollectionId",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
        "rsmf_application": "Teams",
    },
    "Chat - Slack (RSMF)": {
        "extensions": ["rsmf"], "size_range": (8_000, 500_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "No",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "EventCollectionId",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
        "rsmf_application": "Slack",
    },
    "Chat - SMS (RSMF)": {
        "extensions": ["rsmf"], "size_range": (2_000, 50_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "No",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "EventCollectionId",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
        "rsmf_application": "SMS",
    },
    "Chat - WhatsApp (RSMF)": {
        "extensions": ["rsmf"], "size_range": (3_000, 80_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "No",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "EventCollectionId",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
        "rsmf_application": "WhatsApp",
    },
    "Chat - Google Chat (RSMF)": {
        "extensions": ["rsmf"], "size_range": (5_000, 200_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "No",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "EventCollectionId",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
        "rsmf_application": "Google Chat",
    },
    "Bloomberg XML": {
        "extensions": ["xml"], "size_range": (10_000, 500_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
    },
    # ── Images ──
    "Image - JPEG": {
        "extensions": ["jpg", "jpeg"], "size_range": (200_000, 8_000_000),
        "images": "Yes", "ocr_required": "Yes", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "After OCR", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
        "has_exif": True,
    },
    "Image - HEIC": {
        "extensions": ["heic"], "size_range": (1_000_000, 10_000_000),
        "images": "Yes", "ocr_required": "Yes", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "After OCR", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
        "has_exif": True,
    },
    "Image - PNG": {
        "extensions": ["png"], "size_range": (100_000, 5_000_000),
        "images": "Yes", "ocr_required": "Yes", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "After OCR", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
        "has_exif": False,
    },
    "Image - TIFF": {
        "extensions": ["tif", "tiff"], "size_range": (500_000, 20_000_000),
        "images": "Yes", "ocr_required": "Yes", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "After OCR", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
        "has_exif": False,
    },
    # ── Google Workspace ──
    "Google Workspace - Document": {
        "extensions": ["docx"], "size_range": (20_000, 600_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
        "google_doc_type": "DOCUMENT",
    },
    "Google Workspace - Spreadsheet": {
        "extensions": ["xlsx"], "size_range": (15_000, 1_000_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
        "google_doc_type": "SPREADSHEET",
    },
    "Google Workspace - Presentation": {
        "extensions": ["pptx"], "size_range": (100_000, 5_000_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "Yes",
        "google_doc_type": "PRESENTATION",
    },
    # ── Other ──
    "Text / Markup": {
        "extensions": ["txt", "rtf", "html", "csv", "log"], "size_range": (1_000, 500_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
    },
    "Source Code": {
        "extensions": ["py", "js", "ts", "java", "sql", "yaml", "json"], "size_range": (500, 200_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
    },
    "Audio / Video": {
        "extensions": ["mp4", "mp3", "mov", "wav", "m4a"], "size_range": (500_000, 500_000_000),
        "images": "No", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "No", "analytics_eligible": "No", "dedup_method": "SHA256",
        "is_container": False, "supported": False,
        "has_natives": "Yes", "has_images": "No",
        "viewer_supported": "No",
    },
    "Cellebrite Structured Excel": {
        "extensions": ["xlsx"], "size_range": (20_000, 2_000_000),
        "images": "Yes", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "Image Only", "analytics_eligible": "Yes", "dedup_method": "SHA256",
        "is_container": False, "supported": True,
        "has_natives": "Yes", "has_images": "No",
    },
    "Container - ZIP": {
        "extensions": ["zip"], "size_range": (10_000, 200_000_000),
        "images": "No", "ocr_required": "No", "native_produced": "No",
        "redactable": "No", "analytics_eligible": "No", "dedup_method": "N/A",
        "is_container": True, "supported": True,
        "has_natives": "No", "has_images": "No",
        "date_unreliable": True,  # Rule 4 — ZIP timezone gap
    },
    "Unsupported": {
        "extensions": ["mdb", "accdb", "pages", "numbers", "key", "olm"], "size_range": (5_000, 10_000_000),
        "images": "No", "ocr_required": "No", "native_produced": "Yes",
        "redactable": "No", "analytics_eligible": "No", "dedup_method": "SHA256",
        "is_container": False, "supported": False,
        "has_natives": "Yes", "has_images": "No",
        "processing_error": "Unsupported File Type",
    },
}

# ── File type distributions per tier ─────────────────────────────────────
# Counts match mock-data/RULES.md Rule 1 exactly.

TIER_FILE_COUNTS = {
    "small": {
        "Email - MSG":                   600,
        "Email - EML":                   200,
        "Email Container - PST":           6,
        "Email Container - MBOX":          2,
        "Calendar - ICS":                 15,
        "Office - Word (DOCX)":          150,
        "Office - Word (DOC)":            50,
        "Office - Excel (XLSX)":          80,
        "Office - Excel (XLS)":           20,
        "Office - PowerPoint (PPTX)":     40,
        "Office - PowerPoint (PPT)":      10,
        "PDF - Text":                     80,
        "PDF - Scanned":                  12,
        "PDF - MIP Protected":             3,
        "Chat - Teams (RSMF)":            20,
        "Chat - Slack (RSMF)":            10,
        "Image - JPEG":                   25,
        "Image - HEIC":                   10,
        "Image - PNG":                    10,
        "Image - TIFF":                    5,
        "Text / Markup":                  50,
        "Audio / Video":                   5,
        "Unsupported":                    15,
        "Container - ZIP":                 8,
        "Office - Visio":                  4,
    },
    "medium": {
        "Email - MSG":                  3900,
        "Email - EML":                  1300,
        "Email Container - PST":          30,
        "Email Container - MBOX":         10,
        "Calendar - ICS":                150,
        "Office - Word (DOCX)":          900,
        "Office - Word (DOC)":           300,
        "Office - Excel (XLSX)":         530,
        "Office - Excel (XLS)":          170,
        "Office - PowerPoint (PPTX)":    280,
        "Office - PowerPoint (PPT)":      70,
        "PDF - Text":                    560,
        "PDF - Scanned":                 100,
        "PDF - MIP Protected":             5,
        "Chat - Teams (RSMF)":           300,
        "Chat - Slack (RSMF)":           200,
        "Chat - SMS (RSMF)":              60,
        "Chat - WhatsApp (RSMF)":         30,
        "Chat - Google Chat (RSMF)":      50,
        "Image - JPEG":                  180,
        "Image - HEIC":                   80,
        "Image - PNG":                    90,
        "Image - TIFF":                   50,
        "Google Workspace - Document":    60,
        "Google Workspace - Spreadsheet": 25,
        "Google Workspace - Presentation":15,
        "Text / Markup":                 250,
        "Source Code":                    50,
        "Audio / Video":                  30,
        "Cellebrite Structured Excel":    20,
        "Container - ZIP":                35,
        "Office - Visio":                 30,
        "Unsupported":                   100,
    },
    "large": {
        "Email - MSG":                 52500,
        "Email - EML":                 17500,
        "Email Container - PST":         300,
        "Email Container - MBOX":        100,
        "Calendar - ICS":               2000,
        "Office - Word (DOCX)":        11250,
        "Office - Word (DOC)":          3750,
        "Office - Excel (XLSX)":        7500,
        "Office - Excel (XLS)":         2500,
        "Office - PowerPoint (PPTX)":   4000,
        "Office - PowerPoint (PPT)":    1000,
        "PDF - Text":                   8000,
        "PDF - Scanned":                1700,
        "PDF - MIP Protected":            15,
        "Chat - Teams (RSMF)":          9000,
        "Chat - Slack (RSMF)":          6000,
        "Chat - SMS (RSMF)":            1500,
        "Chat - WhatsApp (RSMF)":        700,
        "Chat - Google Chat (RSMF)":    1500,
        "Bloomberg XML":                1000,
        "Image - JPEG":                 2700,
        "Image - HEIC":                 1200,
        "Image - PNG":                  1500,
        "Image - TIFF":                  600,
        "Google Workspace - Document":  1500,
        "Google Workspace - Spreadsheet":600,
        "Google Workspace - Presentation":400,
        "Text / Markup":                3500,
        "Source Code":                  1500,
        "Audio / Video":                 500,
        "Cellebrite Structured Excel":   300,
        "Container - ZIP":               200,
        "Office - Visio":                400,
        "Unsupported":                  1500,
    },
}

# ── Custodian Definitions ─────────────────────────────────────────────────

CUSTODIANS = {
    "small": [
        {"id": "C001", "name": "Michael Brennan",  "email": "michael.brennan@mallinckrodt.com",  "role": "VP, Sales & Marketing",   "dept": "Sales",          "doc_target": 700,  "hold": "Acknowledged", "hold_date": "2018-06-15", "key": True},
        {"id": "C002", "name": "Sarah Chen",        "email": "sarah.chen@mallinckrodt.com",       "role": "Regional Sales Director", "dept": "Sales",          "doc_target": 350,  "hold": "Acknowledged", "hold_date": "2018-06-18"},
        {"id": "C003", "name": "David Park",        "email": "david.park@mallinckrodt.com",       "role": "District Manager",        "dept": "Sales",          "doc_target": 300,  "hold": "Acknowledged", "hold_date": "2018-06-20"},
        {"id": "C004", "name": "Lisa Torres",       "email": "lisa.torres@mallinckrodt.com",      "role": "Executive Assistant",     "dept": "Administration", "doc_target": 150,  "hold": "Outstanding",  "hold_date": None},
    ],
    "medium": [
        {"id": "C001", "name": "James Whitfield",   "email": "james.whitfield@mallinckrodt.com",   "role": "Chief Executive Officer",   "dept": "Executive",          "doc_target": 1800, "hold": "Acknowledged", "hold_date": "2018-06-12", "key": True},
        {"id": "C002", "name": "Patricia Morrison", "email": "patricia.morrison@mallinckrodt.com", "role": "VP, Marketing",             "dept": "Marketing",          "doc_target": 1500, "hold": "Acknowledged", "hold_date": "2018-06-12", "key": True},
        {"id": "C003", "name": "Robert Ashton",     "email": "robert.ashton@mallinckrodt.com",     "role": "VP, Sales",                 "dept": "Sales",              "doc_target": 1200, "hold": "Acknowledged", "hold_date": "2018-06-13", "key": True},
        {"id": "C004", "name": "Sandra Nguyen",     "email": "sandra.nguyen@mallinckrodt.com",     "role": "Regional Sales Director",   "dept": "Sales",              "doc_target": 700,  "hold": "Acknowledged", "hold_date": "2018-06-15"},
        {"id": "C005", "name": "Thomas Bradley",    "email": "thomas.bradley@mallinckrodt.com",    "role": "Compliance Officer",        "dept": "Legal & Compliance", "doc_target": 600,  "hold": "Acknowledged", "hold_date": "2018-06-15"},
        {"id": "C006", "name": "Michelle Park",     "email": "michelle.park@mallinckrodt.com",     "role": "Medical Affairs Director",  "dept": "Medical Affairs",    "doc_target": 500,  "hold": "Acknowledged", "hold_date": "2018-06-18"},
        {"id": "C007", "name": "Kevin O'Brien",     "email": "kevin.obrien@mallinckrodt.com",      "role": "District Manager",          "dept": "Sales",              "doc_target": 400,  "hold": "Acknowledged", "hold_date": "2018-06-20"},
        {"id": "C008", "name": "Rachel Stern",      "email": "rachel.stern@mallinckrodt.com",      "role": "Executive Assistant",       "dept": "Administration",     "doc_target": 150,  "hold": "Acknowledged", "hold_date": "2018-06-22"},
        {"id": "C009", "name": "Frank DeLuca",      "email": "frank.deluca@mallinckrodt.com",      "role": "IT Systems Administrator",  "dept": "IT",                 "doc_target": 100,  "hold": "Escalated",    "hold_date": "2018-07-05"},
        {"id": "C010", "name": "Angela Washington", "email": "angela.washington@mallinckrodt.com", "role": "Legal Coordinator",         "dept": "Legal",              "doc_target": 50,   "hold": "Outstanding",  "hold_date": None},
    ],
    "large": [
        {"id": "C001",  "name": "James Whitfield",    "email": "james.whitfield@mallinckrodt.com",    "role": "Chief Executive Officer",        "dept": "Executive",          "doc_target": 12000, "hold": "Acknowledged", "hold_date": "2018-08-10", "key": True},
        {"id": "C002",  "name": "Mark Trevino",       "email": "mark.trevino@mallinckrodt.com",       "role": "Chief Commercial Officer",       "dept": "Executive",          "doc_target": 10000, "hold": "Acknowledged", "hold_date": "2018-08-10", "key": True},
        {"id": "C003",  "name": "Patricia Morrison",  "email": "patricia.morrison@mallinckrodt.com",  "role": "VP, Marketing",                  "dept": "Marketing",          "doc_target": 8000,  "hold": "Acknowledged", "hold_date": "2018-08-11", "key": True},
        {"id": "C004",  "name": "Robert Ashton",      "email": "robert.ashton@mallinckrodt.com",      "role": "VP, Sales",                      "dept": "Sales",              "doc_target": 7500,  "hold": "Acknowledged", "hold_date": "2018-08-11", "key": True},
        {"id": "C005",  "name": "Diana Kowalski",     "email": "diana.kowalski@mallinckrodt.com",     "role": "VP, Regulatory Affairs",         "dept": "Regulatory",         "doc_target": 6000,  "hold": "Acknowledged", "hold_date": "2018-08-12", "key": True},
        {"id": "C006",  "name": "Sandra Nguyen",      "email": "sandra.nguyen@mallinckrodt.com",      "role": "Regional Sales Director - East", "dept": "Sales",              "doc_target": 4500,  "hold": "Acknowledged", "hold_date": "2018-08-14"},
        {"id": "C007",  "name": "Thomas Bradley",     "email": "thomas.bradley@mallinckrodt.com",     "role": "Chief Compliance Officer",       "dept": "Legal & Compliance", "doc_target": 4000,  "hold": "Acknowledged", "hold_date": "2018-08-14"},
        {"id": "C008",  "name": "Michelle Park",      "email": "michelle.park@mallinckrodt.com",      "role": "Medical Affairs Director",       "dept": "Medical Affairs",    "doc_target": 3500,  "hold": "Acknowledged", "hold_date": "2018-08-15"},
        {"id": "C009",  "name": "Kevin O'Brien",      "email": "kevin.obrien@mallinckrodt.com",       "role": "Regional Sales Director - West", "dept": "Sales",              "doc_target": 3000,  "hold": "Acknowledged", "hold_date": "2018-08-15"},
        {"id": "C010",  "name": "Laura Finnegan",     "email": "laura.finnegan@mallinckrodt.com",     "role": "Director, Government Affairs",   "dept": "Government Affairs", "doc_target": 2800,  "hold": "Acknowledged", "hold_date": "2018-08-16"},
        {"id": "C011",  "name": "Brian Holloway",     "email": "brian.holloway@mallinckrodt.com",     "role": "National Sales Manager",         "dept": "Sales",              "doc_target": 2500,  "hold": "Acknowledged", "hold_date": "2018-08-18"},
        {"id": "C012",  "name": "Cynthia Rhodes",     "email": "cynthia.rhodes@mallinckrodt.com",     "role": "Director, Clinical Research",    "dept": "Medical Affairs",    "doc_target": 2200,  "hold": "Acknowledged", "hold_date": "2018-08-18"},
        {"id": "C013",  "name": "Eric Sandoval",      "email": "eric.sandoval@mallinckrodt.com",      "role": "District Manager - Midwest",     "dept": "Sales",              "doc_target": 1800,  "hold": "Acknowledged", "hold_date": "2018-08-20"},
        {"id": "C014",  "name": "Jennifer Watts",     "email": "jennifer.watts@mallinckrodt.com",     "role": "Senior Marketing Manager",       "dept": "Marketing",          "doc_target": 1600,  "hold": "Acknowledged", "hold_date": "2018-08-20"},
        {"id": "C015",  "name": "Gregory Nash",       "email": "gregory.nash@mallinckrodt.com",       "role": "Director, SOM Compliance",       "dept": "Legal & Compliance", "doc_target": 1400,  "hold": "Acknowledged", "hold_date": "2018-08-22"},
        {"id": "C016",  "name": "Amanda Pierce",      "email": "amanda.pierce@mallinckrodt.com",      "role": "District Manager - Southeast",   "dept": "Sales",              "doc_target": 1200,  "hold": "Acknowledged", "hold_date": "2018-08-22"},
        {"id": "C017",  "name": "Steven Calloway",    "email": "steven.calloway@mallinckrodt.com",    "role": "Sr. Medical Science Liaison",    "dept": "Medical Affairs",    "doc_target": 1000,  "hold": "Acknowledged", "hold_date": "2018-08-24"},
        {"id": "C018",  "name": "Natalie Cruz",       "email": "natalie.cruz@mallinckrodt.com",       "role": "Marketing Manager - Branded",    "dept": "Marketing",          "doc_target": 900,   "hold": "Acknowledged", "hold_date": "2018-08-24"},
        {"id": "C019",  "name": "Daniel Cho",         "email": "daniel.cho@mallinckrodt.com",         "role": "Regulatory Affairs Manager",     "dept": "Regulatory",         "doc_target": 800,   "hold": "Acknowledged", "hold_date": "2018-08-26"},
        {"id": "C020",  "name": "Melissa Grant",      "email": "melissa.grant@mallinckrodt.com",      "role": "Associate General Counsel",      "dept": "Legal",              "doc_target": 700,   "hold": "Acknowledged", "hold_date": "2018-08-26"},
        {"id": "C021",  "name": "Paul Whitmore",      "email": "paul.whitmore@mallinckrodt.com",      "role": "District Manager - Southwest",   "dept": "Sales",              "doc_target": 600,   "hold": "Acknowledged", "hold_date": "2018-08-28"},
        {"id": "C022",  "name": "Rachel Stern",       "email": "rachel.stern@mallinckrodt.com",       "role": "Executive Assistant - CCO",      "dept": "Administration",     "doc_target": 500,   "hold": "Acknowledged", "hold_date": "2018-08-28"},
        {"id": "C023",  "name": "Carlos Ibarra",      "email": "carlos.ibarra@mallinckrodt.com",      "role": "Inside Sales Representative",    "dept": "Sales",              "doc_target": 400,   "hold": "Acknowledged", "hold_date": "2018-09-02"},
        {"id": "C024",  "name": "Heather Bloom",      "email": "heather.bloom@mallinckrodt.com",      "role": "Clinical Educator",              "dept": "Medical Affairs",    "doc_target": 350,   "hold": "Acknowledged", "hold_date": "2018-09-02"},
        {"id": "C025",  "name": "Timothy Marsh",      "email": "timothy.marsh@mallinckrodt.com",      "role": "Trade Relations Manager",        "dept": "Sales",              "doc_target": 300,   "hold": "Acknowledged", "hold_date": "2018-09-05"},
        {"id": "C026",  "name": "Donna Callahan",     "email": "donna.callahan@mallinckrodt.com",     "role": "Sales Operations Analyst",       "dept": "Sales",              "doc_target": 250,   "hold": "Acknowledged", "hold_date": "2018-09-05"},
        {"id": "C027",  "name": "Frank DeLuca",       "email": "frank.deluca@mallinckrodt.com",       "role": "IT Systems Administrator",       "dept": "IT",                 "doc_target": 200,   "hold": "Acknowledged", "hold_date": "2018-09-10"},
        {"id": "C028",  "name": "Sarah Patel",        "email": "sarah.patel@mallinckrodt.com",        "role": "HR Business Partner",            "dept": "Human Resources",    "doc_target": 180,   "hold": "Acknowledged", "hold_date": "2018-09-10"},
        {"id": "C029",  "name": "Walter Kim",         "email": "walter.kim@mallinckrodt.com",         "role": "Finance Manager",                "dept": "Finance",            "doc_target": 150,   "hold": "Escalated",    "hold_date": "2018-09-12"},
        {"id": "C030",  "name": "Nicole Russo",       "email": "nicole.russo@mallinckrodt.com",       "role": "Senior Paralegal",               "dept": "Legal",              "doc_target": 130,   "hold": "Acknowledged", "hold_date": "2018-09-15"},
        {"id": "C031",  "name": "Andrew Flynn",       "email": "andrew.flynn@mallinckrodt.com",       "role": "Quality Assurance Specialist",   "dept": "Quality",            "doc_target": 110,   "hold": "Acknowledged", "hold_date": "2018-09-15"},
        {"id": "C032",  "name": "Tiffany Bell",       "email": "tiffany.bell@mallinckrodt.com",       "role": "Administrative Coordinator",     "dept": "Administration",     "doc_target": 100,   "hold": "Acknowledged", "hold_date": "2018-09-18"},
        {"id": "C033",  "name": "Marcus Webb",        "email": "marcus.webb@mallinckrodt.com",        "role": "Government Pricing Analyst",     "dept": "Finance",            "doc_target": 90,    "hold": "Acknowledged", "hold_date": "2018-09-18"},
        {"id": "C034",  "name": "Irene Hoffman",      "email": "irene.hoffman@mallinckrodt.com",      "role": "Contracts Manager",              "dept": "Legal",              "doc_target": 80,    "hold": "Acknowledged", "hold_date": "2018-09-20"},
        {"id": "C035",  "name": "Owen Garrett",       "email": "owen.garrett@mallinckrodt.com",       "role": "Lab Technician",                 "dept": "R&D",                "doc_target": 70,    "hold": "Acknowledged", "hold_date": "2018-09-20"},
        {"id": "C036",  "name": "Priya Mehta",        "email": "priya.mehta@mallinckrodt.com",        "role": "Business Intelligence Analyst",  "dept": "Sales",              "doc_target": 60,    "hold": "Acknowledged", "hold_date": "2018-09-22"},
        {"id": "C037",  "name": "Jason Dunn",         "email": "jason.dunn@mallinckrodt.com",         "role": "Warehouse Supervisor",           "dept": "Operations",         "doc_target": 50,    "hold": "Acknowledged", "hold_date": "2018-09-25"},
        {"id": "C038",  "name": "Claire Simmons",     "email": "claire.simmons@mallinckrodt.com",     "role": "Receptionist",                   "dept": "Administration",     "doc_target": 40,    "hold": "Outstanding",  "hold_date": None},
        {"id": "C039",  "name": "Victor Okafor",      "email": "victor.okafor@mallinckrodt.com",      "role": "Supply Chain Analyst",           "dept": "Operations",         "doc_target": 30,    "hold": "Outstanding",  "hold_date": None},
        {"id": "C040",  "name": "Angela Washington",  "email": "angela.washington@mallinckrodt.com",  "role": "Legal Coordinator",              "dept": "Legal",              "doc_target": 20,    "hold": "Outstanding",  "hold_date": None},
    ],
}

# ── Workflow Distributions ────────────────────────────────────────────────

WORKFLOW = {
    "small": {
        "dup_nist_pct": 0.10, "processing_error_pct": 0.06, "eca_excluded_pct": 0.33,
        "reviewed_pct": 0.80, "inprogress_pct": 0.12, "unreviewed_pct": 0.08,
        "responsive_pct": 0.30, "nonresponsive_pct": 0.63, "notsure_pct": 0.07,
        "privilege_pct": 0.12, "hot_pct": 0.02, "redacted_pct": 0.08,
        "bates_prefix": "MNK", "productions": 1,
    },
    "medium": {
        "dup_nist_pct": 0.175, "processing_error_pct": 0.09, "eca_excluded_pct": 0.45,
        "reviewed_pct": 0.636, "inprogress_pct": 0.182, "unreviewed_pct": 0.182,
        "responsive_pct": 0.286, "nonresponsive_pct": 0.650, "notsure_pct": 0.064,
        "privilege_pct": 0.12, "hot_pct": 0.015, "redacted_pct": 0.07,
        "bates_prefix": "MNK", "productions": 2,
    },
    "large": {
        "dup_nist_pct": 0.15, "processing_error_pct": 0.067, "eca_excluded_pct": 0.467,
        "reviewed_pct": 0.692, "inprogress_pct": 0.154, "unreviewed_pct": 0.154,
        "responsive_pct": 0.333, "nonresponsive_pct": 0.600, "notsure_pct": 0.067,
        "privilege_pct": 0.133, "hot_pct": 0.013, "redacted_pct": 0.10,
        "bates_prefix": "MNK", "productions": 4,
    },
}

DATE_RANGES = {
    "small":  ("2013-01-01", "2016-12-31"),
    "medium": ("2012-01-01", "2017-12-31"),
    "large":  ("2010-01-01", "2018-06-30"),
}

# ── Content Seeds ─────────────────────────────────────────────────────────

EMAIL_SUBJECTS = [
    "RE: Q{q} {year} Territory Performance Report",
    "FW: DEA Suspicious Order Monitoring - {month} {year}",
    "Oxycodone Market Share Update - {territory}",
    "RE: Speaker Bureau Physician Engagement - {month}",
    "Sales Training Materials - {product} Launch",
    "FW: Customer Complaint - Pharmacy Hold Resolution",
    "RE: {product} Managed Care Coverage Update",
    "Monthly SOM Report - {month} {year}",
    "RE: District Sales Results - {territory}",
    "FW: Compliance Training Completion - {month} {year}",
    "RE: DEA Quota Allocation - {year}",
    "{product} Formulary Win - {territory}",
    "RE: FDA Inquiry Response - Draft",
    "FW: Wholesaler Order Flagged for Review",
    "RE: Key Account Update - {account}",
    "RE: REMS Program Compliance - {product}",
    "FW: IMS Data - {month} {year}",
    "RE: Territory Business Plan - {year}",
    "RE: {product} Patient Assistance Program",
    "FW: Legal Hold Notice - Action Required",
]

OFFICE_TITLES = [
    "{product} Sales Training Module {n}",
    "Territory Business Plan {year} - {territory}",
    "Speaker Bureau Program Guidelines",
    "Q{q} {year} Marketing Presentation",
    "SOM Policy and Procedure Manual v{n}.0",
    "Key Account Strategy - {account}",
    "{product} Market Analysis - {year}",
    "DEA Compliance Training Slides",
    "Managed Care Coverage Grid",
    "Annual Incentive Compensation Plan {year}",
    "Medical Affairs Engagement Protocol",
    "Distribution Channel Review - {quarter}",
]

RSMF_CHANNELS = [
    "sales-northeast-team", "compliance-updates", "marketing-general",
    "speaker-bureau-ops", "som-alerts", "legal-hold-notices",
    "product-launch-exalgo", "managed-care-wins", "district-managers",
    "executive-leadership", "medical-affairs", "regulatory-team",
]

PRODUCTS    = ["OxyContin", "Exalgo", "Pennsaid", "Subsys", "Duexis", "Xartemis XR", "Sumavel", "Opana ER"]
TERRITORIES = ["Northeast", "Southeast", "Midwest", "Southwest", "Northwest", "Mid-Atlantic", "Gulf Coast", "Great Lakes"]
ACCOUNTS    = ["Walgreens", "CVS Health", "Cardinal Health", "McKesson", "AmerisourceBergen", "Express Scripts"]
MONTHS      = ["January","February","March","April","May","June","July","August","September","October","November","December"]
QUARTERS    = ["Q1","Q2","Q3","Q4"]

PRIVILEGE_REASONS   = ["Attorney-Client Communication", "Work Product - Litigation Preparation", "Attorney-Client - Outside Counsel", "Work Product - Regulatory Response"]
ECA_REASONS         = ["Date Out of Range", "Domain Excluded - Opposing Counsel", "No Keyword Hits", "File Type Excluded", "Domain Excluded - Personal", "System File"]
PROC_ERRORS         = ["Password Protected", "Corrupt File", "Unsupported File Type", "Extraction Failure", "OCR Failure - Poor Scan Quality", "Container Extraction Timeout", "Teams Conversion Error", "MIP Protected - Limited Extraction"]
CULL_REASONS        = ["NIST System File", "Exact Duplicate", "Near Duplicate", "Below De Minimis"]
ISSUE_TAGS          = ["Marketing Practices", "DEA Reporting", "Speaker Bureau", "Sales Incentives", "FDA Communications", "Suspicious Orders", "REMS Compliance", "Key Custodian Communication"]
CAMERA_MAKES        = ["Apple", "Samsung", "Google", "Apple", "Apple"]
CAMERA_MODELS       = {"Apple": ["iPhone 12 Pro", "iPhone 13", "iPhone 14 Pro Max"], "Samsung": ["Galaxy S21", "Galaxy S22"], "Google": ["Pixel 6", "Pixel 7"]}

GOOGLE_SHARED_DRIVE = "SDR-2847-MARKETING-SHARED"

EXTERNAL_CONTACTS = [
    ("Dr. Alan Foster", "alan.foster@painspecialists.com"),
    ("Dr. Maria Santos", "msantos@regionalhospital.org"),
    ("Karen Harper", "karen.harper@covidien.com"),
    ("DEA Diversion Control", "diversion@dea.gov"),
    ("FDA CDER", "cder@fda.hhs.gov"),
    ("Bradley Tevelow", "bradley.tevelow@mckinsey.com"),
    ("Dr. Susan Ellis", "sellis@painclinic.net"),
    ("State AG Office", "inquiry@ag.state.us"),
]

# ── Helpers ───────────────────────────────────────────────────────────────

def fake_hash(bits=128):
    return "%0*x" % (bits // 4, random.getrandbits(bits))

def fake_message_id():
    return "<%s.%s@mallinckrodt.com>" % (fake_hash(64), fake_hash(32))

def random_date(start, end):
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end,   "%Y-%m-%d")
    return s + timedelta(days=random.randint(0, (e - s).days))

def fmt_dt(dt):  return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""
def fmt_d(dt):   return dt.strftime("%Y-%m-%d") if dt else ""

def expand(tmpl, date_range):
    yr = random.randint(int(date_range[0][:4]), int(date_range[1][:4]))
    return (tmpl
            .replace("{q}", str(random.randint(1,4)))
            .replace("{quarter}", random.choice(QUARTERS))
            .replace("{year}", str(yr))
            .replace("{month}", random.choice(MONTHS))
            .replace("{territory}", random.choice(TERRITORIES))
            .replace("{product}", random.choice(PRODUCTS))
            .replace("{account}", random.choice(ACCOUNTS))
            .replace("{n}", str(random.randint(1,8))))

def tar_score():
    band = random.random()
    if   band < 0.40: return round(random.uniform(0, 20), 2)
    elif band < 0.75: return round(random.uniform(75, 100), 2)
    else:             return round(random.uniform(20, 75), 2)

def gps_coord():
    return round(random.uniform(-90, 90), 6), round(random.uniform(-180, 180), 6), round(random.uniform(0, 500), 1)

# ── Document builder ──────────────────────────────────────────────────────

def make_doc(ctrl, custodian, ft_name, ft_meta, date_range, custs, bates_counter, wf):
    dr = date_range
    date = random_date(*dr)
    ext  = random.choice(ft_meta["extensions"])
    size = random.randint(*ft_meta["size_range"])

    is_email    = ft_name.startswith("Email -")
    is_calendar = ft_name == "Calendar - ICS"
    is_rsmf     = "RSMF" in ft_name or ft_name in ("Bloomberg XML",)
    is_office   = ft_name.startswith("Office -") or ft_name.startswith("Google Workspace -")
    is_pdf      = ft_name.startswith("PDF")
    is_image    = ft_name.startswith("Image -")
    is_google   = ft_name.startswith("Google Workspace -")
    is_container = ft_meta.get("is_container", False)

    subject = expand(random.choice(EMAIL_SUBJECTS), dr) if is_email or is_calendar else ""
    title   = expand(random.choice(OFFICE_TITLES),  dr) if is_office and not is_email else ""

    # To/From
    if is_email:
        to_person = random.choice(list(custs) + list(EXTERNAL_CONTACTS))
        if isinstance(to_person, dict):
            to_name, to_email_addr = to_person["name"], to_person["email"]
        else:
            to_name, to_email_addr = to_person
    else:
        to_name = to_email_addr = ""

    # RSMF fields
    rsmf_app = ft_meta.get("rsmf_application", "")
    rsmf_participants = ""
    rsmf_msgs = 0
    rsmf_begin = rsmf_end = rsmf_evt = ""
    rsmf_has_placeholders = "No"
    if is_rsmf or ft_name == "Chat - Teams (RSMF)":
        participants = [custodian["name"]] + [c["name"] for c in random.sample(custs, min(3, len(custs)))]
        rsmf_participants = "; ".join(set(participants))
        rsmf_msgs  = random.randint(5, 120)
        rsmf_begin = fmt_dt(date)
        rsmf_end   = fmt_dt(date + timedelta(hours=random.randint(1, 48)))
        rsmf_evt   = fake_hash(64)
        if ft_name == "Chat - Teams (RSMF)" and random.random() < 0.15:
            rsmf_has_placeholders = "Yes"

    # Image / EXIF fields
    gps_lat = gps_lon = gps_alt = ""
    camera_make = camera_model = ""
    date_taken = ""
    if is_image:
        has_exif = ft_meta.get("has_exif", False)
        if has_exif and random.random() < 0.15:  # 15% have GPS
            lat, lon, alt = gps_coord()
            gps_lat, gps_lon, gps_alt = lat, lon, alt
        if has_exif:
            make = random.choice(CAMERA_MAKES)
            camera_make  = make
            camera_model = random.choice(CAMERA_MODELS.get(make, ["Unknown"]))
            date_taken   = fmt_dt(date)

    # Google Workspace fields
    google_doc_id = google_doc_type = google_shared_drive = google_source_hash = ""
    if is_google:
        google_doc_id    = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"[:26] + fake_hash(32)[:6]
        google_doc_type  = ft_meta.get("google_doc_type", "DOCUMENT")
        if random.random() < 0.20:
            google_shared_drive = GOOGLE_SHARED_DRIVE
        google_source_hash = fake_hash(256)

    # ICS — blank date sent (Rule 4)
    date_sent = fmt_dt(date) if is_email else ""
    date_received = fmt_dt(date + timedelta(minutes=random.randint(1,30))) if is_email else ""
    if is_calendar:
        date_sent = date_received = ""  # Rule 4

    # ZIP children — date gap (Rule 4)
    date_created = fmt_d(date)
    if ft_meta.get("date_unreliable") and random.random() < 0.30:
        date_created = "1980-01-01"

    # OCR flag
    ocr_flag = "Yes" if ft_meta.get("ocr_required") == "Yes" else "No"

    # Viewer support
    viewer_supported = "No" if ft_meta.get("viewer_supported") == "No" else "Yes"

    # Pages
    pages = random.randint(1, 30) if is_pdf or ft_name in ("Office - Word (DOCX)", "Office - Word (DOC)", "Office - PowerPoint (PPTX)", "Office - PowerPoint (PPT)") else random.randint(1, 5)

    return {
        # ── Universal ──
        "Control Number":         ctrl,
        "File Name":              f"{subject[:40].replace('/', '-')}.{ext}" if is_email else f"{ctrl}.{ext}",
        "File Extension":         ext,
        "File Type Category":     ft_name,
        "File Size (bytes)":      size,
        "MD5 Hash":               fake_hash(128),
        "SHA256 Hash":            fake_hash(256),
        "Custodian":              custodian["name"],
        "Custodian Email":        custodian["email"],
        "Custodian Department":   custodian.get("dept", ""),
        "Processing Folder Path": f"\\\\Collection\\{custodian['name'].replace(' ','_')}\\{date.year}\\{date.strftime('%m')}",
        "Virtual Path":           f"{custodian['name'].replace(' ','_')}\\{ft_name}\\{ctrl}.{ext}",
        "Container ID":           "",
        "Container Name":         "",
        "Container Extension":    "",
        "Level":                  "0" if is_container else "1",
        "Primary Date":           fmt_dt(date),
        "Sort Date":              fmt_dt(date),
        "Language":               "English",
        "Has Images":             ft_meta["has_images"],
        "Has Natives":            ft_meta["has_natives"],
        "OCR Flag":               ocr_flag,
        "Supported by Viewer":    viewer_supported,
        "Extracted Text Preview": "" if ft_meta.get("processing_error") == "MIP Protected - Limited Extraction" else
                                  f"[{ft_name}] {subject or title} — {custodian['name']} {fmt_d(date)}",
        # ── Workflow Behavior (Rule 2) ──
        "Images?":                ft_meta["images"],
        "OCR Required?":          ft_meta["ocr_required"],
        "Native Produced?":       ft_meta["native_produced"],
        "Redactable?":            ft_meta["redactable"],
        "Analytics Eligible?":    ft_meta["analytics_eligible"],
        "Dedup Method":           ft_meta["dedup_method"],
        # ── Workflow Stage (set later) ──
        "Workflow Stage":         "",
        "Cull Reason":            "",
        "Processing Status":      "Complete",
        "Processing Error Type":  ft_meta.get("processing_error", ""),
        "Duplicate Spare":        "No",
        "ECA Exclusion Reason":   "",
        "Batch Name":             "",
        "Batch Status":           "",
        "Reviewer":               "",
        "Date First Assigned":    "",
        "Responsiveness":         "",
        "Privilege":              "",
        "Privilege Reason":       "",
        "Hot Doc":                "No",
        "Issue Tags":             "",
        "Bates Begin":            "",
        "Bates End":              "",
        "Page Count":             pages,
        "Production Set":         "",
        "Redacted":               "No",
        "Redaction Reason":       "",
        "TAR Score":              "",
        "AL Predicted Relevant":  "",
        # ── Email fields ──
        "Email From":             custodian["name"] if is_email else "",
        "Email From SMTP":        custodian["email"] if is_email else "",
        "Email To":               to_name,
        "Email To SMTP":          to_email_addr,
        "Email CC":               "",
        "Email CC SMTP":          "",
        "Email BCC":              "",
        "Email BCC SMTP":         "",
        "Email Subject":          subject,
        "Message ID":             fake_message_id() if is_email else "",
        "In Reply To":            "",
        "Date Sent":              date_sent,
        "Date Received":          date_received,
        "Conversation Topic":     subject if is_email else "",
        "Conversation Index":     fake_hash(128) if is_email else "",
        "Has Attachments":        "Yes" if is_email and random.random() < 0.35 else "No",
        "Attachment Count":       random.randint(1,4) if is_email and random.random() < 0.35 else 0,
        "Email Thread ID":        "",
        "Email Threading Inclusive": "",
        "Importance":             random.choice(["Normal","Normal","Normal","High","Low"]) if is_email else "",
        "Parent Document ID":     "",
        "Family ID":              "",
        # ── Office / Document fields ──
        "Author":                 custodian["name"] if is_office else "",
        "Last Modified By":       custodian["name"] if is_office else "",
        "Date Created":           date_created if is_office or ft_name == "Container - ZIP" else "",
        "Date Last Modified":     fmt_d(date + timedelta(days=random.randint(0,30))) if is_office else "",
        "Title":                  title,
        "Company":                "Mallinckrodt Inc." if is_office else "",
        "Word Count":             random.randint(200,8000) if "Word" in ft_name else "",
        "Slide Count":            random.randint(5,45) if "PowerPoint" in ft_name else "",
        "Sheet Names":            "Sheet1; Sheet2" if "Excel" in ft_name else "",
        # ── PDF fields ──
        "PDF Author":             custodian["name"] if is_pdf else "",
        "PDF Creator":            random.choice(["Microsoft Word","Adobe Acrobat","Nuance PDF"]) if is_pdf else "",
        "PDF Producer":           "Adobe PDF Library" if is_pdf else "",
        "PDF Page Count":         pages if is_pdf else "",
        "Is Encrypted":           "No",
        "Is Form":                random.choice(["Yes","No","No","No"]) if is_pdf else "",
        # ── RSMF fields ──
        "Rsmf/Application":       rsmf_app,
        "Rsmf/Participants":      rsmf_participants,
        "Rsmf/MessageCount":      rsmf_msgs,
        "Rsmf/BeginDate":         rsmf_begin,
        "Rsmf/EndDate":           rsmf_end,
        "Rsmf/EventCollectionId": rsmf_evt,
        "Rsmf/HasPlaceholders":   rsmf_has_placeholders,
        # ── Image / EXIF fields ──
        "Camera Make":            camera_make,
        "Camera Model":           camera_model,
        "Date Taken":             date_taken,
        "GPS Latitude":           gps_lat,
        "GPS Longitude":          gps_lon,
        "GPS Altitude":           gps_alt,
        # ── Google Workspace fields ──
        "GoogleDrive/DocID":         google_doc_id,
        "GoogleDrive/DocumentType":  google_doc_type,
        "GoogleDrive/SharedDriveID": google_shared_drive,
        "GoogleDrive/SourceHash":    google_source_hash,
    }


def generate(tier_name, out_dir, seed):
    random.seed(seed)
    wf     = WORKFLOW[tier_name]
    custs  = CUSTODIANS[tier_name]
    dr     = DATE_RANGES[tier_name]
    counts = TIER_FILE_COUNTS[tier_name]

    print(f"\n{'='*60}\n  Generating: {tier_name.upper()} tier\n  Output: {out_dir}\n{'='*60}")

    # ── Build full document list by file type ──
    all_docs = []
    doc_num  = 0
    for ft_name, count in counts.items():
        ft_meta = FILE_TYPES[ft_name]
        for _ in range(count):
            doc_num += 1
            cust = random.choice(custs)
            d = make_doc(f"DOC-{doc_num:07d}", cust, ft_name, ft_meta, dr, custs, None, wf)
            all_docs.append(d)

    random.shuffle(all_docs)
    total = len(all_docs)
    print(f"  Total documents: {total:,}")

    # ── Assign workflow stages ──
    n_dup      = int(total * wf["dup_nist_pct"])
    n_err      = int(total * wf["processing_error_pct"])
    n_eca      = int(total * wf["eca_excluded_pct"])
    n_review   = total - n_dup - n_err - n_eca
    n_reviewed = int(n_review * wf["reviewed_pct"])
    n_inprog   = int(n_review * wf["inprogress_pct"])

    for i, d in enumerate(all_docs):
        if i < n_dup:
            d["Workflow Stage"] = "Pre-Review: Duplicate/NIST"
            d["Cull Reason"]    = random.choice(CULL_REASONS)
            d["Duplicate Spare"] = "Yes"
        elif i < n_dup + n_err:
            d["Workflow Stage"]       = "Pre-Review: Processing Error"
            d["Processing Status"]    = "Error"
            d["Processing Error Type"] = d["Processing Error Type"] or random.choice(PROC_ERRORS)
        elif i < n_dup + n_err + n_eca:
            d["Workflow Stage"]      = "ECA: Excluded"
            d["ECA Exclusion Reason"] = random.choice(ECA_REASONS)
        elif i < n_dup + n_err + n_eca + n_reviewed:
            d["Workflow Stage"] = "Review: Reviewed"
        elif i < n_dup + n_err + n_eca + n_reviewed + n_inprog:
            d["Workflow Stage"] = "Review: In Progress"
        else:
            d["Workflow Stage"] = "Review: Queued"

    # ── Responsiveness, privilege, TAR ──
    reviewed = [d for d in all_docs if d["Workflow Stage"] == "Review: Reviewed"]
    random.shuffle(reviewed)
    n_resp   = int(len(reviewed) * wf["responsive_pct"])
    n_nonresp = int(len(reviewed) * wf["nonresponsive_pct"])

    resp_docs    = reviewed[:n_resp]
    nonresp_docs = reviewed[n_resp:n_resp + n_nonresp]
    notsure_docs = reviewed[n_resp + n_nonresp:]

    for d in resp_docs:    d["Responsiveness"] = "Responsive"
    for d in nonresp_docs: d["Responsiveness"] = "Non-Responsive"
    for d in notsure_docs: d["Responsiveness"] = "Not Sure"

    n_priv  = int(n_resp * wf["privilege_pct"])
    priv_docs = resp_docs[:n_priv]
    prod_docs = resp_docs[n_priv:]

    for d in priv_docs:
        d["Privilege"]        = "Privileged"
        d["Privilege Reason"] = random.choice(PRIVILEGE_REASONS)

    n_hot = int(n_resp * wf["hot_pct"])
    for d in random.sample(resp_docs, min(n_hot, len(resp_docs))):
        d["Hot Doc"]    = "Yes"
        d["Issue Tags"] = random.choice(ISSUE_TAGS)

    # TAR scores — full review population (Rule 7: bimodal)
    for d in reviewed:
        score = tar_score()
        d["TAR Score"]            = score
        d["AL Predicted Relevant"] = "Yes" if score >= 50 else "No"

    # Bates + production
    bates_n = [1]
    n_redacted = int(len(prod_docs) * wf["redacted_pct"])
    redacted_sample = set(id(d) for d in random.sample(prod_docs, min(n_redacted, len(prod_docs))))
    for d in prod_docs:
        begin = f"{wf['bates_prefix']}{bates_n[0]:08d}"
        end   = f"{wf['bates_prefix']}{bates_n[0] + int(d['Page Count']) - 1:08d}"
        bates_n[0] += int(d["Page Count"])
        d["Bates Begin"]    = begin
        d["Bates End"]      = end
        d["Production Set"] = f"VOL{random.randint(1, wf['productions']):03d}"
        if id(d) in redacted_sample:
            d["Redacted"]        = "Yes"
            d["Redaction Reason"] = random.choice(["PII - Patient Information", "Privilege - Partial", "Privacy - Third Party"])

    # ── Email families (Rule 9) ──
    email_docs = [d for d in all_docs if d["File Type Category"] in ("Email - MSG", "Email - EML")]
    print(f"  Building email families ({len(email_docs):,} emails)...")
    families = []
    fam_id = thr_id = 0
    n_standalone = int(len(email_docs) * 0.22)
    random.shuffle(email_docs)
    standalone = email_docs[:n_standalone]
    threaded   = email_docs[n_standalone:]

    for d in standalone:
        fam_id += 1
        fk = f"FAM-{fam_id:06d}"
        d["Family ID"] = fk
        d["Email Thread ID"] = ""
        d["Email Threading Inclusive"] = "Yes"
        families.append({"family_id": fk, "thread_id": None, "parent_doc_id": d["Control Number"],
                         "children": [], "subject": d["Email Subject"], "family_size": 1})

    i = 0
    while i < len(threaded):
        fam_id += 1; thr_id += 1
        sz    = random.choices([2,3,4,5,6,8], weights=[20,25,20,15,10,10])[0]
        group = threaded[i:i+sz]; i += sz
        fk = f"FAM-{fam_id:06d}"; tk = f"THR-{thr_id:06d}"
        parent = group[0]
        inclusive_idx = random.randint(max(0, len(group)-2), len(group)-1)
        for j, d in enumerate(group):
            d["Family ID"]               = fk
            d["Email Thread ID"]         = tk
            d["Parent Document ID"]      = "" if j == 0 else parent["Control Number"]
            d["Email Threading Inclusive"] = "Yes" if j == inclusive_idx else "No"
            if j > 0:
                d["In Reply To"]    = parent["Message ID"]
                d["Email Subject"]  = "RE: " + parent["Email Subject"].lstrip("RE: ").lstrip("FW: ")
        families.append({"family_id": fk, "thread_id": tk, "parent_doc_id": parent["Control Number"],
                         "children": [d["Control Number"] for d in group[1:]],
                         "subject": parent["Email Subject"], "family_size": len(group)})

    # ── Batches ──
    batch_sets = {
        "small":  [("First Pass Review", 0.85), ("QC Review", 0.15)],
        "medium": [("First Pass Review", 0.70), ("Privilege Review", 0.15), ("QC Review", 0.10), ("Hot Docs", 0.05)],
        "large":  [("First Pass Review", 0.60), ("Privilege Review", 0.15), ("QC Review", 0.12), ("Hot Docs", 0.05), ("Second Pass", 0.05), ("Clawback Review", 0.03)],
    }[tier_name]

    reviewer_pool = {
        "small":  ["Jordan Lee", "Sam Rivera", "Taylor Kim"],
        "medium": ["Jordan Lee", "Sam Rivera", "Taylor Kim", "Morgan Chen", "Alex Patel", "Casey Wu"],
        "large":  ["Jordan Lee", "Sam Rivera", "Taylor Kim", "Morgan Chen", "Alex Patel", "Casey Wu",
                   "Riley Zhao", "Devon Scott", "Avery Nguyen", "Quinn Torres", "Blake Fisher",
                   "Skylar Osei", "Jamie Brooks", "Reese Yamamoto", "Finley Grant"],
    }[tier_name]

    batches = []
    batch_id = 0
    rev_pool = reviewed[:]
    random.shuffle(rev_pool)
    cursor = 0
    bsz_min, bsz_max = (150,350) if tier_name=="small" else (200,500) if tier_name=="medium" else (300,800)

    for bset_name, pct in batch_sets:
        n_set  = int(len(rev_pool) * pct)
        bdocs  = rev_pool[cursor:cursor+n_set]; cursor += n_set
        j = 0
        while j < len(bdocs):
            batch_id += 1
            bsz     = random.randint(bsz_min, bsz_max)
            batch   = bdocs[j:j+bsz]; j += bsz
            rev     = random.choice(reviewer_pool)
            status  = random.choices(["Completed","In Progress","Not Started"], weights=[70,20,10])[0]
            adate   = random_date("2018-09-01", "2019-03-01")
            cdate   = adate + timedelta(days=random.randint(3,14)) if status=="Completed" else None
            bname   = f"{bset_name[:4].upper()}-{batch_id:04d}"
            for d in batch:
                d["Batch Name"] = bname; d["Batch Status"] = status
                d["Reviewer"]   = rev;   d["Date First Assigned"] = fmt_d(adate)
            batches.append({"batch_name": bname, "batch_set": bset_name, "status": status,
                            "reviewer": rev, "doc_count": len(batch),
                            "date_assigned": fmt_d(adate), "date_completed": fmt_d(cdate),
                            "document_ids": [d["Control Number"] for d in batch]})

    # ── Write outputs ──
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    docs_path = os.path.join(out_dir, "documents.csv")
    with open(docs_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_docs[0].keys()))
        writer.writeheader(); writer.writerows(all_docs)
    print(f"  Written {docs_path} ({os.path.getsize(docs_path)/1e6:.1f} MB, {len(all_docs):,} docs)")

    for fname, data in [("custodians.json", [{**c, "actual_doc_count": sum(1 for d in all_docs if d["Custodian"]==c["name"])} for c in custs]),
                        ("email-families.json", families),
                        ("batches.json", batches)]:
        path = os.path.join(out_dir, fname)
        with open(path, "w") as f: json.dump(data, f, indent=2)
        print(f"  Written {path}")

    print(f"\n  Done — {tier_name} tier written to {out_dir}")


def main():
    p = argparse.ArgumentParser(description="Generate OIDA Relativity mock metadata")
    p.add_argument("--tier",  required=True, choices=["small","medium","large"])
    p.add_argument("--out",   default=None)
    p.add_argument("--seed",  type=int, default=DEFAULT_SEED)
    args = p.parse_args()
    generate(args.tier, args.out or os.path.join("mock-data", args.tier), args.seed)

if __name__ == "__main__":
    main()
