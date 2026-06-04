#!/usr/bin/env python3
"""
generate_mock_metadata.py — OIDA Relativity Mock Data Generator

Generates realistic Relativity workspace metadata at three litigation scales,
using content patterns drawn from the Opioid Industry Documents Archive.

Outputs (written to mock-data/{tier}/):
  documents.csv        — one row per document, all Relativity fields populated
  custodians.json      — custodian profiles, hold status, doc counts
  email-families.json  — parent/child threading structure
  batches.json         — batch assignments and reviewer info

Usage:
  python scripts/generate_mock_metadata.py --tier small
  python scripts/generate_mock_metadata.py --tier medium
  python scripts/generate_mock_metadata.py --tier large
  python scripts/generate_mock_metadata.py --tier small --out ./my-output/
  python scripts/generate_mock_metadata.py --tier medium --seed 99
"""

import argparse
import csv
import hashlib
import json
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Reproducibility ────────────────────────────────────────────────────────
DEFAULT_SEED = 42

# ── Tier Configurations ────────────────────────────────────────────────────

TIERS = {
    "small": {
        "label": "Small Litigation (~1,500 docs)",
        "total_docs": 1500,
        "implied_collected": 9000,
        "date_start": "2013-01-01",
        "date_end": "2016-12-31",
        "collection_date": "2018-06-01",
        "bates_prefix": "MNK",
        "productions": 1,
        "workflow": {
            "dup_nist_pct":        0.10,
            "processing_error_pct": 0.06,
            "eca_excluded_pct":    0.33,
            "reviewed_pct":        0.80,
            "inprogress_pct":      0.12,
            "unreviewed_pct":      0.08,
            "responsive_pct":      0.30,
            "nonresponsive_pct":   0.63,
            "notsure_pct":         0.07,
            "privilege_pct":       0.12,
            "hot_pct":             0.02,
            "redacted_pct":        0.08,
        },
        "file_types": {
            "Email":                0.60,
            "Office - Word":        0.10,
            "Office - Excel":       0.05,
            "Office - PowerPoint":  0.03,
            "PDF":                  0.07,
            "Teams (RSMF)":         0.02,
            "Slack (RSMF)":         0.01,
            "Image":                0.02,
            "Other":                0.10,
        },
    },
    "medium": {
        "label": "Medium Litigation (~10,000 docs)",
        "total_docs": 10000,
        "implied_collected": 60000,
        "date_start": "2012-01-01",
        "date_end": "2017-12-31",
        "collection_date": "2018-06-01",
        "bates_prefix": "MNK",
        "productions": 2,
        "workflow": {
            "dup_nist_pct":        0.175,
            "processing_error_pct": 0.09,
            "eca_excluded_pct":    0.45,
            "reviewed_pct":        0.636,
            "inprogress_pct":      0.182,
            "unreviewed_pct":      0.091,
            "qc_pct":              0.091,
            "responsive_pct":      0.286,
            "nonresponsive_pct":   0.650,
            "notsure_pct":         0.064,
            "privilege_pct":       0.12,
            "hot_pct":             0.015,
            "redacted_pct":        0.07,
        },
        "file_types": {
            "Email":                0.57,
            "Office - Word":        0.10,
            "Office - Excel":       0.05,
            "Office - PowerPoint":  0.03,
            "PDF":                  0.06,
            "Teams (RSMF)":         0.04,
            "Slack (RSMF)":         0.02,
            "Image":                0.025,
            "Other":                0.065,
        },
    },
    "large": {
        "label": "Large Litigation (~150,000 docs)",
        "total_docs": 150000,
        "implied_collected": 1200000,
        "date_start": "2010-01-01",
        "date_end": "2018-06-30",
        "collection_date": "2018-08-01",
        "bates_prefix": "MNK",
        "productions": 4,
        "workflow": {
            "dup_nist_pct":        0.15,
            "processing_error_pct": 0.067,
            "eca_excluded_pct":    0.467,
            "reviewed_pct":        0.692,
            "inprogress_pct":      0.154,
            "unreviewed_pct":      0.154,
            "responsive_pct":      0.333,
            "nonresponsive_pct":   0.600,
            "notsure_pct":         0.067,
            "privilege_pct":       0.133,
            "hot_pct":             0.013,
            "redacted_pct":        0.10,
        },
        "file_types": {
            "Email":                0.50,
            "Office - Word":        0.10,
            "Office - Excel":       0.05,
            "Office - PowerPoint":  0.03,
            "PDF":                  0.07,
            "Teams (RSMF)":         0.06,
            "Slack (RSMF)":         0.04,
            "Image":                0.03,
            "SMS/iMessage (RSMF)":  0.01,
            "Other":                0.01,
        },
    },
}

# ── Custodian Definitions ──────────────────────────────────────────────────

CUSTODIANS = {
    "small": [
        {"id": "C001", "name": "Michael Brennan",  "email": "michael.brennan@mallinckrodt.com",  "role": "VP, Sales & Marketing",       "dept": "Sales",              "doc_target": 700,  "hold": "Acknowledged", "hold_date": "2018-06-15", "key": True},
        {"id": "C002", "name": "Sarah Chen",        "email": "sarah.chen@mallinckrodt.com",       "role": "Regional Sales Director",     "dept": "Sales",              "doc_target": 350,  "hold": "Acknowledged", "hold_date": "2018-06-18"},
        {"id": "C003", "name": "David Park",        "email": "david.park@mallinckrodt.com",       "role": "District Manager",            "dept": "Sales",              "doc_target": 300,  "hold": "Acknowledged", "hold_date": "2018-06-20"},
        {"id": "C004", "name": "Lisa Torres",       "email": "lisa.torres@mallinckrodt.com",      "role": "Executive Assistant",         "dept": "Administration",     "doc_target": 150,  "hold": "Acknowledged", "hold_date": "2018-07-02"},
    ],
    "medium": [
        {"id": "C001", "name": "James Whitfield",   "email": "james.whitfield@mallinckrodt.com",  "role": "Chief Executive Officer",     "dept": "Executive",          "doc_target": 1800, "hold": "Acknowledged", "hold_date": "2018-06-12", "key": True},
        {"id": "C002", "name": "Patricia Morrison", "email": "patricia.morrison@mallinckrodt.com","role": "VP, Marketing",               "dept": "Marketing",          "doc_target": 1500, "hold": "Acknowledged", "hold_date": "2018-06-12", "key": True},
        {"id": "C003", "name": "Robert Ashton",     "email": "robert.ashton@mallinckrodt.com",    "role": "VP, Sales",                   "dept": "Sales",              "doc_target": 1200, "hold": "Acknowledged", "hold_date": "2018-06-13", "key": True},
        {"id": "C004", "name": "Sandra Nguyen",     "email": "sandra.nguyen@mallinckrodt.com",    "role": "Regional Sales Director",     "dept": "Sales",              "doc_target": 700,  "hold": "Acknowledged", "hold_date": "2018-06-15"},
        {"id": "C005", "name": "Thomas Bradley",    "email": "thomas.bradley@mallinckrodt.com",   "role": "Compliance Officer",          "dept": "Legal & Compliance", "doc_target": 600,  "hold": "Acknowledged", "hold_date": "2018-06-15"},
        {"id": "C006", "name": "Michelle Park",     "email": "michelle.park@mallinckrodt.com",    "role": "Medical Affairs Director",    "dept": "Medical Affairs",    "doc_target": 500,  "hold": "Acknowledged", "hold_date": "2018-06-18"},
        {"id": "C007", "name": "Kevin O'Brien",     "email": "kevin.obrien@mallinckrodt.com",     "role": "District Manager",            "dept": "Sales",              "doc_target": 400,  "hold": "Acknowledged", "hold_date": "2018-06-20"},
        {"id": "C008", "name": "Rachel Stern",      "email": "rachel.stern@mallinckrodt.com",     "role": "Executive Assistant",         "dept": "Administration",     "doc_target": 150,  "hold": "Acknowledged", "hold_date": "2018-06-22"},
        {"id": "C009", "name": "Frank DeLuca",      "email": "frank.deluca@mallinckrodt.com",     "role": "IT Systems Administrator",   "dept": "IT",                 "doc_target": 100,  "hold": "Acknowledged", "hold_date": "2018-07-05"},
        {"id": "C010", "name": "Angela Washington", "email": "angela.washington@mallinckrodt.com","role": "Legal Coordinator",           "dept": "Legal",              "doc_target": 50,   "hold": "Outstanding",  "hold_date": None},
    ],
    "large": [
        {"id": "C001", "name": "James Whitfield",    "email": "james.whitfield@mallinckrodt.com",   "role": "Chief Executive Officer",          "dept": "Executive",           "doc_target": 12000, "hold": "Acknowledged", "hold_date": "2018-08-10", "key": True},
        {"id": "C002", "name": "Mark Trevino",       "email": "mark.trevino@mallinckrodt.com",      "role": "Chief Commercial Officer",         "dept": "Executive",           "doc_target": 10000, "hold": "Acknowledged", "hold_date": "2018-08-10", "key": True},
        {"id": "C003", "name": "Patricia Morrison",  "email": "patricia.morrison@mallinckrodt.com", "role": "VP, Marketing",                    "dept": "Marketing",           "doc_target": 8000,  "hold": "Acknowledged", "hold_date": "2018-08-11", "key": True},
        {"id": "C004", "name": "Robert Ashton",      "email": "robert.ashton@mallinckrodt.com",     "role": "VP, Sales",                        "dept": "Sales",               "doc_target": 7500,  "hold": "Acknowledged", "hold_date": "2018-08-11", "key": True},
        {"id": "C005", "name": "Diana Kowalski",     "email": "diana.kowalski@mallinckrodt.com",    "role": "VP, Regulatory Affairs",           "dept": "Regulatory",          "doc_target": 6000,  "hold": "Acknowledged", "hold_date": "2018-08-12", "key": True},
        {"id": "C006", "name": "Sandra Nguyen",      "email": "sandra.nguyen@mallinckrodt.com",     "role": "Regional Sales Director - East",   "dept": "Sales",               "doc_target": 4500,  "hold": "Acknowledged", "hold_date": "2018-08-14"},
        {"id": "C007", "name": "Thomas Bradley",     "email": "thomas.bradley@mallinckrodt.com",    "role": "Chief Compliance Officer",         "dept": "Legal & Compliance",  "doc_target": 4000,  "hold": "Acknowledged", "hold_date": "2018-08-14"},
        {"id": "C008", "name": "Michelle Park",      "email": "michelle.park@mallinckrodt.com",     "role": "Medical Affairs Director",         "dept": "Medical Affairs",     "doc_target": 3500,  "hold": "Acknowledged", "hold_date": "2018-08-15"},
        {"id": "C009", "name": "Kevin O'Brien",      "email": "kevin.obrien@mallinckrodt.com",      "role": "Regional Sales Director - West",   "dept": "Sales",               "doc_target": 3000,  "hold": "Acknowledged", "hold_date": "2018-08-15"},
        {"id": "C010", "name": "Laura Finnegan",     "email": "laura.finnegan@mallinckrodt.com",    "role": "Director, Government Affairs",     "dept": "Government Affairs",  "doc_target": 2800,  "hold": "Acknowledged", "hold_date": "2018-08-16"},
        {"id": "C011", "name": "Brian Holloway",     "email": "brian.holloway@mallinckrodt.com",    "role": "National Sales Manager",           "dept": "Sales",               "doc_target": 2500,  "hold": "Acknowledged", "hold_date": "2018-08-18"},
        {"id": "C012", "name": "Cynthia Rhodes",     "email": "cynthia.rhodes@mallinckrodt.com",    "role": "Director, Clinical Research",      "dept": "Medical Affairs",     "doc_target": 2200,  "hold": "Acknowledged", "hold_date": "2018-08-18"},
        {"id": "C013", "name": "Eric Sandoval",      "email": "eric.sandoval@mallinckrodt.com",     "role": "District Manager - Midwest",       "dept": "Sales",               "doc_target": 1800,  "hold": "Acknowledged", "hold_date": "2018-08-20"},
        {"id": "C014", "name": "Jennifer Watts",     "email": "jennifer.watts@mallinckrodt.com",    "role": "Senior Marketing Manager",         "dept": "Marketing",           "doc_target": 1600,  "hold": "Acknowledged", "hold_date": "2018-08-20"},
        {"id": "C015", "name": "Gregory Nash",       "email": "gregory.nash@mallinckrodt.com",      "role": "Director, SOM Compliance",         "dept": "Legal & Compliance",  "doc_target": 1400,  "hold": "Acknowledged", "hold_date": "2018-08-22"},
        {"id": "C016", "name": "Amanda Pierce",      "email": "amanda.pierce@mallinckrodt.com",     "role": "District Manager - Southeast",     "dept": "Sales",               "doc_target": 1200,  "hold": "Acknowledged", "hold_date": "2018-08-22"},
        {"id": "C017", "name": "Steven Calloway",    "email": "steven.calloway@mallinckrodt.com",   "role": "Sr. Medical Science Liaison",      "dept": "Medical Affairs",     "doc_target": 1000,  "hold": "Acknowledged", "hold_date": "2018-08-24"},
        {"id": "C018", "name": "Natalie Cruz",       "email": "natalie.cruz@mallinckrodt.com",      "role": "Marketing Manager - Branded",      "dept": "Marketing",           "doc_target": 900,   "hold": "Acknowledged", "hold_date": "2018-08-24"},
        {"id": "C019", "name": "Daniel Cho",         "email": "daniel.cho@mallinckrodt.com",        "role": "Regulatory Affairs Manager",       "dept": "Regulatory",          "doc_target": 800,   "hold": "Acknowledged", "hold_date": "2018-08-26"},
        {"id": "C020", "name": "Melissa Grant",      "email": "melissa.grant@mallinckrodt.com",     "role": "Associate General Counsel",        "dept": "Legal",               "doc_target": 700,   "hold": "Acknowledged", "hold_date": "2018-08-26"},
        {"id": "C021", "name": "Paul Whitmore",      "email": "paul.whitmore@mallinckrodt.com",     "role": "District Manager - Southwest",     "dept": "Sales",               "doc_target": 600,   "hold": "Acknowledged", "hold_date": "2018-08-28"},
        {"id": "C022", "name": "Rachel Stern",       "email": "rachel.stern@mallinckrodt.com",      "role": "Executive Assistant - CCO",        "dept": "Administration",      "doc_target": 500,   "hold": "Acknowledged", "hold_date": "2018-08-28"},
        {"id": "C023", "name": "Carlos Ibarra",      "email": "carlos.ibarra@mallinckrodt.com",     "role": "Inside Sales Representative",      "dept": "Sales",               "doc_target": 400,   "hold": "Acknowledged", "hold_date": "2018-09-02"},
        {"id": "C024", "name": "Heather Bloom",      "email": "heather.bloom@mallinckrodt.com",     "role": "Clinical Educator",                "dept": "Medical Affairs",     "doc_target": 350,   "hold": "Acknowledged", "hold_date": "2018-09-02"},
        {"id": "C025", "name": "Timothy Marsh",      "email": "timothy.marsh@mallinckrodt.com",     "role": "Trade Relations Manager",          "dept": "Sales",               "doc_target": 300,   "hold": "Acknowledged", "hold_date": "2018-09-05"},
        {"id": "C026", "name": "Donna Callahan",     "email": "donna.callahan@mallinckrodt.com",    "role": "Sales Operations Analyst",         "dept": "Sales",               "doc_target": 250,   "hold": "Acknowledged", "hold_date": "2018-09-05"},
        {"id": "C027", "name": "Frank DeLuca",       "email": "frank.deluca@mallinckrodt.com",      "role": "IT Systems Administrator",         "dept": "IT",                  "doc_target": 200,   "hold": "Acknowledged", "hold_date": "2018-09-10"},
        {"id": "C028", "name": "Sarah Patel",        "email": "sarah.patel@mallinckrodt.com",       "role": "HR Business Partner",              "dept": "Human Resources",     "doc_target": 180,   "hold": "Acknowledged", "hold_date": "2018-09-10"},
        {"id": "C029", "name": "Walter Kim",         "email": "walter.kim@mallinckrodt.com",        "role": "Finance Manager",                  "dept": "Finance",             "doc_target": 150,   "hold": "Escalated",    "hold_date": "2018-09-12"},
        {"id": "C030", "name": "Nicole Russo",       "email": "nicole.russo@mallinckrodt.com",      "role": "Senior Paralegal",                 "dept": "Legal",               "doc_target": 130,   "hold": "Acknowledged", "hold_date": "2018-09-15"},
        {"id": "C031", "name": "Andrew Flynn",       "email": "andrew.flynn@mallinckrodt.com",      "role": "Quality Assurance Specialist",     "dept": "Quality",             "doc_target": 110,   "hold": "Acknowledged", "hold_date": "2018-09-15"},
        {"id": "C032", "name": "Tiffany Bell",       "email": "tiffany.bell@mallinckrodt.com",      "role": "Administrative Coordinator",       "dept": "Administration",      "doc_target": 100,   "hold": "Acknowledged", "hold_date": "2018-09-18"},
        {"id": "C033", "name": "Marcus Webb",        "email": "marcus.webb@mallinckrodt.com",       "role": "Government Pricing Analyst",       "dept": "Finance",             "doc_target": 90,    "hold": "Acknowledged", "hold_date": "2018-09-18"},
        {"id": "C034", "name": "Irene Hoffman",      "email": "irene.hoffman@mallinckrodt.com",     "role": "Contracts Manager",                "dept": "Legal",               "doc_target": 80,    "hold": "Acknowledged", "hold_date": "2018-09-20"},
        {"id": "C035", "name": "Owen Garrett",       "email": "owen.garrett@mallinckrodt.com",      "role": "Lab Technician",                   "dept": "R&D",                 "doc_target": 70,    "hold": "Acknowledged", "hold_date": "2018-09-20"},
        {"id": "C036", "name": "Priya Mehta",        "email": "priya.mehta@mallinckrodt.com",       "role": "Business Intelligence Analyst",    "dept": "Sales",               "doc_target": 60,    "hold": "Acknowledged", "hold_date": "2018-09-22"},
        {"id": "C037", "name": "Jason Dunn",         "email": "jason.dunn@mallinckrodt.com",        "role": "Warehouse Supervisor",             "dept": "Operations",          "doc_target": 50,    "hold": "Acknowledged", "hold_date": "2018-09-25"},
        {"id": "C038", "name": "Claire Simmons",     "email": "claire.simmons@mallinckrodt.com",    "role": "Receptionist",                     "dept": "Administration",      "doc_target": 40,    "hold": "Outstanding",  "hold_date": None},
        {"id": "C039", "name": "Victor Okafor",      "email": "victor.okafor@mallinckrodt.com",     "role": "Supply Chain Analyst",             "dept": "Operations",          "doc_target": 30,    "hold": "Outstanding",  "hold_date": None},
        {"id": "C040", "name": "Angela Washington",  "email": "angela.washington@mallinckrodt.com", "role": "Legal Coordinator",                "dept": "Legal",               "doc_target": 20,    "hold": "Outstanding",  "hold_date": None},
    ],
}

# ── Content Seeds (OIDA-informed) ──────────────────────────────────────────

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
    "RE: Speaker Program Audit Results",
    "Key Account Update - {account}",
    "RE: Clinical Data Request - {product}",
    "FW: IMS Data - {month} {year}",
    "RE: New Hire Onboarding - Sales",
    "Territory Business Plan - {year}",
    "RE: {product} Patient Assistance Program",
    "FW: Legal Hold Notice",
    "RE: Managed Markets Update - Q{q}",
    "REMS Program Update - {product}",
    "RE: Sales Incentive Compensation - {quarter}",
]

PRODUCTS      = ["OxyContin", "Exalgo", "Pennsaid", "Subsys", "Duexis", "Xartemis XR", "Sumavel", "Opana ER"]
TERRITORIES   = ["Northeast", "Southeast", "Midwest", "Southwest", "Northwest", "Mid-Atlantic", "Gulf Coast", "Great Lakes"]
ACCOUNTS      = ["Walgreens", "CVS Health", "Cardinal Health", "McKesson", "AmerisourceBergen", "Express Scripts", "OptumRx"]
MONTHS        = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
QUARTERS      = ["Q1 2014", "Q2 2014", "Q3 2014", "Q4 2014", "Q1 2015", "Q2 2015", "Q3 2015", "Q4 2015", "Q1 2016", "Q2 2016"]

OFFICE_TITLES = [
    "{product} Sales Training Module {n}",
    "Territory Business Plan {year} - {territory}",
    "Speaker Bureau Program Guidelines",
    "Q{q} {year} Marketing Deck",
    "SOM Policy and Procedure Manual",
    "Key Account Strategy - {account}",
    "{product} Market Analysis",
    "DEA Compliance Training Slides",
    "Managed Care Coverage Grid",
    "Annual Incentive Compensation Plan",
    "Medical Affairs Engagement Protocol",
    "Distribution Channel Review",
    "Customer Segmentation Analysis",
    "Product Launch Readiness Checklist",
    "Regulatory Submission Summary",
]

PRIVILEGE_REASONS = [
    "Attorney-Client Communication",
    "Work Product - Litigation Preparation",
    "Attorney-Client - Outside Counsel",
    "Work Product - Regulatory Response",
    "Attorney-Client - In-House Counsel",
]

ECA_EXCLUSION_REASONS = [
    "Date Out of Range",
    "Domain Excluded - Opposing Counsel",
    "No Keyword Hits",
    "File Type Excluded",
    "Domain Excluded - Personal",
    "System File",
    "Duplicate of Collected",
]

PROCESSING_ERROR_TYPES = [
    "Password Protected",
    "Corrupt File",
    "Unsupported File Type",
    "Extraction Failure",
    "OCR Failure - Poor Scan Quality",
    "Container Extraction Timeout",
    "Teams Conversion Error",
]

CULL_REASONS = [
    "NIST System File",
    "Exact Duplicate",
    "Near Duplicate",
    "Below De Minimis",
]

ISSUE_TAGS = [
    "Marketing Practices",
    "DEA Reporting",
    "Speaker Bureau",
    "Sales Incentives",
    "FDA Communications",
    "Suspicious Orders",
    "REMS Compliance",
    "Pricing",
    "Key Custodian Communication",
]

RSMF_CHANNEL_NAMES = [
    "sales-northeast-team", "compliance-updates", "marketing-general",
    "speaker-bureau-ops", "som-alerts", "legal-hold-notices",
    "product-launch-exalgo", "managed-care-wins", "district-managers",
    "executive-leadership", "medical-affairs", "regulatory-team",
]

EXTERNAL_CONTACTS = [
    ("Dr. Alan Foster", "alan.foster@painspecialists.com"),
    ("Dr. Maria Santos", "msantos@regionalhospital.org"),
    ("Karen Harper", "karen.harper@covidien.com"),
    ("Dan Winkelman", "dan.winkelman@biomednews.com"),
    ("DEA Diversion", "diversion@dea.gov"),
    ("FDA CDER", "cder@fda.hhs.gov"),
    ("Bradley Tevelow", "bradley.tevelow@mckinsey.com"),
    ("Laura Moran", "laura.moran@mckinsey.com"),
    ("Dr. Susan Ellis", "sellis@painclinic.net"),
    ("State AG Office", "inquiry@ag.state.us"),
]

FILE_TYPE_META = {
    "Email": {
        "extensions": ["msg", "eml"],
        "size_range": (15_000, 250_000),
        "has_natives": "Yes",
        "has_images": "No",
        "mime": "message/rfc822",
    },
    "Office - Word": {
        "extensions": ["docx", "doc"],
        "size_range": (25_000, 800_000),
        "has_natives": "Yes",
        "has_images": "No",
        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    "Office - Excel": {
        "extensions": ["xlsx", "xls"],
        "size_range": (20_000, 2_000_000),
        "has_natives": "Yes",
        "has_images": "No",
        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    },
    "Office - PowerPoint": {
        "extensions": ["pptx", "ppt"],
        "size_range": (100_000, 5_000_000),
        "has_natives": "Yes",
        "has_images": "Yes",
        "mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
    "PDF": {
        "extensions": ["pdf"],
        "size_range": (50_000, 3_000_000),
        "has_natives": "Yes",
        "has_images": "Yes",
        "mime": "application/pdf",
    },
    "Teams (RSMF)": {
        "extensions": ["rsmf"],
        "size_range": (10_000, 500_000),
        "has_natives": "Yes",
        "has_images": "No",
        "mime": "application/rsmf",
    },
    "Slack (RSMF)": {
        "extensions": ["rsmf"],
        "size_range": (8_000, 300_000),
        "has_natives": "Yes",
        "has_images": "No",
        "mime": "application/rsmf",
    },
    "SMS/iMessage (RSMF)": {
        "extensions": ["rsmf"],
        "size_range": (2_000, 50_000),
        "has_natives": "Yes",
        "has_images": "No",
        "mime": "application/rsmf",
    },
    "Image": {
        "extensions": ["jpg", "png", "tif", "heic"],
        "size_range": (200_000, 8_000_000),
        "has_natives": "Yes",
        "has_images": "Yes",
        "mime": "image/jpeg",
    },
    "Other": {
        "extensions": ["txt", "csv", "zip", "xml"],
        "size_range": (1_000, 500_000),
        "has_natives": "Yes",
        "has_images": "No",
        "mime": "text/plain",
    },
}

# ── Helpers ────────────────────────────────────────────────────────────────

def fake_md5():
    return "%032x" % random.getrandbits(128)

def fake_sha256():
    return "%064x" % random.getrandbits(256)

def fake_message_id():
    domain = random.choice(["mallinckrodt.com", "outlook.com", "mckinsey.com"])
    return "<%s.%s@%s>" % (fake_md5()[:16], fake_md5()[:8], domain)

def random_date(start_str, end_str):
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end   = datetime.strptime(end_str,   "%Y-%m-%d")
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def fmt_date(dt):
    return dt.strftime("%Y-%m-%d") if dt else ""

def fmt_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""

def tar_score():
    band = random.random()
    if band < 0.40:
        return round(random.uniform(0, 20), 2)
    elif band < 0.75:
        return round(random.uniform(75, 100), 2)
    else:
        return round(random.uniform(20, 75), 2)

def expand_subject(template, year_range):
    year = random.randint(int(year_range[0][:4]), int(year_range[1][:4]))
    return (template
            .replace("{q}", str(random.randint(1, 4)))
            .replace("{year}", str(year))
            .replace("{month}", random.choice(MONTHS))
            .replace("{quarter}", random.choice(QUARTERS))
            .replace("{territory}", random.choice(TERRITORIES))
            .replace("{product}", random.choice(PRODUCTS))
            .replace("{account}", random.choice(ACCOUNTS))
            .replace("{n}", str(random.randint(1, 8))))

def expand_title(template, year_range):
    return expand_subject(template, year_range)

def weighted_choice(choices):
    keys   = list(choices.keys())
    weights = list(choices.values())
    return random.choices(keys, weights=weights, k=1)[0]

def assign_custodians(custodians, total_docs):
    targets  = [c["doc_target"] for c in custodians]
    total_t  = sum(targets)
    assigned = [0] * len(custodians)
    docs     = list(range(total_docs))
    random.shuffle(docs)
    cursor = 0
    for i, c in enumerate(custodians):
        n = round(c["doc_target"] / total_t * total_docs)
        assigned[i] = n
        cursor += n
    diff = total_docs - sum(assigned)
    assigned[0] += diff
    result = []
    for i, c in enumerate(custodians):
        result.extend([c] * assigned[i])
    random.shuffle(result)
    return result

def build_email_families(email_docs, date_start, date_end):
    families = []
    threads  = {}
    fam_id   = 0
    thr_id   = 0

    standalone_pct = 0.22
    n_standalone   = int(len(email_docs) * standalone_pct)
    n_threaded     = len(email_docs) - n_standalone

    pool = email_docs[:]
    random.shuffle(pool)

    standalone = pool[:n_standalone]
    threaded   = pool[n_standalone:]

    for doc in standalone:
        fam_id += 1
        families.append({
            "family_id":       f"FAM-{fam_id:06d}",
            "thread_id":       None,
            "parent_doc_id":   doc["Control Number"],
            "children":        [],
            "subject":         doc.get("Email Subject", ""),
            "family_size":     1,
            "is_thread_inclusive": True,
        })
        doc["Family ID"]      = f"FAM-{fam_id:06d}"
        doc["Email Thread ID"] = ""
        doc["Parent Document ID"] = ""

    i = 0
    while i < len(threaded):
        thr_id += 1
        fam_id += 1
        family_size  = random.choices([2, 3, 4, 5, 6, 8], weights=[20, 25, 20, 15, 10, 10])[0]
        family_size  = min(family_size, len(threaded) - i)
        family_docs  = threaded[i:i + family_size]
        parent       = family_docs[0]
        children     = family_docs[1:]
        i           += family_size

        fam_key  = f"FAM-{fam_id:06d}"
        thr_key  = f"THR-{thr_id:06d}"
        subject  = parent.get("Email Subject", "")
        inclusive_idx = random.randint(max(0, len(family_docs) - 2), len(family_docs) - 1)

        family_entry = {
            "family_id":           fam_key,
            "thread_id":           thr_key,
            "parent_doc_id":       parent["Control Number"],
            "children":            [d["Control Number"] for d in children],
            "subject":             subject,
            "family_size":         family_size,
            "is_thread_inclusive": True,
        }
        families.append(family_entry)

        for j, doc in enumerate(family_docs):
            doc["Family ID"]               = fam_key
            doc["Email Thread ID"]         = thr_key
            doc["Parent Document ID"]      = "" if j == 0 else parent["Control Number"]
            doc["Email Threading Inclusive"] = "Yes" if j == inclusive_idx else "No"
            if j > 0:
                doc["In Reply To"] = parent.get("Message ID", "")
                doc["Email Subject"] = "RE: " + subject.lstrip("RE: ").lstrip("FW: ")

    return families

def build_batches(reviewed_docs, tier, reviewers):
    batches   = []
    batch_id  = 0
    batch_sets = {
        "small":  [("First Pass Review", 0.85), ("QC Review", 0.15)],
        "medium": [("First Pass Review", 0.70), ("Privilege Review", 0.15), ("QC Review", 0.10), ("Hot Docs", 0.05)],
        "large":  [("First Pass Review", 0.60), ("Privilege Review", 0.15), ("QC Review", 0.12), ("Hot Docs", 0.05), ("Clawback Review", 0.03), ("Second Pass", 0.05)],
    }

    pool = reviewed_docs[:]
    random.shuffle(pool)
    cursor = 0
    for batch_set_name, pct in batch_sets[tier]:
        n_set = int(len(pool) * pct)
        set_docs = pool[cursor:cursor + n_set]
        cursor  += n_set
        batch_size_min, batch_size_max = (150, 350) if tier == "small" else (200, 500) if tier == "medium" else (300, 800)
        j = 0
        while j < len(set_docs):
            batch_id += 1
            size  = random.randint(batch_size_min, batch_size_max)
            bdocs = set_docs[j:j + size]
            j    += size
            reviewer = random.choice(reviewers)
            status   = random.choices(["Completed", "In Progress", "Not Started"], weights=[70, 20, 10])[0]
            assigned_date = random_date("2018-09-01", "2019-03-01")
            completed_date = (assigned_date + timedelta(days=random.randint(3, 14))) if status == "Completed" else None
            batch_name = f"{batch_set_name[:4].upper()}-{batch_id:04d}"

            batches.append({
                "batch_name":       batch_name,
                "batch_set":        batch_set_name,
                "status":           status,
                "reviewer":         reviewer,
                "doc_count":        len(bdocs),
                "date_assigned":    fmt_date(assigned_date),
                "date_completed":   fmt_date(completed_date),
                "document_ids":     [d["Control Number"] for d in bdocs],
            })
            for doc in bdocs:
                doc["Batch Name"]   = batch_name
                doc["Batch Status"] = status
                doc["Reviewer"]     = reviewer
                doc["Date First Assigned"] = fmt_date(assigned_date)

    return batches

# ── Main Generator ─────────────────────────────────────────────────────────

def generate(tier_name, out_dir, seed):
    random.seed(seed)
    cfg  = TIERS[tier_name]
    wf   = cfg["workflow"]
    custs = CUSTODIANS[tier_name]
    total = cfg["total_docs"]

    print(f"\n{'='*60}")
    print(f"  Generating: {cfg['label']}")
    print(f"  Output:     {out_dir}")
    print(f"  Seed:       {seed}")
    print(f"{'='*60}")

    # ── Stage counts ──
    n_dup          = int(total * wf["dup_nist_pct"])
    n_proc_err     = int(total * wf["processing_error_pct"])
    n_eca          = int(total * wf["eca_excluded_pct"])
    n_review       = total - n_dup - n_proc_err - n_eca

    n_reviewed     = int(n_review * wf["reviewed_pct"])
    n_inprogress   = int(n_review * wf["inprogress_pct"])
    n_unreviewed   = n_review - n_reviewed - n_inprogress

    n_responsive   = int(n_reviewed * wf["responsive_pct"])
    n_nonresp      = int(n_reviewed * wf["nonresponsive_pct"])
    n_notsure      = n_reviewed - n_responsive - n_nonresp

    n_privilege    = int(n_responsive * wf["privilege_pct"])
    n_hot          = int(n_responsive * wf["hot_pct"])
    n_produced     = n_responsive - n_privilege
    n_redacted     = int(n_produced * wf["redacted_pct"])

    print(f"\n  Workflow breakdown:")
    print(f"    Duplicates/NIST:      {n_dup:,}")
    print(f"    Processing errors:    {n_proc_err:,}")
    print(f"    ECA excluded:         {n_eca:,}")
    print(f"    Sent to review:       {n_review:,}")
    print(f"      Reviewed:           {n_reviewed:,}")
    print(f"        Responsive:       {n_responsive:,}")
    print(f"          Privileged:     {n_privilege:,}")
    print(f"          Produced:       {n_produced:,}")
    print(f"          Redacted:       {n_redacted:,}")

    # ── Assign custodians ──
    custodian_pool = assign_custodians(custs, total)

    # ── Reviewers ──
    reviewer_pool = {
        "small":  ["Jordan Lee", "Sam Rivera", "Taylor Kim"],
        "medium": ["Jordan Lee", "Sam Rivera", "Taylor Kim", "Morgan Chen", "Alex Patel", "Casey Wu"],
        "large":  ["Jordan Lee", "Sam Rivera", "Taylor Kim", "Morgan Chen", "Alex Patel",
                   "Casey Wu", "Riley Zhao", "Devon Scott", "Avery Nguyen", "Quinn Torres",
                   "Blake Fisher", "Skylar Osei", "Jamie Brooks", "Reese Yamamoto", "Finley Grant"],
    }[tier_name]

    # ── Bates counter ──
    bates_counter = [1]
    def next_bates(pages=1):
        begin  = f"{cfg['bates_prefix']}{bates_counter[0]:08d}"
        end    = f"{cfg['bates_prefix']}{bates_counter[0] + pages - 1:08d}"
        bates_counter[0] += pages
        return begin, end

    # ── Generate all documents ──
    docs = []
    doc_num = 0

    def new_doc(custodian, file_type, workflow_stage):
        nonlocal doc_num
        doc_num += 1
        ctrl    = f"DOC-{doc_num:07d}"
        meta    = FILE_TYPE_META.get(file_type, FILE_TYPE_META["Other"])
        ext     = random.choice(meta["extensions"])
        size    = random.randint(*meta["size_range"])
        date    = random_date(cfg["date_start"], cfg["date_end"])
        pages   = random.randint(1, 30) if file_type in ("PDF", "Office - Word", "Office - PowerPoint") else random.randint(1, 5)

        subject = expand_subject(random.choice(EMAIL_SUBJECTS), (cfg["date_start"], cfg["date_end"]))
        title   = expand_title(random.choice(OFFICE_TITLES),    (cfg["date_start"], cfg["date_end"]))

        # email-specific
        is_email = file_type == "Email"
        is_rsmf  = "RSMF" in file_type
        is_office_doc = file_type.startswith("Office")
        is_pdf   = file_type == "PDF"

        from_person = custodian
        to_person   = random.choice(custs + list({"name": n, "email": e} for n, e in EXTERNAL_CONTACTS))
        if isinstance(to_person, tuple):
            to_name, to_email = to_person
        else:
            to_name  = to_person.get("name", "")
            to_email = to_person.get("email", "")

        msg_id = fake_message_id() if is_email else ""

        # RSMF
        rsmf_app   = ""
        rsmf_parts = ""
        rsmf_msgs  = 0
        rsmf_begin = ""
        rsmf_end   = ""
        rsmf_evt   = ""
        if is_rsmf:
            rsmf_app   = file_type.split(" ")[0]
            participants = [custodian["name"]] + [c["name"] for c in random.sample(custs, min(3, len(custs)))]
            rsmf_parts = "; ".join(set(participants))
            rsmf_msgs  = random.randint(5, 120)
            rsmf_begin = fmt_datetime(date)
            rsmf_end   = fmt_datetime(date + timedelta(hours=random.randint(1, 48)))
            rsmf_evt   = fake_md5()[:16]

        return {
            # ── Universal ──
            "Control Number":        ctrl,
            "File Name":             f"{ctrl}.{ext}" if not is_email else f"{subject[:40].replace('/', '-')}.{ext}",
            "File Extension":        ext,
            "File Type Category":    file_type,
            "File Size (bytes)":     size,
            "MD5 Hash":              fake_md5(),
            "SHA256 Hash":           fake_sha256(),
            "Custodian":             custodian["name"],
            "Custodian Email":       custodian["email"],
            "Custodian Department":  custodian.get("dept", ""),
            "Processing Folder Path": f"\\\\Collection\\{custodian['name'].replace(' ', '_')}\\{date.year}\\{date.strftime('%m')}",
            "Virtual Path":          f"{custodian['name'].replace(' ', '_')}\\{file_type}\\{ctrl}.{ext}",
            "Container ID":          "",
            "Container Name":        "",
            "Level":                 "1",
            "Primary Date":          fmt_datetime(date),
            "Sort Date":             fmt_datetime(date),
            "Language":              "English",
            "Has Images":            meta["has_images"],
            "Has Natives":           meta["has_natives"],
            "OCR Flag":              "Yes" if is_pdf else "No",
            "Extracted Text Preview": f"[{file_type}] {subject if is_email else title} — from {custodian['name']} on {fmt_date(date)}",
            # ── Workflow ──
            "Workflow Stage":        workflow_stage,
            "Cull Reason":           "",
            "Processing Status":     "Complete",
            "Processing Error Type": "",
            "Duplicate Spare":       "No",
            "ECA Exclusion Reason":  "",
            "Batch Name":            "",
            "Batch Status":          "",
            "Reviewer":              "",
            "Date First Assigned":   "",
            "Responsiveness":        "",
            "Privilege":             "",
            "Privilege Reason":      "",
            "Hot Doc":               "No",
            "Issue Tags":            "",
            "Bates Begin":           "",
            "Bates End":             "",
            "Page Count":            pages,
            "Production Set":        "",
            "Redacted":              "No",
            "Redaction Reason":      "",
            "TAR Score":             "",
            "AL Predicted Relevant": "",
            # ── Email ──
            "Email From":            custodian["name"] if is_email else "",
            "Email From SMTP":       custodian["email"] if is_email else "",
            "Email To":              to_name if is_email else "",
            "Email To SMTP":         to_email if is_email else "",
            "Email CC":              "",
            "Email CC SMTP":         "",
            "Email BCC":             "",
            "Email BCC SMTP":        "",
            "Email Subject":         subject if is_email else "",
            "Message ID":            msg_id,
            "In Reply To":           "",
            "Date Sent":             fmt_datetime(date) if is_email else "",
            "Date Received":         fmt_datetime(date + timedelta(minutes=random.randint(1, 30))) if is_email else "",
            "Conversation Topic":    subject if is_email else "",
            "Conversation Index":    fake_md5()[:32] if is_email else "",
            "Has Attachments":       "Yes" if is_email and random.random() < 0.35 else "No",
            "Attachment Count":      random.randint(1, 4) if is_email and random.random() < 0.35 else 0,
            "Attachment Names":      "",
            "Email Thread ID":       "",
            "Email Threading Inclusive": "",
            "Importance":            random.choice(["Normal", "Normal", "Normal", "High", "Low"]) if is_email else "",
            "Parent Document ID":    "",
            "Family ID":             "",
            # ── Office ──
            "Author":                custodian["name"] if is_office_doc else "",
            "Last Modified By":      custodian["name"] if is_office_doc else "",
            "Date Created":          fmt_date(date) if is_office_doc else "",
            "Date Last Modified":    fmt_date(date + timedelta(days=random.randint(0, 30))) if is_office_doc else "",
            "Title":                 title if is_office_doc else "",
            "Company":               "Mallinckrodt Inc." if is_office_doc else "",
            "Word Count":            random.randint(200, 8000) if file_type == "Office - Word" else "",
            "Slide Count":           random.randint(5, 45) if file_type == "Office - PowerPoint" else "",
            "Sheet Names":           "Sheet1; Sheet2" if file_type == "Office - Excel" else "",
            # ── PDF ──
            "PDF Author":            custodian["name"] if is_pdf else "",
            "PDF Creator":           random.choice(["Microsoft Word", "Adobe Acrobat", "Nuance PDF"]) if is_pdf else "",
            "PDF Producer":          "Adobe PDF Library" if is_pdf else "",
            "PDF Page Count":        pages if is_pdf else "",
            "Is Encrypted":          "No",
            "Is Form":               random.choice(["Yes", "No", "No", "No"]) if is_pdf else "",
            # ── RSMF ──
            "Rsmf/Application":      rsmf_app,
            "Rsmf/Participants":     rsmf_parts,
            "Rsmf/MessageCount":     rsmf_msgs,
            "Rsmf/BeginDate":        rsmf_begin,
            "Rsmf/EndDate":          rsmf_end,
            "Rsmf/EventCollectionId": rsmf_evt,
        }

    print("\n  Generating documents...")

    # Duplicates / NIST
    for i in range(n_dup):
        c = custodian_pool[len(docs)]
        ft = weighted_choice(cfg["file_types"])
        d = new_doc(c, ft, "Pre-Review: Duplicate/NIST")
        d["Cull Reason"]    = random.choice(CULL_REASONS)
        d["Duplicate Spare"] = "Yes"
        docs.append(d)

    # Processing errors
    for i in range(n_proc_err):
        c = custodian_pool[len(docs)]
        ft = weighted_choice(cfg["file_types"])
        d = new_doc(c, ft, "Pre-Review: Processing Error")
        d["Processing Status"]     = "Error"
        d["Processing Error Type"] = random.choice(PROCESSING_ERROR_TYPES)
        docs.append(d)

    # ECA excluded
    for i in range(n_eca):
        c = custodian_pool[len(docs)]
        ft = weighted_choice(cfg["file_types"])
        d = new_doc(c, ft, "ECA: Excluded")
        d["ECA Exclusion Reason"] = random.choice(ECA_EXCLUSION_REASONS)
        docs.append(d)

    # Review population
    review_docs  = []
    reviewed_docs = []

    for i in range(n_review):
        c  = custodian_pool[len(docs)]
        ft = weighted_choice(cfg["file_types"])
        if i < n_reviewed:
            d = new_doc(c, ft, "Review: Reviewed")
            reviewed_docs.append(d)
        elif i < n_reviewed + n_inprogress:
            d = new_doc(c, ft, "Review: In Progress")
        else:
            d = new_doc(c, ft, "Review: Queued")
        review_docs.append(d)
        docs.append(d)

    # Apply responsiveness + privilege to reviewed docs
    random.shuffle(reviewed_docs)
    resp_docs    = reviewed_docs[:n_responsive]
    nonresp_docs = reviewed_docs[n_responsive:n_responsive + n_nonresp]
    notsure_docs = reviewed_docs[n_responsive + n_nonresp:]

    for d in resp_docs:    d["Responsiveness"] = "Responsive"
    for d in nonresp_docs: d["Responsiveness"] = "Non-Responsive"
    for d in notsure_docs: d["Responsiveness"] = "Not Sure"

    priv_docs    = resp_docs[:n_privilege]
    produced_docs = resp_docs[n_privilege:]

    for d in priv_docs:
        d["Privilege"]        = "Privileged"
        d["Privilege Reason"] = random.choice(PRIVILEGE_REASONS)

    hot_sample = random.sample(resp_docs, min(n_hot, len(resp_docs)))
    for d in hot_sample:
        d["Hot Doc"]    = "Yes"
        d["Issue Tags"] = random.choice(ISSUE_TAGS)

    # TAR scores for all reviewed
    for d in reviewed_docs:
        score = tar_score()
        d["TAR Score"]             = score
        d["AL Predicted Relevant"] = "Yes" if score >= 50 else "No"

    # Bates numbers + production set for produced docs
    random.shuffle(produced_docs)
    redacted_sample = random.sample(produced_docs, min(n_redacted, len(produced_docs)))
    for d in produced_docs:
        bb, be = next_bates(int(d["Page Count"]))
        d["Bates Begin"]    = bb
        d["Bates End"]      = be
        d["Production Set"] = f"VOL{random.randint(1, cfg['productions']):03d}"
        if d in redacted_sample:
            d["Redacted"]        = "Yes"
            d["Redaction Reason"] = random.choice(["PII - Patient Information", "Privilege - Partial", "Privacy - Third Party"])

    # Build email families
    email_docs = [d for d in docs if d["File Type Category"] == "Email"]
    print(f"  Building email families ({len(email_docs):,} emails)...")
    families = build_email_families(email_docs, cfg["date_start"], cfg["date_end"])

    # Build batches
    print(f"  Building batches ({len(reviewed_docs):,} reviewed docs)...")
    batches = build_batches(reviewed_docs, tier_name, reviewer_pool)

    # ── Write outputs ──
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # documents.csv
    docs_path = os.path.join(out_dir, "documents.csv")
    fieldnames = list(docs[0].keys())
    print(f"\n  Writing {docs_path}...")
    with open(docs_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(docs)
    size_mb = os.path.getsize(docs_path) / 1e6
    print(f"    {len(docs):,} documents, {size_mb:.1f} MB")

    # custodians.json
    custs_path = os.path.join(out_dir, "custodians.json")
    custs_out  = []
    for c in custs:
        count = sum(1 for d in docs if d["Custodian"] == c["name"])
        custs_out.append({**c, "actual_doc_count": count})
    with open(custs_path, "w") as f:
        json.dump(custs_out, f, indent=2)
    print(f"  Written {custs_path} ({len(custs_out)} custodians)")

    # email-families.json
    fam_path = os.path.join(out_dir, "email-families.json")
    with open(fam_path, "w") as f:
        json.dump(families, f, indent=2)
    fam_mb = os.path.getsize(fam_path) / 1e6
    print(f"  Written {fam_path} ({len(families):,} families, {fam_mb:.1f} MB)")

    # batches.json
    bat_path = os.path.join(out_dir, "batches.json")
    with open(bat_path, "w") as f:
        json.dump(batches, f, indent=2)
    print(f"  Written {bat_path} ({len(batches)} batches)")

    print(f"\n  Done. All files written to: {out_dir}")
    return docs, families, batches


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate OIDA Relativity mock metadata")
    parser.add_argument("--tier",   required=True, choices=["small", "medium", "large"],
                        help="Dataset tier: small (~1,500 docs), medium (~10,000), large (~150,000)")
    parser.add_argument("--out",    default=None,
                        help="Output directory (default: mock-data/{tier}/)")
    parser.add_argument("--seed",   type=int, default=DEFAULT_SEED,
                        help="Random seed for reproducibility (default: 42)")
    args = parser.parse_args()

    out_dir = args.out or os.path.join("mock-data", args.tier)
    generate(args.tier, out_dir, args.seed)


if __name__ == "__main__":
    main()
