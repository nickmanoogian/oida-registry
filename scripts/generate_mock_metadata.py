#!/usr/bin/env python3
"""
generate_mock_metadata.py — OIDA MDL 2804 Relativity Mock Data Generator

Generates Relativity workspace metadata built around the National Prescription
Opiate Litigation (MDL 2804). The dataset tells a coherent story across three
defendant organizations — Mallinckrodt, Insys Therapeutics, and McKinsey — with
a four-phase timeline, scripted hot documents, scripted email threads, phase-aware
responsiveness rates, and issue tag clustering.

Outputs (to mock-data/{tier}/):
  documents.csv        — one row per document, all Relativity fields + narrative fields
  custodians.json      — custodian profiles with org, role, hold status
  email-families.json  — parent/child threading (organic + scripted story threads)
  batches.json         — batch assignments and reviewer info

Usage:
  python scripts/generate_mock_metadata.py --tier small
  python scripts/generate_mock_metadata.py --tier medium
  python scripts/generate_mock_metadata.py --tier large
  python scripts/generate_mock_metadata.py --tier small --seed 99 --out ./custom/
"""

import argparse, csv, json, os, random, sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEFAULT_SEED = 42

# ── Narrative: MDL 2804 Phase Definitions ────────────────────────────────

NARRATIVE_PHASES = {
    1: {"name": "Growth",    "start": "2010-01-01", "end": "2012-12-31"},
    2: {"name": "Pressure",  "start": "2013-01-01", "end": "2014-12-31"},
    3: {"name": "Crisis",    "start": "2015-01-01", "end": "2016-12-31"},
    4: {"name": "Litigation","start": "2017-01-01", "end": "2018-06-30"},
}

PHASE_WEIGHTS = {
    "small":  {2: 0.45, 3: 0.55},
    "medium": {1: 0.08, 2: 0.32, 3: 0.38, 4: 0.22},
    "large":  {1: 0.18, 2: 0.27, 3: 0.30, 4: 0.25},
}

PHASE_RESPONSIVE_PCT = {1: 0.12, 2: 0.40, 3: 0.55, 4: 0.35}
PHASE_PRIVILEGE_PCT  = {1: 0.02, 2: 0.08, 3: 0.15, 4: 0.25}

ORG_BATES_PREFIX = {
    "Mallinckrodt":   "MNK",
    "Insys":          "INSYS",
    "McKinsey":       "MCK",
    "Outside Counsel":"OC",
}

ORG_COMPANY_NAME = {
    "Mallinckrodt":   "Mallinckrodt Inc.",
    "Insys":          "Insys Therapeutics",
    "McKinsey":       "McKinsey & Company",
    "Outside Counsel":"Kirkland & Ellis LLP",
}

# ── Custodians ────────────────────────────────────────────────────────────

CUSTODIANS = {
    "small": [
        {"id": "C001", "name": "Michael Brennan",  "email": "michael.brennan@mallinckrodt.com",
         "role": "VP, Sales & Marketing",   "dept": "Sales",          "doc_target": 700,
         "org": "Mallinckrodt", "phases_active": [1,2,3,4],
         "narrative": "SOM override decision-maker; escalated Cardinal Health flags",
         "hold": "Acknowledged", "hold_date": "2018-06-15", "key": True},
        {"id": "C002", "name": "Sarah Chen",        "email": "sarah.chen@mallinckrodt.com",
         "role": "Regional Sales Director", "dept": "Sales",          "doc_target": 350,
         "org": "Mallinckrodt", "phases_active": [1,2,3],
         "narrative": "Field-level orders; first to receive suspicious order alerts",
         "hold": "Acknowledged", "hold_date": "2018-06-18"},
        {"id": "C003", "name": "Thomas Bradley",    "email": "thomas.bradley@mallinckrodt.com",
         "role": "Chief Compliance Officer","dept": "Legal & Compliance","doc_target": 300,
         "org": "Mallinckrodt", "phases_active": [2,3,4],
         "narrative": "Internal compliance objector; legal hold coordinator; whistleblower escalation",
         "hold": "Acknowledged", "hold_date": "2018-06-20"},
        {"id": "C004", "name": "Lisa Torres",       "email": "lisa.torres@mallinckrodt.com",
         "role": "Executive Assistant",     "dept": "Administration", "doc_target": 150,
         "org": "Mallinckrodt", "phases_active": [2,3],
         "narrative": "Calendar custodian; hold never acknowledged",
         "hold": "Outstanding", "hold_date": None},
    ],
    "medium": [
        {"id": "C001", "name": "James Whitfield",   "email": "james.whitfield@mallinckrodt.com",
         "role": "Chief Executive Officer",        "dept": "Executive",          "doc_target": 1800,
         "org": "Mallinckrodt", "phases_active": [1,2,3,4],
         "narrative": "Ultimate SOM override authority; McKinsey engagement sponsor",
         "hold": "Acknowledged", "hold_date": "2018-06-12", "key": True},
        {"id": "C002", "name": "Patricia Morrison", "email": "patricia.morrison@mallinckrodt.com",
         "role": "VP, Marketing",                  "dept": "Marketing",          "doc_target": 1500,
         "org": "Mallinckrodt", "phases_active": [1,2,3,4],
         "narrative": "Sales maximization strategy; receives McKinsey deliverables; quota spreadsheet author",
         "hold": "Acknowledged", "hold_date": "2018-06-12", "key": True},
        {"id": "C003", "name": "Robert Ashton",     "email": "robert.ashton@mallinckrodt.com",
         "role": "VP, Sales",                      "dept": "Sales",              "doc_target": 1200,
         "org": "Mallinckrodt", "phases_active": [2,3,4],
         "narrative": "SOM flag override chain; territory quota pressure; key actor in Cardinal Health decision",
         "hold": "Acknowledged", "hold_date": "2018-06-13", "key": True},
        {"id": "C004", "name": "Thomas Bradley",    "email": "thomas.bradley@mallinckrodt.com",
         "role": "Chief Compliance Officer",       "dept": "Legal & Compliance", "doc_target": 600,
         "org": "Mallinckrodt", "phases_active": [2,3,4],
         "narrative": "Internal dissent on SOM; legal hold coordinator; forwarded whistleblower tip to counsel",
         "hold": "Acknowledged", "hold_date": "2018-06-15"},
        {"id": "C005", "name": "Sandra Nguyen",     "email": "sandra.nguyen@mallinckrodt.com",
         "role": "Regional Sales Director",        "dept": "Sales",              "doc_target": 700,
         "org": "Mallinckrodt", "phases_active": [1,2],
         "narrative": "Escalated Cardinal Health order anomaly that triggered the override chain",
         "hold": "Acknowledged", "hold_date": "2018-06-15"},
        {"id": "C006", "name": "Gregory Nash",      "email": "gregory.nash@mallinckrodt.com",
         "role": "Director, SOM Compliance",       "dept": "Legal & Compliance", "doc_target": 400,
         "org": "Mallinckrodt", "phases_active": [1,2,3,4],
         "narrative": "Day-to-day SOM operations; wrote business justification memos for overrides; SOM deletion log",
         "hold": "Acknowledged", "hold_date": "2018-06-18"},
        {"id": "C007", "name": "Michelle Park",     "email": "michelle.park@mallinckrodt.com",
         "role": "Medical Affairs Director",       "dept": "Medical Affairs",    "doc_target": 500,
         "org": "Mallinckrodt", "phases_active": [1,2,3],
         "narrative": "Speaker bureau KOL management; physician payment justification",
         "hold": "Acknowledged", "hold_date": "2018-06-18"},
        {"id": "C008", "name": "Dr. Alec Harrington","email": "alec.harrington@insysrx.com",
         "role": "VP, Sales",                      "dept": "Sales",              "doc_target": 500,
         "org": "Insys", "phases_active": [2,3,4],
         "narrative": "Speaker bureau architect; payment escalation approver; prior auth fraud overseer",
         "hold": "Acknowledged", "hold_date": "2018-07-01"},
        {"id": "C009", "name": "Natalie Rosen",     "email": "natalie.rosen@insysrx.com",
         "role": "Reimbursement Manager",          "dept": "Reimbursement",      "doc_target": 200,
         "org": "Insys", "phases_active": [2,3],
         "narrative": "IRC prior authorization fraud; scripted calls to payers; call guide author",
         "hold": "Acknowledged", "hold_date": "2018-07-01"},
        {"id": "C010", "name": "Bradley Tevelow",   "email": "bradley.tevelow@mckinsey.com",
         "role": "Senior Engagement Manager",      "dept": "Healthcare Practice", "doc_target": 100,
         "org": "McKinsey", "phases_active": [1,2],
         "narrative": "Delivered opioid sales maximization strategy; the turbocharge deck",
         "hold": "Outstanding", "hold_date": None},
    ],
    "large": [
        {"id": "C001", "name": "James Whitfield",    "email": "james.whitfield@mallinckrodt.com",
         "role": "Chief Executive Officer",         "dept": "Executive",           "doc_target": 12000,
         "org": "Mallinckrodt", "phases_active": [1,2,3,4],
         "narrative": "Ultimate override authority; MDL settlement approver",
         "hold": "Acknowledged", "hold_date": "2018-08-10", "key": True},
        {"id": "C002", "name": "Mark Trevino",       "email": "mark.trevino@mallinckrodt.com",
         "role": "Chief Commercial Officer",        "dept": "Executive",           "doc_target": 10000,
         "org": "Mallinckrodt", "phases_active": [1,2,3,4],
         "narrative": "Commercial strategy; quota escalation; McKinsey engagement sponsor",
         "hold": "Acknowledged", "hold_date": "2018-08-10", "key": True},
        {"id": "C003", "name": "Patricia Morrison",  "email": "patricia.morrison@mallinckrodt.com",
         "role": "VP, Marketing",                   "dept": "Marketing",           "doc_target": 8000,
         "org": "Mallinckrodt", "phases_active": [1,2,3,4],
         "narrative": "Oxycodone positioning; quota spreadsheet; McKinsey turbocharge deck recipient",
         "hold": "Acknowledged", "hold_date": "2018-08-11", "key": True},
        {"id": "C004", "name": "Robert Ashton",      "email": "robert.ashton@mallinckrodt.com",
         "role": "VP, Sales",                       "dept": "Sales",               "doc_target": 7500,
         "org": "Mallinckrodt", "phases_active": [2,3,4],
         "narrative": "SOM override chain; Cardinal Health decision; territory quota pressure",
         "hold": "Acknowledged", "hold_date": "2018-08-11", "key": True},
        {"id": "C005", "name": "Diana Kowalski",     "email": "diana.kowalski@mallinckrodt.com",
         "role": "VP, Regulatory Affairs",          "dept": "Regulatory",          "doc_target": 6000,
         "org": "Mallinckrodt", "phases_active": [1,2,3,4],
         "narrative": "DEA quota negotiations; SOM program stewardship; forwarded DEA letter",
         "hold": "Acknowledged", "hold_date": "2018-08-12", "key": True},
        {"id": "C006", "name": "Thomas Bradley",     "email": "thomas.bradley@mallinckrodt.com",
         "role": "Chief Compliance Officer",        "dept": "Legal & Compliance",  "doc_target": 4000,
         "org": "Mallinckrodt", "phases_active": [2,3,4],
         "narrative": "Internal dissent; legal hold issuance; whistleblower escalation",
         "hold": "Acknowledged", "hold_date": "2018-08-14"},
        {"id": "C007", "name": "Michelle Park",      "email": "michelle.park@mallinckrodt.com",
         "role": "Medical Affairs Director",        "dept": "Medical Affairs",     "doc_target": 3500,
         "org": "Mallinckrodt", "phases_active": [1,2,3],
         "narrative": "Speaker bureau KOL management; physician payment justification",
         "hold": "Acknowledged", "hold_date": "2018-08-15"},
        {"id": "C008", "name": "Gregory Nash",       "email": "gregory.nash@mallinckrodt.com",
         "role": "Director, SOM Compliance",        "dept": "Legal & Compliance",  "doc_target": 3000,
         "org": "Mallinckrodt", "phases_active": [1,2,3,4],
         "narrative": "Day-to-day SOM; override memos; SOM deletion log after legal hold",
         "hold": "Acknowledged", "hold_date": "2018-08-15"},
        {"id": "C009", "name": "Sandra Nguyen",      "email": "sandra.nguyen@mallinckrodt.com",
         "role": "Regional Sales Dir. – East",      "dept": "Sales",               "doc_target": 4500,
         "org": "Mallinckrodt", "phases_active": [1,2],
         "narrative": "Escalated Cardinal Health anomaly alert that triggered the override chain",
         "hold": "Acknowledged", "hold_date": "2018-08-14"},
        {"id": "C010", "name": "Laura Finnegan",     "email": "laura.finnegan@mallinckrodt.com",
         "role": "Director, Government Affairs",    "dept": "Government Affairs",  "doc_target": 2800,
         "org": "Mallinckrodt", "phases_active": [3,4],
         "narrative": "State AG liaison; Ohio subpoena response coordinator",
         "hold": "Acknowledged", "hold_date": "2018-08-16"},
        {"id": "C011", "name": "Dr. Alec Harrington","email": "alec.harrington@insysrx.com",
         "role": "VP, Sales",                       "dept": "Sales",               "doc_target": 5000,
         "org": "Insys", "phases_active": [2,3,4],
         "narrative": "Speaker bureau architect; IRC fraud overseer; RICO defendant",
         "hold": "Acknowledged", "hold_date": "2018-07-01"},
        {"id": "C012", "name": "Natalie Rosen",      "email": "natalie.rosen@insysrx.com",
         "role": "Reimbursement Manager",           "dept": "Reimbursement",       "doc_target": 2000,
         "org": "Insys", "phases_active": [2,3],
         "narrative": "IRC scripted prior auth calls; insurer fraud execution; call guide author",
         "hold": "Acknowledged", "hold_date": "2018-07-02"},
        {"id": "C013", "name": "Bradley Tevelow",    "email": "bradley.tevelow@mckinsey.com",
         "role": "Senior Engagement Manager",       "dept": "Healthcare Practice", "doc_target": 800,
         "org": "McKinsey", "phases_active": [1,2],
         "narrative": "Delivered opioid growth acceleration strategy; the turbocharge deck",
         "hold": "Outstanding", "hold_date": None},
        {"id": "C014", "name": "Richard Galveston",  "email": "rgalveston@kirklandoutside.com",
         "role": "Senior Litigation Partner",       "dept": "Outside Counsel",     "doc_target": 1200,
         "org": "Outside Counsel", "phases_active": [3,4],
         "narrative": "DEA response; legal hold coordination; MDL settlement negotiations",
         "hold": "Acknowledged", "hold_date": "2018-08-20"},
        # Peripheral Mallinckrodt custodians (C015–C040)
        {"id": "C015", "name": "Brian Holloway",    "email": "brian.holloway@mallinckrodt.com",   "role": "National Sales Manager",       "dept": "Sales",          "doc_target": 2500, "org": "Mallinckrodt", "phases_active": [1,2,3,4], "hold": "Acknowledged", "hold_date": "2018-08-18"},
        {"id": "C016", "name": "Amanda Pierce",     "email": "amanda.pierce@mallinckrodt.com",    "role": "District Manager – Southeast", "dept": "Sales",          "doc_target": 1200, "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-08-22"},
        {"id": "C017", "name": "Steven Calloway",   "email": "steven.calloway@mallinckrodt.com",  "role": "Medical Science Liaison",      "dept": "Medical Affairs","doc_target": 1000, "org": "Mallinckrodt", "phases_active": [1,2,3],   "hold": "Acknowledged", "hold_date": "2018-08-24"},
        {"id": "C018", "name": "Natalie Cruz",      "email": "natalie.cruz@mallinckrodt.com",     "role": "Marketing Manager",            "dept": "Marketing",      "doc_target": 900,  "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-08-24"},
        {"id": "C019", "name": "Daniel Cho",        "email": "daniel.cho@mallinckrodt.com",       "role": "Regulatory Affairs Manager",   "dept": "Regulatory",     "doc_target": 800,  "org": "Mallinckrodt", "phases_active": [2,3],     "hold": "Acknowledged", "hold_date": "2018-08-26"},
        {"id": "C020", "name": "Melissa Grant",     "email": "melissa.grant@mallinckrodt.com",    "role": "Associate General Counsel",    "dept": "Legal",          "doc_target": 700,  "org": "Mallinckrodt", "phases_active": [3,4],     "hold": "Acknowledged", "hold_date": "2018-08-26"},
        {"id": "C021", "name": "Paul Whitmore",     "email": "paul.whitmore@mallinckrodt.com",    "role": "District Manager – SW",        "dept": "Sales",          "doc_target": 600,  "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-08-28"},
        {"id": "C022", "name": "Rachel Stern",      "email": "rachel.stern@mallinckrodt.com",     "role": "Executive Assistant – CCO",    "dept": "Administration", "doc_target": 500,  "org": "Mallinckrodt", "phases_active": [2,3,4],   "hold": "Acknowledged", "hold_date": "2018-08-28"},
        {"id": "C023", "name": "Carlos Ibarra",     "email": "carlos.ibarra@mallinckrodt.com",    "role": "Inside Sales Rep",             "dept": "Sales",          "doc_target": 400,  "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-09-02"},
        {"id": "C024", "name": "Heather Bloom",     "email": "heather.bloom@mallinckrodt.com",    "role": "Clinical Educator",            "dept": "Medical Affairs","doc_target": 350,  "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-09-02"},
        {"id": "C025", "name": "Timothy Marsh",     "email": "timothy.marsh@mallinckrodt.com",    "role": "Trade Relations Manager",      "dept": "Sales",          "doc_target": 300,  "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-09-05"},
        {"id": "C026", "name": "Donna Callahan",    "email": "donna.callahan@mallinckrodt.com",   "role": "Sales Operations Analyst",     "dept": "Sales",          "doc_target": 250,  "org": "Mallinckrodt", "phases_active": [2,3],     "hold": "Acknowledged", "hold_date": "2018-09-05"},
        {"id": "C027", "name": "Frank DeLuca",      "email": "frank.deluca@mallinckrodt.com",     "role": "IT Systems Administrator",     "dept": "IT",             "doc_target": 200,  "org": "Mallinckrodt", "phases_active": [1,2,3,4], "hold": "Acknowledged", "hold_date": "2018-09-10"},
        {"id": "C028", "name": "Sarah Patel",       "email": "sarah.patel@mallinckrodt.com",      "role": "HR Business Partner",          "dept": "Human Resources","doc_target": 180,  "org": "Mallinckrodt", "phases_active": [2,3],     "hold": "Acknowledged", "hold_date": "2018-09-10"},
        {"id": "C029", "name": "Walter Kim",        "email": "walter.kim@mallinckrodt.com",       "role": "Finance Manager",              "dept": "Finance",        "doc_target": 150,  "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Escalated",    "hold_date": "2018-09-12"},
        {"id": "C030", "name": "Nicole Russo",      "email": "nicole.russo@mallinckrodt.com",     "role": "Senior Paralegal",             "dept": "Legal",          "doc_target": 130,  "org": "Mallinckrodt", "phases_active": [3,4],     "hold": "Acknowledged", "hold_date": "2018-09-15"},
        {"id": "C031", "name": "Andrew Flynn",      "email": "andrew.flynn@mallinckrodt.com",     "role": "QA Specialist",                "dept": "Quality",        "doc_target": 110,  "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-09-15"},
        {"id": "C032", "name": "Tiffany Bell",      "email": "tiffany.bell@mallinckrodt.com",     "role": "Administrative Coordinator",   "dept": "Administration", "doc_target": 100,  "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-09-18"},
        {"id": "C033", "name": "Marcus Webb",       "email": "marcus.webb@mallinckrodt.com",      "role": "Government Pricing Analyst",   "dept": "Finance",        "doc_target": 90,   "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-09-18"},
        {"id": "C034", "name": "Irene Hoffman",     "email": "irene.hoffman@mallinckrodt.com",    "role": "Contracts Manager",            "dept": "Legal",          "doc_target": 80,   "org": "Mallinckrodt", "phases_active": [2,3],     "hold": "Acknowledged", "hold_date": "2018-09-20"},
        {"id": "C035", "name": "Owen Garrett",      "email": "owen.garrett@mallinckrodt.com",     "role": "Lab Technician",               "dept": "R&D",            "doc_target": 70,   "org": "Mallinckrodt", "phases_active": [1],       "hold": "Acknowledged", "hold_date": "2018-09-20"},
        {"id": "C036", "name": "Priya Mehta",       "email": "priya.mehta@mallinckrodt.com",      "role": "BI Analyst",                   "dept": "Sales",          "doc_target": 60,   "org": "Mallinckrodt", "phases_active": [2,3],     "hold": "Acknowledged", "hold_date": "2018-09-22"},
        {"id": "C037", "name": "Jason Dunn",        "email": "jason.dunn@mallinckrodt.com",       "role": "Warehouse Supervisor",         "dept": "Operations",     "doc_target": 50,   "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Acknowledged", "hold_date": "2018-09-25"},
        {"id": "C038", "name": "Claire Simmons",    "email": "claire.simmons@mallinckrodt.com",   "role": "Receptionist",                 "dept": "Administration", "doc_target": 40,   "org": "Mallinckrodt", "phases_active": [1],       "hold": "Outstanding",  "hold_date": None},
        {"id": "C039", "name": "Victor Okafor",     "email": "victor.okafor@mallinckrodt.com",    "role": "Supply Chain Analyst",         "dept": "Operations",     "doc_target": 30,   "org": "Mallinckrodt", "phases_active": [1,2],     "hold": "Outstanding",  "hold_date": None},
        {"id": "C040", "name": "Angela Washington", "email": "angela.washington@mallinckrodt.com","role": "Legal Coordinator",            "dept": "Legal",          "doc_target": 20,   "org": "Mallinckrodt", "phases_active": [3,4],     "hold": "Outstanding",  "hold_date": None},
    ],
}

# ── Issue Tag Matrix (Rule 2 / Narrative) ─────────────────────────────────

ISSUE_TAG_MATRIX = {
    ("Mallinckrodt", 1): ["Sales Incentives", "McKinsey Strategy", "DEA Reporting", "Speaker Bureau"],
    ("Mallinckrodt", 2): ["SOM Override", "DEA Correspondence", "Sales Incentives", "Speaker Bureau Payments", "McKinsey Strategy"],
    ("Mallinckrodt", 3): ["SOM Override", "Legal Hold", "Whistleblower", "State AG Investigation", "DEA Correspondence", "Speaker Bureau Payments"],
    ("Mallinckrodt", 4): ["Legal Hold", "State AG Investigation", "DEA Correspondence", "SOM Override"],
    ("Insys", 1):        ["Speaker Bureau Payments", "Sales Incentives"],
    ("Insys", 2):        ["Speaker Bureau Payments", "Prior Auth Fraud", "Sales Incentives"],
    ("Insys", 3):        ["Prior Auth Fraud", "Speaker Bureau Payments", "Legal Hold", "Whistleblower"],
    ("Insys", 4):        ["Prior Auth Fraud", "Legal Hold", "State AG Investigation"],
    ("McKinsey", 1):     ["McKinsey Strategy", "Sales Incentives"],
    ("McKinsey", 2):     ["McKinsey Strategy", "Sales Incentives", "State AG Investigation"],
    ("McKinsey", 3):     ["McKinsey Strategy", "State AG Investigation", "Legal Hold"],
    ("McKinsey", 4):     ["McKinsey Strategy", "State AG Investigation"],
    ("Outside Counsel",3):["Legal Hold", "State AG Investigation", "DEA Correspondence"],
    ("Outside Counsel",4):["Legal Hold", "State AG Investigation", "DEA Correspondence"],
}
ISSUE_TAGS_FALLBACK = ["Sales Incentives", "DEA Reporting", "Legal Hold", "SOM Override"]

# ── Email Subject Pools (phase + org aware) ───────────────────────────────

EMAIL_SUBJECTS_BY_ORG_PHASE = {
    ("Mallinckrodt", 1): [
        "Q{q} {year} Oxycodone Territory Performance — {territory}",
        "FW: McKinsey Engagement — Opioid Growth Strategy Kickoff",
        "RE: {product} Market Share Update — {territory}",
        "Monthly SOM Report — {month} {year} — All Clear",
        "RE: Key Account Meeting — {account}",
        "Speaker Bureau KOL Recruitment — {month} {year}",
        "RE: DEA Quota Allocation {year} — Requested Volume",
        "FW: Managed Care Win — {territory} Formulary",
        "{product} Launch Briefing — District Managers",
        "RE: Annual Territory Business Plan — {year}",
        "FW: IMS Prescription Data — {month} {year}",
        "RE: Incentive Compensation Plan — {year} Targets",
        "Customer Order Update — {account} — {month}",
    ],
    ("Mallinckrodt", 2): [
        "RE: Override of Cardinal Health Suspicious Order Flag — {territory}",
        "FW: DEA Suspicious Order Monitoring — {month} {year} — Threshold Review",
        "RE: SOM Flag — {account} — Business Justification Required",
        "URGENT: Wholesaler Order Volume Anomaly — {territory}",
        "RE: DEA Diversion Investigator Meeting — SOM Program Review",
        "FW: Compliance Escalation — {territory} Order Patterns",
        "RE: Q{q} {year} Territory Quota — Variance Analysis",
        "SOM Policy Exception Request — {account} — {month} {year}",
        "FW: Cardinal Health — Order Anomaly Alert — {territory} Pharmacy Cluster",
        "RE: {product} Sales Incentive Acceleration — {year} Plan",
        "RE: DEA Response Preparation — SOM Documentation",
        "FW: District Manager Coaching — Volume Acceleration — {territory}",
    ],
    ("Mallinckrodt", 3): [
        "LEGAL HOLD NOTICE — Opioid Litigation — Immediate Action Required",
        "RE: Ohio AG Subpoena — Opioid Sales Practices — Response Coordination",
        "FW: State AG Investigation — {territory} — Document Preservation",
        "RE: Whistleblower Concerns — Speaker Bureau — Escalation",
        "RE: SOM Records Preservation — {month} {year} — Legal Hold Reminder",
        "FW: DEA Administrative Subpoena — Production Deadline {month} {year}",
        "RE: Congressional Inquiry — Opioid Distribution Practices",
        "FW: Internal Investigation Update — SOM Override Findings",
        "CONFIDENTIAL — Response to {account} Fraud Investigation Inquiry",
        "RE: Crisis Communications Plan — Opioid Media Inquiries",
        "FW: SOM Archive Cleanup — {month} {year}",
        "RE: Employee Disclosure — Cooperation with Investigators",
    ],
    ("Mallinckrodt", 4): [
        "RE: MDL 2804 — Discovery Order — Production Obligations",
        "FW: MDL 2804 — Plaintiff Liaison Counsel — Meet and Confer",
        "RE: Mallinckrodt Settlement Negotiation — $35M Framework",
        "FW: Document Production — Privilege Log Supplement",
        "RE: Deposition Preparation — {role}",
        "MDL 2804 — Clawback Notice — Inadvertent Production",
        "RE: Settlement Agreement — Mallinckrodt — Final Terms",
        "FW: Board Approval — Settlement Authorization",
        "MDL 2804 — Privilege Dispute — In Camera Review Request",
        "RE: Bankruptcy Filing Preparation — Mallinckrodt",
        "FW: State AG Coordinated Settlement — Multi-State Framework",
    ],
    ("Insys", 2): [
        "RE: Speaker Program — Dr. {speaker} Payments — {month} {year}",
        "FW: Subsys Speaker Bureau — Q{q} {year} KOL Roster",
        "RE: IRC Prior Authorization Process — Script Update v{n}",
        "FW: Sunshine Act Reporting — Speaker Payment Aggregation — {month}",
        "RE: IRC Call Script — Subsys Prior Authorization v{n}",
        "Subsys Speaker Event — {territory} — Attendance Report",
        "FW: IRC Payer Response — {account} — Prior Auth Approval",
        "RE: Subsys Sales Targets — Q{q} {year} — {territory}",
        "RE: Dr. {speaker} — Event Count Increase Request",
        "FW: Managed Care Update — Subsys Formulary — {account}",
    ],
    ("Insys", 3): [
        "FW: UHC Fraud Investigation — Subsys Prior Authorization Pattern",
        "RE: DOJ Civil Investigation — Insys Reimbursement Center",
        "PRIVILEGED — FW: Subsys IRC Practices — Attorney Review",
        "RE: Speaker Bureau — Internal Compliance Review — {month} {year}",
        "FW: State AG Investigation — Insys Speaker Program",
        "RE: Dr. {speaker} — DOJ Witness Interview",
        "FW: Whistleblower Complaint — IRC Script Practices",
        "CONFIDENTIAL — Insys Exposure Analysis — Speaker Payments",
        "FW: DOJ Grand Jury Subpoena — IRC Records",
        "RE: Insys Corporate Compliance — Emergency Protocol",
    ],
    ("Insys", 4): [
        "FW: DOJ — RICO Indictment — Insys Executives — Privileged Review",
        "RE: CEO John Kapoor — Criminal Defense Coordination",
        "FW: Insys Settlement Discussion — DOJ Framework",
        "RE: Insys Bankruptcy — Chapter 11 Planning",
        "FW: MDL 2804 — Insys Document Production",
    ],
    ("McKinsey", 1): [
        "RE: Mallinckrodt Opioid Engagement — Diagnostic Phase Update",
        "FW: Generic Oxycodone Market — Growth Opportunity Analysis",
        "RE: Mallinckrodt — Territory Restructuring Recommendation",
        "FW: Opioid Sales Maximization — Benchmark Analysis — {territory}",
        "RE: McKinsey Deliverable — {product} Acceleration Strategy",
        "FW: Mallinckrodt Executive Team — Strategy Presentation",
        "RE: Incentive Compensation Redesign — McK Recommendation",
        "FW: Generic Opioid Growth Acceleration — Phase 2 Planning",
        "RE: Mallinckrodt Board Presentation — Growth Strategy",
    ],
    ("McKinsey", 2): [
        "RE: Mallinckrodt — Follow-On Engagement — Sales Operations",
        "FW: McKinsey — Opioid Portfolio Review — Updated",
        "RE: MNK Engagement — Close-Out Documentation",
        "FW: McKinsey Internal — Opioid Client Exposure Review",
        "RE: McKinsey — Regulatory Risk Assessment — Client Portfolio",
    ],
    ("McKinsey", 3): [
        "RE: McKinsey — Opioid Practice — Reputational Risk Review",
        "FW: McKinsey State AG — Response Coordination",
        "RE: McKinsey Opioid Settlement — $600M Framework Discussion",
    ],
    ("Outside Counsel", 3): [
        "PRIVILEGED — RE: Legal Hold Implementation — Mallinckrodt",
        "FW: DEA Response Draft — Attorney Review Required",
        "RE: Ohio AG Subpoena — Scope Limitation Strategy",
        "PRIVILEGED — Internal Investigation Findings — Outside Counsel",
        "RE: MDL Exposure Analysis — Mallinckrodt SOM Claims",
    ],
    ("Outside Counsel", 4): [
        "RE: MDL 2804 — Settlement Framework — Privileged",
        "FW: Discovery Order No. 1 — Production Obligations",
        "RE: Mallinckrodt $35M Settlement — Board Authorization",
        "PRIVILEGED — Deposition Preparation — Executive Witnesses",
        "FW: MDL — Clawback Protocol — Inadvertent Production",
    ],
}

OFFICE_TITLES_BY_PHASE = {
    1: [
        "McKinsey — Generic Opioid Growth Acceleration Strategy v{n}.{n}",
        "Territory Business Plan {year} — {territory}",
        "Speaker Bureau Program Guidelines v{n}.0",
        "Q{q} {year} Marketing Presentation — {product}",
        "SOM Policy and Procedure Manual v{n}.0",
        "Key Account Strategy — {account} {year}",
        "{product} Market Analysis — {year}",
        "Annual Incentive Compensation Plan {year}",
        "Medical Affairs KOL Engagement Protocol",
        "DEA Quota Allocation Request — {year}",
    ],
    2: [
        "SOM Flag Exception Documentation — {account} — {month} {year}",
        "SOM Override Business Justification Memo — {territory}",
        "DEA Compliance Response Preparation — {year}",
        "Speaker Bureau Payment Summary — Q{q} {year}",
        "IRC Prior Authorization Call Guide v{n}",
        "Suspicious Order Threshold Review — Internal",
        "Sales Incentive Acceleration Plan — {year}",
        "Wholesaler Order Pattern Analysis — {account}",
        "DEA SOM Inspection Preparation — Checklist",
        "FY{year} — Sales Incentive Compensation Plan — Oxycodone Territory Quotas",
    ],
    3: [
        "Legal Hold Custodian Inventory — {month} {year}",
        "Ohio AG Subpoena Response — Draft v{n}",
        "SOM Records Preservation Protocol",
        "Internal Investigation Findings — SOM Override Review",
        "Crisis Communications Talking Points — Opioid Litigation",
        "State AG — Multistate Coordination — Settlement Framework",
        "Whistleblower Response Protocol — {year}",
        "Document Production Index — {month} {year}",
        "Congressional Hearing Preparation — {product} Sales",
    ],
    4: [
        "MDL 2804 — Production Index — VOL{n}0{n}",
        "Settlement Agreement — Mallinckrodt — $35M — DRAFT",
        "Privilege Log — Supplement {n} — {month} {year}",
        "Deposition Outline — Executive Witnesses",
        "MDL — Expert Witness Report — SOM Practices",
        "Bankruptcy Preparation — Chapter 11 Framework",
        "Clawback Log — Inadvertently Produced Documents",
        "MDL Settlement Board Resolution — {year}",
    ],
}

SPEAKER_NAMES = ["Dr. Alan Foster", "Dr. Maria Santos", "Dr. Susan Ellis", "Dr. Robert Kim", "Dr. Patricia Quinn"]

# ── Scripted Hot Documents ────────────────────────────────────────────────

SCRIPTED_HOT_DOCS = [
    {
        "control_number": "HOT-0000001",
        "subject": "RE: Override of Cardinal Health Suspicious Order Flag — Cincinnati, OH",
        "file_type": "Email - MSG",
        "phase": 2, "date": "2013-08-14",
        "custodian_by_tier": {"small": "Michael Brennan", "medium": "Robert Ashton", "large": "Robert Ashton"},
        "org": "Mallinckrodt",
        "issue_tags": "SOM Override; DEA Correspondence",
        "privilege": None,
        "why_hot": "Explicitly instructs SOM team to release flagged order; the word override in subject is the key search term",
    },
    {
        "control_number": "HOT-0000002",
        "title": "Mallinckrodt Generic Opioid — Growth Acceleration Strategy v3.2",
        "file_type": "Office - PowerPoint (PPTX)",
        "phase": 1, "date": "2011-09-22",
        "custodian_by_tier": {"small": "Michael Brennan", "medium": "Bradley Tevelow", "large": "Bradley Tevelow"},
        "org": "McKinsey",
        "issue_tags": "McKinsey Strategy; Sales Incentives",
        "privilege": None,
        "why_hot": "The turbocharge deck — centerpiece of the $600M McKinsey settlement",
        "tiers": ["medium", "large"],
    },
    {
        "control_number": "HOT-0000003",
        "subject": "FW: DEA Diversion Investigator Meeting — SOM Program Review [CONFIDENTIAL]",
        "file_type": "Email - MSG",
        "phase": 2, "date": "2014-03-07",
        "custodian_by_tier": {"small": "Thomas Bradley", "medium": "Thomas Bradley", "large": "Diana Kowalski"},
        "org": "Mallinckrodt",
        "issue_tags": "DEA Correspondence; SOM Override",
        "privilege": None,
        "why_hot": "Internal forward of DEA letter noting SOM inadequacies; Mallinckrodt continued shipping after receipt",
    },
    {
        "control_number": "HOT-0000004",
        "subject": "RE: Speaker Program — Dr. Alan Foster Payments Q3 2013",
        "file_type": "Email - MSG",
        "phase": 2, "date": "2013-10-09",
        "custodian_by_tier": {"small": "Michael Brennan", "medium": "Dr. Alec Harrington", "large": "Dr. Alec Harrington"},
        "org": "Insys",
        "issue_tags": "Speaker Bureau Payments",
        "privilege": None,
        "why_hot": "Direct approval of payments later characterized as kickbacks; Dr. Foster subsequently indicted",
        "tiers": ["medium", "large"],
    },
    {
        "control_number": "HOT-0000005",
        "title": "Insys Reimbursement Center — Prior Authorization Call Guide v4 [INTERNAL USE ONLY]",
        "file_type": "Office - Word (DOCX)",
        "phase": 2, "date": "2014-02-18",
        "custodian_by_tier": {"small": "Thomas Bradley", "medium": "Natalie Rosen", "large": "Natalie Rosen"},
        "org": "Insys",
        "issue_tags": "Prior Auth Fraud",
        "privilege": None,
        "why_hot": "The IRC call guide instructing agents to misrepresent patient diagnoses; exhibit in RICO trial",
        "tiers": ["medium", "large"],
    },
    {
        "control_number": "HOT-0000006",
        "subject": "CONFIDENTIAL — Concerns re: Speaker Bureau Payment Practices",
        "file_type": "Email - MSG",
        "phase": 3, "date": "2015-06-03",
        "custodian_by_tier": {"small": "Thomas Bradley", "medium": "Thomas Bradley", "large": "Thomas Bradley"},
        "org": "Mallinckrodt",
        "issue_tags": "Whistleblower; Speaker Bureau Payments",
        "privilege": "Attorney-Client Communication",
        "why_hot": "Bradley forwarded whistleblower tip to legal; establishes company knowledge before state AG filing",
    },
    {
        "control_number": "HOT-0000007",
        "subject": "LEGAL HOLD NOTICE — Opioid Litigation Matter — All Personnel — Immediate Action Required",
        "file_type": "Email - MSG",
        "phase": 3, "date": "2015-09-14",
        "custodian_by_tier": {"small": "Thomas Bradley", "medium": "Thomas Bradley", "large": "Thomas Bradley"},
        "org": "Mallinckrodt",
        "issue_tags": "Legal Hold",
        "privilege": None,
        "why_hot": "Legal hold that should have frozen SOM data; SOM deletions after this date became spoliation evidence",
    },
    {
        "control_number": "HOT-0000008",
        "title": "SOM_Flag_Archive_Cleanup_September2015.xlsx",
        "file_type": "Office - Excel (XLSX)",
        "phase": 3, "date": "2015-09-22",
        "custodian_by_tier": {"small": "Thomas Bradley", "medium": "Robert Ashton", "large": "Gregory Nash"},
        "org": "Mallinckrodt",
        "issue_tags": "SOM Override; Legal Hold",
        "privilege": None,
        "why_hot": "SOM record deletion occurring 8 days after legal hold issued — key spoliation document",
    },
    {
        "control_number": "HOT-0000009",
        "title": "DRAFT — Response to Ohio AG Subpoena — Mallinckrodt Opioid Sales Practices",
        "file_type": "Office - Word (DOCX)",
        "phase": 3, "date": "2016-01-15",
        "custodian_by_tier": {"small": "Thomas Bradley", "medium": "Thomas Bradley", "large": "Richard Galveston"},
        "org": "Outside Counsel",
        "issue_tags": "State AG Investigation; Legal Hold",
        "privilege": "Work Product - Litigation Preparation",
        "why_hot": "Redline edits altered facts vs earlier draft; version comparison showed strategic omissions",
    },
    {
        "control_number": "HOT-0000010",
        "subject": "FW: DOJ — RICO Indictment — Insys Executives — Immediate Privileged Review",
        "file_type": "Email - MSG",
        "phase": 4, "date": "2016-12-08",
        "custodian_by_tier": {"small": "Thomas Bradley", "medium": "Dr. Alec Harrington", "large": "Dr. Alec Harrington"},
        "org": "Insys",
        "issue_tags": "Prior Auth Fraud; Speaker Bureau Payments",
        "privilege": "Attorney-Client — Outside Counsel",
        "why_hot": "Harrington internal response to RICO indictment; establishes consciousness of guilt",
        "tiers": ["medium", "large"],
    },
    {
        "control_number": "HOT-0000011",
        "title": "Settlement Framework Discussion — McKinsey Opioid Engagement Liability [PRIVILEGED]",
        "file_type": "PDF - Text",
        "phase": 4, "date": "2017-08-30",
        "custodian_by_tier": {"small": "Thomas Bradley", "medium": "Bradley Tevelow", "large": "Bradley Tevelow"},
        "org": "McKinsey",
        "issue_tags": "McKinsey Strategy; State AG Investigation",
        "privilege": "Work Product - Litigation Preparation",
        "why_hot": "McKinsey internal discussion of settlement exposure; establishes awareness strategy was actionable",
        "tiers": ["medium", "large"],
    },
    {
        "control_number": "HOT-0000012",
        "subject": "URGENT: Cardinal Health — Order Volume Anomaly Alert — Butner, NC Pharmacy Cluster",
        "file_type": "Email - MSG",
        "phase": 2, "date": "2013-11-21",
        "custodian_by_tier": {"small": "Sarah Chen", "medium": "Sandra Nguyen", "large": "Sandra Nguyen"},
        "org": "Mallinckrodt",
        "issue_tags": "SOM Override; DEA Correspondence",
        "privilege": None,
        "why_hot": "The escalation that triggered the override chain; establishes distributor flagged orders before Mallinckrodt released them",
    },
    {
        "control_number": "HOT-0000013",
        "title": "FY2013 — Sales Incentive Compensation Plan — Oxycodone Territory Quotas",
        "file_type": "Office - Excel (XLSX)",
        "phase": 2, "date": "2013-01-15",
        "custodian_by_tier": {"small": "Michael Brennan", "medium": "Patricia Morrison", "large": "Patricia Morrison"},
        "org": "Mallinckrodt",
        "issue_tags": "Sales Incentives; McKinsey Strategy",
        "privilege": None,
        "why_hot": "Compensation plan tying bonuses directly to oxycodone volume with no compliance carve-outs",
    },
]

# ── Scripted Email Threads ────────────────────────────────────────────────

SCRIPTED_THREADS = [
    {
        "family_id": "SFAM-0001", "thread_id": "STHR-0001",
        "label": "SOM Override Decision Chain",
        "tiers": ["small", "medium", "large"],
        "messages": [
            {"ctrl": "HOT-0000012", "use_hot": True, "phase": 2, "date": "2013-11-21",
             "from_org": "Mallinckrodt", "from_name_tier": {"small": "Sarah Chen", "medium": "Sandra Nguyen", "large": "Sandra Nguyen"},
             "subject": "URGENT: Cardinal Health — Order Volume Anomaly Alert — Butner, NC Pharmacy Cluster",
             "issue_tags": "SOM Override; DEA Correspondence"},
            {"ctrl": "STHR-0001-002", "phase": 2, "date": "2013-11-22",
             "from_org": "Mallinckrodt", "from_name_tier": {"small": "Michael Brennan", "medium": "Robert Ashton", "large": "Robert Ashton"},
             "subject": "RE: URGENT: Cardinal Health — Order Volume Anomaly Alert — Butner, NC Pharmacy Cluster",
             "issue_tags": "SOM Override"},
            {"ctrl": "HOT-0000001", "use_hot": True, "phase": 2, "date": "2013-11-26",
             "from_org": "Mallinckrodt", "from_name_tier": {"small": "Michael Brennan", "medium": "Robert Ashton", "large": "Robert Ashton"},
             "subject": "RE: Override of Cardinal Health Suspicious Order Flag — Cincinnati, OH",
             "issue_tags": "SOM Override; DEA Correspondence", "inclusive": True},
        ],
    },
    {
        "family_id": "SFAM-0002", "thread_id": "STHR-0002",
        "label": "McKinsey Turbocharge Engagement",
        "tiers": ["medium", "large"],
        "messages": [
            {"ctrl": "STHR-0002-001", "phase": 1, "date": "2011-07-12",
             "from_org": "Mallinckrodt", "from_name_tier": {"medium": "James Whitfield", "large": "James Whitfield"},
             "subject": "Mallinckrodt — McKinsey Opioid Sales Engagement — Kickoff",
             "issue_tags": "McKinsey Strategy"},
            {"ctrl": "STHR-0002-002", "phase": 1, "date": "2011-09-15",
             "from_org": "McKinsey", "from_name_tier": {"medium": "Bradley Tevelow", "large": "Bradley Tevelow"},
             "subject": "RE: Mallinckrodt — McKinsey Opioid Sales Engagement — Kickoff",
             "issue_tags": "McKinsey Strategy; Sales Incentives"},
            {"ctrl": "HOT-0000002", "use_hot": True, "phase": 1, "date": "2011-09-22",
             "from_org": "McKinsey", "from_name_tier": {"medium": "Bradley Tevelow", "large": "Bradley Tevelow"},
             "subject": "FW: Mallinckrodt Generic Opioid — Growth Acceleration Strategy v3.2 (FINAL)",
             "issue_tags": "McKinsey Strategy; Sales Incentives", "inclusive": True},
        ],
    },
    {
        "family_id": "SFAM-0003", "thread_id": "STHR-0003",
        "label": "Insys Speaker Bureau Launch",
        "tiers": ["medium", "large"],
        "messages": [
            {"ctrl": "STHR-0003-001", "phase": 2, "date": "2013-07-08",
             "from_org": "Insys", "from_name_tier": {"medium": "Dr. Alec Harrington", "large": "Dr. Alec Harrington"},
             "subject": "Speaker Program Launch — Q3 2013 KOL Engagement Plan",
             "issue_tags": "Speaker Bureau Payments"},
            {"ctrl": "STHR-0003-002", "phase": 2, "date": "2013-09-14",
             "from_org": "Insys", "from_name_tier": {"medium": "Natalie Rosen", "large": "Natalie Rosen"},
             "subject": "RE: Speaker Program Launch — Q3 2013 KOL Engagement Plan",
             "issue_tags": "Speaker Bureau Payments"},
            {"ctrl": "HOT-0000004", "use_hot": True, "phase": 2, "date": "2013-10-09",
             "from_org": "Insys", "from_name_tier": {"medium": "Dr. Alec Harrington", "large": "Dr. Alec Harrington"},
             "subject": "RE: Speaker Program — Dr. Alan Foster Payments Q3 2013",
             "issue_tags": "Speaker Bureau Payments", "inclusive": True},
        ],
    },
    {
        "family_id": "SFAM-0004", "thread_id": "STHR-0004",
        "label": "Whistleblower and Legal Hold",
        "tiers": ["small", "medium", "large"],
        "messages": [
            {"ctrl": "HOT-0000006", "use_hot": True, "phase": 3, "date": "2015-06-03",
             "from_org": "Mallinckrodt", "from_name_tier": {"small": "Thomas Bradley", "medium": "Thomas Bradley", "large": "Thomas Bradley"},
             "subject": "CONFIDENTIAL — Concerns re: Speaker Bureau Payment Practices",
             "issue_tags": "Whistleblower; Speaker Bureau Payments", "privilege": "Attorney-Client Communication"},
            {"ctrl": "HOT-0000007", "use_hot": True, "phase": 3, "date": "2015-09-14",
             "from_org": "Mallinckrodt", "from_name_tier": {"small": "Thomas Bradley", "medium": "Thomas Bradley", "large": "Thomas Bradley"},
             "subject": "LEGAL HOLD NOTICE — Opioid Litigation Matter — All Personnel — Immediate Action Required",
             "issue_tags": "Legal Hold", "inclusive": True},
        ],
    },
    {
        "family_id": "SFAM-0005", "thread_id": "STHR-0005",
        "label": "DEA Response Strategy",
        "tiers": ["medium", "large"],
        "messages": [
            {"ctrl": "HOT-0000003", "use_hot": True, "phase": 2, "date": "2014-03-07",
             "from_org": "Mallinckrodt", "from_name_tier": {"medium": "Thomas Bradley", "large": "Diana Kowalski"},
             "subject": "FW: DEA Diversion Investigator Meeting — SOM Program Review [CONFIDENTIAL]",
             "issue_tags": "DEA Correspondence; SOM Override"},
            {"ctrl": "STHR-0005-002", "phase": 2, "date": "2014-03-10",
             "from_org": "Mallinckrodt", "from_name_tier": {"medium": "James Whitfield", "large": "James Whitfield"},
             "subject": "RE: DEA Diversion Investigator Meeting — SOM Program Review [CONFIDENTIAL]",
             "issue_tags": "DEA Correspondence", "privilege": "Attorney-Client Communication"},
            {"ctrl": "STHR-0005-003", "phase": 2, "date": "2014-04-30",
             "from_org": "Mallinckrodt", "from_name_tier": {"medium": "Thomas Bradley", "large": "Thomas Bradley"},
             "subject": "RE: DEA Diversion Investigator Meeting — SOM Program Review [CONFIDENTIAL]",
             "issue_tags": "DEA Correspondence; SOM Override", "inclusive": True},
        ],
    },
]

# ── Workflow Configuration ────────────────────────────────────────────────

WORKFLOW = {
    "small":  {"bates_prefix": "MNK", "productions": 1, "hot_pct": 0.02, "redacted_pct": 0.08},
    "medium": {"bates_prefix": "MNK", "productions": 2, "hot_pct": 0.015, "redacted_pct": 0.07},
    "large":  {"bates_prefix": "MNK", "productions": 4, "hot_pct": 0.013, "redacted_pct": 0.10},
}

DATE_RANGES = {
    "small":  ("2013-01-01", "2016-12-31"),
    "medium": ("2010-01-01", "2017-12-31"),
    "large":  ("2010-01-01", "2018-06-30"),
}

# ── File Type Definitions (RULES.md Rule 1 & 2) ───────────────────────────

FILE_TYPES = {
    "Email - MSG":                  {"extensions":["msg"],          "size_range":(15000,300000),    "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"MD5",              "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes"},
    "Email - EML":                  {"extensions":["eml"],          "size_range":(10000,200000),    "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"MD5",              "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes"},
    "Email Container - PST":        {"extensions":["pst"],          "size_range":(50000000,4000000000),"images":"No","ocr_required":"No","native_produced":"No","redactable":"No","analytics_eligible":"No","dedup_method":"N/A",           "is_container":True, "supported":True, "has_natives":"No","has_images":"No"},
    "Email Container - MBOX":       {"extensions":["mbox"],         "size_range":(10000000,2000000000),"images":"No","ocr_required":"No","native_produced":"No","redactable":"No","analytics_eligible":"No","dedup_method":"N/A",           "is_container":True, "supported":True, "has_natives":"No","has_images":"No"},
    "Calendar - ICS":               {"extensions":["ics"],          "size_range":(2000,20000),      "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No","blank_date_sent":True},
    "Office - Word (DOCX)":         {"extensions":["docx"],         "size_range":(25000,800000),    "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No"},
    "Office - Word (DOC)":          {"extensions":["doc"],          "size_range":(20000,600000),    "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No"},
    "Office - Excel (XLSX)":        {"extensions":["xlsx"],         "size_range":(20000,5000000),   "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No"},
    "Office - Excel (XLS)":         {"extensions":["xls"],          "size_range":(15000,3000000),   "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No"},
    "Office - PowerPoint (PPTX)":   {"extensions":["pptx"],         "size_range":(100000,8000000),  "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes","high_responsiveness":True},
    "Office - PowerPoint (PPT)":    {"extensions":["ppt"],          "size_range":(80000,6000000),   "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes","high_responsiveness":True},
    "Office - Visio":               {"extensions":["vsdx","vsd"],   "size_range":(50000,2000000),   "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"No", "dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes"},
    "PDF - Text":                   {"extensions":["pdf"],          "size_range":(50000,3000000),   "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes"},
    "PDF - Scanned":                {"extensions":["pdf"],          "size_range":(200000,8000000),  "images":"Yes","ocr_required":"Yes","native_produced":"Yes","redactable":"Image Only","analytics_eligible":"After OCR","dedup_method":"SHA256",     "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes"},
    "PDF - MIP Protected":          {"extensions":["pdf"],          "size_range":(50000,2000000),   "images":"Limited","ocr_required":"No","native_produced":"Limited","redactable":"No","analytics_eligible":"No","dedup_method":"SHA256",            "is_container":False,"supported":False,"has_natives":"Yes","has_images":"No","processing_error":"MIP Protected - Limited Extraction"},
    "Chat - Teams (RSMF)":          {"extensions":["rsmf"],         "size_range":(10000,800000),    "images":"Yes","ocr_required":"No", "native_produced":"No", "redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"EventCollectionId","is_container":False,"supported":True, "has_natives":"Yes","has_images":"No","rsmf_application":"Teams"},
    "Chat - Slack (RSMF)":          {"extensions":["rsmf"],         "size_range":(8000,500000),     "images":"Yes","ocr_required":"No", "native_produced":"No", "redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"EventCollectionId","is_container":False,"supported":True, "has_natives":"Yes","has_images":"No","rsmf_application":"Slack"},
    "Chat - SMS (RSMF)":            {"extensions":["rsmf"],         "size_range":(2000,50000),      "images":"Yes","ocr_required":"No", "native_produced":"No", "redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"EventCollectionId","is_container":False,"supported":True, "has_natives":"Yes","has_images":"No","rsmf_application":"SMS"},
    "Chat - WhatsApp (RSMF)":       {"extensions":["rsmf"],         "size_range":(3000,80000),      "images":"Yes","ocr_required":"No", "native_produced":"No", "redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"EventCollectionId","is_container":False,"supported":True, "has_natives":"Yes","has_images":"No","rsmf_application":"WhatsApp"},
    "Chat - Google Chat (RSMF)":    {"extensions":["rsmf"],         "size_range":(5000,200000),     "images":"Yes","ocr_required":"No", "native_produced":"No", "redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"EventCollectionId","is_container":False,"supported":True, "has_natives":"Yes","has_images":"No","rsmf_application":"Google Chat"},
    "Bloomberg XML":                {"extensions":["xml"],          "size_range":(10000,500000),    "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No"},
    "Image - JPEG":                 {"extensions":["jpg","jpeg"],   "size_range":(200000,8000000),  "images":"Yes","ocr_required":"Yes","native_produced":"Yes","redactable":"Image Only","analytics_eligible":"After OCR","dedup_method":"SHA256",     "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes","has_exif":True},
    "Image - HEIC":                 {"extensions":["heic"],         "size_range":(1000000,10000000),"images":"Yes","ocr_required":"Yes","native_produced":"Yes","redactable":"Image Only","analytics_eligible":"After OCR","dedup_method":"SHA256",     "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes","has_exif":True},
    "Image - PNG":                  {"extensions":["png"],          "size_range":(100000,5000000),  "images":"Yes","ocr_required":"Yes","native_produced":"Yes","redactable":"Image Only","analytics_eligible":"After OCR","dedup_method":"SHA256",     "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes","has_exif":False},
    "Image - TIFF":                 {"extensions":["tif","tiff"],   "size_range":(500000,20000000), "images":"Yes","ocr_required":"Yes","native_produced":"Yes","redactable":"Image Only","analytics_eligible":"After OCR","dedup_method":"SHA256",     "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes","has_exif":False},
    "Google Workspace - Document":  {"extensions":["docx"],         "size_range":(20000,600000),    "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No","google_doc_type":"DOCUMENT"},
    "Google Workspace - Spreadsheet":{"extensions":["xlsx"],        "size_range":(15000,1000000),   "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No","google_doc_type":"SPREADSHEET"},
    "Google Workspace - Presentation":{"extensions":["pptx"],       "size_range":(100000,5000000),  "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"Yes","google_doc_type":"PRESENTATION"},
    "Text / Markup":                {"extensions":["txt","rtf","html","csv","log"],"size_range":(1000,500000),"images":"Yes","ocr_required":"No","native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",  "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No"},
    "Source Code":                  {"extensions":["py","js","ts","java","sql","yaml","json"],"size_range":(500,200000),"images":"Yes","ocr_required":"No","native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256","is_container":False,"supported":True,"has_natives":"Yes","has_images":"No"},
    "Audio / Video":                {"extensions":["mp4","mp3","mov","wav","m4a"],"size_range":(500000,500000000),"images":"No","ocr_required":"No","native_produced":"Yes","redactable":"No","analytics_eligible":"No","dedup_method":"SHA256",        "is_container":False,"supported":False,"has_natives":"Yes","has_images":"No","viewer_supported":"No"},
    "Cellebrite Structured Excel":  {"extensions":["xlsx"],         "size_range":(20000,2000000),   "images":"Yes","ocr_required":"No", "native_produced":"Yes","redactable":"Image Only","analytics_eligible":"Yes","dedup_method":"SHA256",          "is_container":False,"supported":True, "has_natives":"Yes","has_images":"No"},
    "Container - ZIP":              {"extensions":["zip"],          "size_range":(10000,200000000), "images":"No","ocr_required":"No", "native_produced":"No", "redactable":"No","analytics_eligible":"No","dedup_method":"N/A",                       "is_container":True, "supported":True, "has_natives":"No","has_images":"No","date_unreliable":True},
    "Unsupported":                  {"extensions":["mdb","accdb","pages","numbers","key","olm"],"size_range":(5000,10000000),"images":"No","ocr_required":"No","native_produced":"Yes","redactable":"No","analytics_eligible":"No","dedup_method":"SHA256","is_container":False,"supported":False,"has_natives":"Yes","has_images":"No","processing_error":"Unsupported File Type"},
}

TIER_FILE_COUNTS = {
    "small": {
        "Email - MSG":600,"Email - EML":200,"Email Container - PST":6,"Email Container - MBOX":2,
        "Calendar - ICS":15,"Office - Word (DOCX)":150,"Office - Word (DOC)":50,
        "Office - Excel (XLSX)":80,"Office - Excel (XLS)":20,"Office - PowerPoint (PPTX)":40,
        "Office - PowerPoint (PPT)":10,"PDF - Text":80,"PDF - Scanned":12,"PDF - MIP Protected":3,
        "Chat - Teams (RSMF)":20,"Chat - Slack (RSMF)":10,"Image - JPEG":25,
        "Image - HEIC":10,"Image - PNG":10,"Image - TIFF":5,"Text / Markup":50,
        "Audio / Video":5,"Unsupported":15,"Container - ZIP":8,"Office - Visio":4,
    },
    "medium": {
        "Email - MSG":3900,"Email - EML":1300,"Email Container - PST":30,"Email Container - MBOX":10,
        "Calendar - ICS":150,"Office - Word (DOCX)":900,"Office - Word (DOC)":300,
        "Office - Excel (XLSX)":530,"Office - Excel (XLS)":170,"Office - PowerPoint (PPTX)":280,
        "Office - PowerPoint (PPT)":70,"PDF - Text":560,"PDF - Scanned":100,"PDF - MIP Protected":5,
        "Chat - Teams (RSMF)":300,"Chat - Slack (RSMF)":200,"Chat - SMS (RSMF)":60,
        "Chat - WhatsApp (RSMF)":30,"Chat - Google Chat (RSMF)":50,"Image - JPEG":180,
        "Image - HEIC":80,"Image - PNG":90,"Image - TIFF":50,
        "Google Workspace - Document":60,"Google Workspace - Spreadsheet":25,"Google Workspace - Presentation":15,
        "Text / Markup":250,"Source Code":50,"Audio / Video":30,"Cellebrite Structured Excel":20,
        "Container - ZIP":35,"Office - Visio":30,"Unsupported":100,
    },
    "large": {
        "Email - MSG":52500,"Email - EML":17500,"Email Container - PST":300,"Email Container - MBOX":100,
        "Calendar - ICS":2000,"Office - Word (DOCX)":11250,"Office - Word (DOC)":3750,
        "Office - Excel (XLSX)":7500,"Office - Excel (XLS)":2500,"Office - PowerPoint (PPTX)":4000,
        "Office - PowerPoint (PPT)":1000,"PDF - Text":8000,"PDF - Scanned":1700,"PDF - MIP Protected":15,
        "Chat - Teams (RSMF)":9000,"Chat - Slack (RSMF)":6000,"Chat - SMS (RSMF)":1500,
        "Chat - WhatsApp (RSMF)":700,"Chat - Google Chat (RSMF)":1500,"Bloomberg XML":1000,
        "Image - JPEG":2700,"Image - HEIC":1200,"Image - PNG":1500,"Image - TIFF":600,
        "Google Workspace - Document":1500,"Google Workspace - Spreadsheet":600,"Google Workspace - Presentation":400,
        "Text / Markup":3500,"Source Code":1500,"Audio / Video":500,"Cellebrite Structured Excel":300,
        "Container - ZIP":200,"Office - Visio":400,"Unsupported":1500,
    },
}

PRIVILEGE_REASONS = [
    "Attorney-Client Communication", "Work Product - Litigation Preparation",
    "Attorney-Client — Outside Counsel", "Work Product - Regulatory Response",
]
ECA_REASONS     = ["Date Out of Range","Domain Excluded - Opposing Counsel","No Keyword Hits","File Type Excluded","Domain Excluded - Personal","System File"]
PROC_ERRORS     = ["Password Protected","Corrupt File","Unsupported File Type","Extraction Failure","OCR Failure - Poor Scan Quality","Container Extraction Timeout","Teams Conversion Error","MIP Protected - Limited Extraction"]
CULL_REASONS    = ["NIST System File","Exact Duplicate","Near Duplicate","Below De Minimis"]
CAMERA_MAKES    = ["Apple","Samsung","Google","Apple","Apple"]
CAMERA_MODELS   = {"Apple":["iPhone 12 Pro","iPhone 13","iPhone 14 Pro Max"],"Samsung":["Galaxy S21","Galaxy S22"],"Google":["Pixel 6","Pixel 7"]}
PRODUCTS        = ["Oxycodone ER","Exalgo","Pennsaid","Subsys","Duexis","Xartemis XR"]
TERRITORIES     = ["Northeast","Southeast","Midwest","Southwest","Northwest","Mid-Atlantic","Gulf Coast","Great Lakes"]
ACCOUNTS        = ["Cardinal Health","McKesson","AmerisourceBergen","Walgreens","CVS Health","Express Scripts"]
MONTHS          = ["January","February","March","April","May","June","July","August","September","October","November","December"]
ROLES           = ["VP Sales","Compliance Officer","District Manager","CEO","Reimbursement Manager"]

# ── Helpers ───────────────────────────────────────────────────────────────

def fake_hash(bits=128):  return "%0*x" % (bits//4, random.getrandbits(bits))
def fake_message_id():    return "<%s.%s@mallinckrodt.com>" % (fake_hash(64), fake_hash(32))
def random_date(s, e):
    sd, ed = datetime.strptime(s,"%Y-%m-%d"), datetime.strptime(e,"%Y-%m-%d")
    return sd + timedelta(days=random.randint(0, max(0,(ed-sd).days)))
def fmt_dt(dt): return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""
def fmt_d(dt):  return dt.strftime("%Y-%m-%d") if dt else ""

def tar_score():
    b = random.random()
    if   b < 0.40: return round(random.uniform(0,20),2)
    elif b < 0.75: return round(random.uniform(75,100),2)
    else:          return round(random.uniform(20,75),2)

def expand(tmpl, dr):
    yr = random.randint(int(dr[0][:4]), int(dr[1][:4]))
    return (tmpl
            .replace("{q}",str(random.randint(1,4)))
            .replace("{year}",str(yr))
            .replace("{month}",random.choice(MONTHS))
            .replace("{territory}",random.choice(TERRITORIES))
            .replace("{product}",random.choice(PRODUCTS))
            .replace("{account}",random.choice(ACCOUNTS))
            .replace("{n}",str(random.randint(1,8)))
            .replace("{speaker}",random.choice(SPEAKER_NAMES).replace("Dr. ",""))
            .replace("{role}",random.choice(ROLES))
            .replace("{bates_range}","MNK00042100–MNK00043900"))

def assign_phase(custodian, tier_name):
    tier_weights = PHASE_WEIGHTS[tier_name]
    eligible = [p for p in tier_weights if p in custodian.get("phases_active",[1,2,3,4])]
    if not eligible: eligible = list(tier_weights.keys())
    weights = [tier_weights[p] for p in eligible]
    total = sum(weights)
    weights = [w/total for w in weights]
    return random.choices(eligible, weights=weights)[0]

def phase_date_range(phase, tier_dr):
    pd = NARRATIVE_PHASES[phase]
    ts, te = datetime.strptime(tier_dr[0],"%Y-%m-%d"), datetime.strptime(tier_dr[1],"%Y-%m-%d")
    ps, pe = datetime.strptime(pd["start"],"%Y-%m-%d"), datetime.strptime(pd["end"],"%Y-%m-%d")
    s, e   = max(ts,ps), min(te,pe)
    if s > e: s, e = ts, te
    return fmt_d(s), fmt_d(e)

# ── Document Builder ──────────────────────────────────────────────────────

def make_doc(ctrl, custodian, ft_name, ft_meta, tier_dr, all_custs, wf, phase, org):
    pdr    = phase_date_range(phase, tier_dr)
    date   = random_date(*pdr)
    ext    = random.choice(ft_meta["extensions"])
    size   = random.randint(*ft_meta["size_range"])

    is_email     = ft_name.startswith("Email -")
    is_calendar  = ft_name == "Calendar - ICS"
    is_rsmf      = "RSMF" in ft_name
    is_office    = ft_name.startswith("Office -") or ft_name.startswith("Google Workspace -")
    is_pdf       = ft_name.startswith("PDF")
    is_image     = ft_name.startswith("Image -")
    is_google    = ft_name.startswith("Google Workspace -")
    is_container = ft_meta.get("is_container", False)

    # Subject / Title (phase + org aware)
    subject_pool = (EMAIL_SUBJECTS_BY_ORG_PHASE.get((org, phase))
                    or EMAIL_SUBJECTS_BY_ORG_PHASE.get(("Mallinckrodt", phase))
                    or ["RE: {product} Update — {month} {year}"])
    title_pool   = OFFICE_TITLES_BY_PHASE.get(phase, OFFICE_TITLES_BY_PHASE[2])

    subject = expand(random.choice(subject_pool), tier_dr) if is_email or is_calendar else ""
    title   = expand(random.choice(title_pool),   tier_dr) if is_office and not is_email else ""

    # ICS — blank date sent (RULES.md Rule 4)
    date_sent = fmt_dt(date) if is_email else ""
    date_recv = fmt_dt(date + timedelta(minutes=random.randint(1,30))) if is_email else ""
    if is_calendar: date_sent = date_recv = ""

    # ZIP children — date gap (Rule 4)
    date_created = fmt_d(date)
    if ft_meta.get("date_unreliable") and random.random() < 0.30:
        date_created = "1980-01-01"

    # To/From
    to_cust  = random.choice(all_custs + [{"name": "DEA Diversion Control", "email": "diversion@dea.gov"},
                                           {"name": "FDA CDER",               "email": "cder@fda.hhs.gov"},
                                           {"name": "Ohio AG Office",          "email": "inquiry@ag.state.us"}])
    to_name  = to_cust.get("name","")
    to_email = to_cust.get("email","")

    # RSMF
    rsmf_app=rsmf_parts=rsmf_begin=rsmf_end=rsmf_evt=""; rsmf_msgs=0; rsmf_ph="No"
    if is_rsmf:
        rsmf_app   = ft_meta.get("rsmf_application","")
        participants = [custodian["name"]] + [c["name"] for c in random.sample(all_custs, min(3,len(all_custs)))]
        rsmf_parts = "; ".join(dict.fromkeys(participants))
        rsmf_msgs  = random.randint(5,120)
        rsmf_begin = fmt_dt(date)
        rsmf_end   = fmt_dt(date + timedelta(hours=random.randint(1,48)))
        rsmf_evt   = fake_hash(64)
        if ft_name == "Chat - Teams (RSMF)" and random.random() < 0.15: rsmf_ph = "Yes"

    # Image / EXIF
    gps_lat=gps_lon=gps_alt=camera_make=camera_model=date_taken=""
    if is_image and ft_meta.get("has_exif"):
        if random.random() < 0.15:
            gps_lat = round(random.uniform(-90,90),6)
            gps_lon = round(random.uniform(-180,180),6)
            gps_alt = round(random.uniform(0,500),1)
        mk = random.choice(CAMERA_MAKES)
        camera_make  = mk
        camera_model = random.choice(CAMERA_MODELS.get(mk,["Unknown"]))
        date_taken   = fmt_dt(date)

    # Google Workspace
    gdoc_id=gdoc_type=gshared=""
    if is_google:
        gdoc_id   = fake_hash(128)[:32]
        gdoc_type = ft_meta.get("google_doc_type","DOCUMENT")
        if random.random() < 0.20: gshared = "SDR-2847-MARKETING-SHARED"

    pages = random.randint(1,30) if is_pdf or "Word" in ft_name or "PowerPoint" in ft_name else random.randint(1,5)
    ocr_flag = "Yes" if ft_meta.get("ocr_required")=="Yes" else "No"
    viewer   = "No" if ft_meta.get("viewer_supported")=="No" else "Yes"

    bates_prefix = ORG_BATES_PREFIX.get(org, "MNK")

    return {
        "Control Number":          ctrl,
        "File Name":               f"{subject[:40].replace('/','_')}.{ext}" if is_email else f"{ctrl}.{ext}",
        "File Extension":          ext,
        "File Type Category":      ft_name,
        "File Size (bytes)":       size,
        "MD5 Hash":                fake_hash(128),
        "SHA256 Hash":             fake_hash(256),
        "Custodian":               custodian["name"],
        "Custodian Email":         custodian["email"],
        "Custodian Department":    custodian.get("dept",""),
        "Custodian Org":           org,
        "Narrative Phase":         phase,
        "Narrative Phase Name":    NARRATIVE_PHASES[phase]["name"],
        "Processing Folder Path":  f"\\\\Collection\\{custodian['name'].replace(' ','_')}\\{date.year}\\{date.strftime('%m')}",
        "Virtual Path":            f"{org}\\{custodian['name'].replace(' ','_')}\\{ft_name}\\{ctrl}.{ext}",
        "Container ID":            "",
        "Container Name":          "",
        "Level":                   "0" if is_container else "1",
        "Primary Date":            fmt_dt(date),
        "Sort Date":               fmt_dt(date),
        "Language":                "English",
        "Has Images":              ft_meta["has_images"],
        "Has Natives":             ft_meta["has_natives"],
        "OCR Flag":                ocr_flag,
        "Supported by Viewer":     viewer,
        "Extracted Text Preview":  "" if ft_meta.get("processing_error")=="MIP Protected - Limited Extraction" else f"[{ft_name}] {subject or title} — {custodian['name']} {fmt_d(date)}",
        "Images?":                 ft_meta["images"],
        "OCR Required?":           ft_meta["ocr_required"],
        "Native Produced?":        ft_meta["native_produced"],
        "Redactable?":             ft_meta["redactable"],
        "Analytics Eligible?":     ft_meta["analytics_eligible"],
        "Dedup Method":            ft_meta["dedup_method"],
        "Workflow Stage":          "",
        "Cull Reason":             "",
        "Processing Status":       "Error" if ft_meta.get("processing_error") else "Complete",
        "Processing Error Type":   ft_meta.get("processing_error",""),
        "Duplicate Spare":         "No",
        "ECA Exclusion Reason":    "",
        "Batch Name":              "",
        "Batch Status":            "",
        "Reviewer":                "",
        "Date First Assigned":     "",
        "Responsiveness":          "",
        "Privilege":               "",
        "Privilege Reason":        "",
        "Hot Doc":                 "No",
        "Issue Tags":              "",
        "Bates Begin":             "",
        "Bates End":               "",
        "Page Count":              pages,
        "Production Set":          "",
        "Bates Prefix":            bates_prefix,
        "Redacted":                "No",
        "Redaction Reason":        "",
        "TAR Score":               "",
        "AL Predicted Relevant":   "",
        "Email From":              custodian["name"] if is_email else "",
        "Email From SMTP":         custodian["email"] if is_email else "",
        "Email To":                to_name if is_email else "",
        "Email To SMTP":           to_email if is_email else "",
        "Email CC":                "",
        "Email CC SMTP":           "",
        "Email BCC":               "",
        "Email BCC SMTP":          "",
        "Email Subject":           subject,
        "Message ID":              fake_message_id() if is_email else "",
        "In Reply To":             "",
        "Date Sent":               date_sent,
        "Date Received":           date_recv,
        "Conversation Topic":      subject if is_email else "",
        "Conversation Index":      fake_hash(128) if is_email else "",
        "Has Attachments":         "Yes" if is_email and random.random()<0.35 else "No",
        "Attachment Count":        random.randint(1,4) if is_email and random.random()<0.35 else 0,
        "Email Thread ID":         "",
        "Email Threading Inclusive": "",
        "Importance":              random.choice(["Normal","Normal","Normal","High","Low"]) if is_email else "",
        "Parent Document ID":      "",
        "Family ID":               "",
        "Author":                  custodian["name"] if is_office else "",
        "Last Modified By":        custodian["name"] if is_office else "",
        "Date Created":            date_created,
        "Date Last Modified":      fmt_d(date + timedelta(days=random.randint(0,30))) if is_office else "",
        "Title":                   title,
        "Company":                 ORG_COMPANY_NAME.get(org,""),
        "Word Count":              random.randint(200,8000) if "Word" in ft_name else "",
        "Slide Count":             random.randint(5,45) if "PowerPoint" in ft_name else "",
        "Sheet Names":             "Sheet1; Sheet2" if "Excel" in ft_name else "",
        "PDF Author":              custodian["name"] if is_pdf else "",
        "PDF Creator":             random.choice(["Microsoft Word","Adobe Acrobat","Nuance PDF"]) if is_pdf else "",
        "PDF Producer":            "Adobe PDF Library" if is_pdf else "",
        "PDF Page Count":          pages if is_pdf else "",
        "Is Encrypted":            "No",
        "Is Form":                 random.choice(["Yes","No","No","No"]) if is_pdf else "",
        "Rsmf/Application":        rsmf_app,
        "Rsmf/Participants":       rsmf_parts,
        "Rsmf/MessageCount":       rsmf_msgs,
        "Rsmf/BeginDate":          rsmf_begin,
        "Rsmf/EndDate":            rsmf_end,
        "Rsmf/EventCollectionId":  rsmf_evt,
        "Rsmf/HasPlaceholders":    rsmf_ph,
        "Camera Make":             camera_make,
        "Camera Model":            camera_model,
        "Date Taken":              date_taken,
        "GPS Latitude":            gps_lat,
        "GPS Longitude":           gps_lon,
        "GPS Altitude":            gps_alt,
        "GoogleDrive/DocID":       gdoc_id,
        "GoogleDrive/DocumentType":gdoc_type,
        "GoogleDrive/SharedDriveID":gshared,
        "_force_privilege":        False,
    }

# ── Main Generator ────────────────────────────────────────────────────────

def generate(tier_name, out_dir, seed, edge_cases_on=False):
    random.seed(seed)
    wf     = WORKFLOW[tier_name]
    custs  = CUSTODIANS[tier_name]
    counts = TIER_FILE_COUNTS[tier_name]
    dr     = DATE_RANGES[tier_name]

    print(f"\n{'='*60}\n  MDL 2804 — {tier_name.upper()} tier\n  Output: {out_dir}\n  Seed:   {seed}\n{'='*60}")

    # ── Build organic documents ──
    all_docs = []
    doc_num  = 0
    for ft_name, count in counts.items():
        ft_meta = FILE_TYPES[ft_name]
        for _ in range(count):
            doc_num += 1
            cust  = random.choice(custs)
            phase = assign_phase(cust, tier_name)
            org   = cust.get("org", "Mallinckrodt")
            d = make_doc(f"DOC-{doc_num:07d}", cust, ft_name, ft_meta, dr, custs, wf, phase, org)
            all_docs.append(d)

    # ── Inject scripted hot documents ──
    scripted_hot_ids = set()
    for hd in SCRIPTED_HOT_DOCS:
        tiers_for = hd.get("tiers", ["small","medium","large"])
        if tier_name not in tiers_for:
            continue
        cust_name = hd["custodian_by_tier"].get(tier_name)
        cust = next((c for c in custs if c["name"] == cust_name), custs[0])
        org  = cust.get("org", hd.get("org", "Mallinckrodt"))

        # Make the base doc
        ft_name = hd["file_type"]
        ft_meta = FILE_TYPES[ft_name]
        d = make_doc(hd["control_number"], cust, ft_name, ft_meta, dr, custs, wf, hd["phase"], org)

        # Apply scripted overrides
        if hd.get("subject"):  d["Email Subject"] = hd["subject"]
        if hd.get("title"):    d["Title"] = hd["title"]; d["Extracted Text Preview"] = f"[{ft_name}] {hd['title']} — {cust['name']}"
        d["Hot Doc"]       = "Yes"
        d["Issue Tags"]    = hd["issue_tags"]
        d["Primary Date"]  = f"{hd['date']} 09:00:00"
        d["Sort Date"]     = d["Primary Date"]
        d["Workflow Stage"] = "Review: Reviewed"
        d["Responsiveness"] = "Responsive"
        if hd.get("privilege"):
            d["_force_privilege"]  = True
            d["Privilege"]         = "Privileged"
            d["Privilege Reason"]  = hd["privilege"]
        scripted_hot_ids.add(hd["control_number"])
        all_docs.append(d)

    print(f"  Total documents: {len(all_docs):,} ({len(scripted_hot_ids)} scripted hot docs)")

    # ── Workflow stage assignment ──
    # Rough stage buckets based on index position in shuffled list
    random.shuffle(all_docs)
    total  = len(all_docs)
    n_dup  = int(total * 0.10)
    n_err  = int(total * 0.07)
    n_eca  = int(total * (0.33 if tier_name=="small" else 0.43 if tier_name=="medium" else 0.45))

    for i, d in enumerate(all_docs):
        if d["Control Number"] in scripted_hot_ids:
            continue  # already set
        if i < n_dup:
            d["Workflow Stage"] = "Pre-Review: Duplicate/NIST"
            d["Cull Reason"]    = random.choice(CULL_REASONS)
            d["Duplicate Spare"] = "Yes"
        elif i < n_dup + n_err:
            d["Workflow Stage"]        = "Pre-Review: Processing Error"
            d["Processing Status"]     = "Error"
            d["Processing Error Type"] = d["Processing Error Type"] or random.choice(PROC_ERRORS)
        elif i < n_dup + n_err + n_eca:
            d["Workflow Stage"]       = "ECA: Excluded"
            d["ECA Exclusion Reason"] = random.choice(ECA_REASONS)
        else:
            r = random.random()
            if   r < 0.65: d["Workflow Stage"] = "Review: Reviewed"
            elif r < 0.85: d["Workflow Stage"] = "Review: In Progress"
            else:          d["Workflow Stage"] = "Review: Queued"

    # ── Phase-aware responsiveness, privilege, TAR ──
    reviewed = [d for d in all_docs if d["Workflow Stage"] == "Review: Reviewed"]
    for d in reviewed:
        if d["Control Number"] in scripted_hot_ids:
            continue  # already Responsive
        phase = d.get("Narrative Phase", 2)
        r = random.random()
        resp_thresh = PHASE_RESPONSIVE_PCT.get(phase, 0.30)
        if   r < resp_thresh:        d["Responsiveness"] = "Responsive"
        elif r < resp_thresh + 0.07: d["Responsiveness"] = "Not Sure"
        else:                        d["Responsiveness"] = "Non-Responsive"

    # Privilege (phase-aware)
    for d in reviewed:
        if d["Responsiveness"] != "Responsive": continue
        if d.get("_force_privilege"): continue
        phase = d.get("Narrative Phase", 2)
        if random.random() < PHASE_PRIVILEGE_PCT.get(phase, 0.10):
            d["Privilege"]        = "Privileged"
            d["Privilege Reason"] = random.choice(PRIVILEGE_REASONS)

    # TAR scores (bimodal — full review population, Rule 7)
    for d in reviewed:
        score = tar_score()
        d["TAR Score"]            = score
        d["AL Predicted Relevant"] = "Yes" if score >= 50 else "No"

    # Issue tags (matrix-based)
    for d in reviewed:
        if d["Responsiveness"] == "Responsive" and not d.get("Issue Tags"):
            org   = d.get("Custodian Org", "Mallinckrodt")
            phase = d.get("Narrative Phase", 2)
            pool  = ISSUE_TAG_MATRIX.get((org, phase), ISSUE_TAGS_FALLBACK)
            n     = 2 if random.random() < 0.40 else 1
            d["Issue Tags"] = "; ".join(random.sample(pool, min(n, len(pool))))

    # Hot docs (organic — small subset of non-scripted responsive docs)
    organic_resp = [d for d in reviewed if d["Responsiveness"]=="Responsive" and d["Control Number"] not in scripted_hot_ids and not d.get("Privilege")]
    n_hot = max(0, int(len(organic_resp) * wf["hot_pct"]) - len(scripted_hot_ids))
    for d in random.sample(organic_resp, min(n_hot, len(organic_resp))):
        d["Hot Doc"] = "Yes"

    # Bates + production
    bates_n = {pfx: 1 for pfx in ORG_BATES_PREFIX.values()}
    produced_by_org = {}
    for d in reviewed:
        if d["Responsiveness"]=="Responsive" and d["Privilege"]!="Privileged":
            org = d.get("Custodian Org","Mallinckrodt")
            pfx = ORG_BATES_PREFIX.get(org,"MNK")
            produced_by_org.setdefault(pfx, []).append(d)
    for pfx, docs in produced_by_org.items():
        n_red = int(len(docs) * wf["redacted_pct"])
        red_set = set(id(d) for d in random.sample(docs, min(n_red, len(docs))))
        for d in docs:
            bb = f"{pfx}{bates_n[pfx]:08d}"
            be = f"{pfx}{bates_n[pfx]+int(d['Page Count'])-1:08d}"
            bates_n[pfx] += int(d["Page Count"])
            d["Bates Begin"] = bb; d["Bates End"] = be
            d["Production Set"] = f"VOL{random.randint(1,wf['productions']):03d}"
            if id(d) in red_set:
                d["Redacted"]        = "Yes"
                d["Redaction Reason"] = random.choice(["PII - Patient Information","Privilege - Partial","Privacy - Third Party"])

    # ── Email families (organic + scripted) ──
    email_docs = [d for d in all_docs if d["File Type Category"] in ("Email - MSG","Email - EML")]
    print(f"  Building email families ({len(email_docs):,} emails)...")
    families = []
    fam_id = thr_id = 0

    # Scripted threads first — build O(1) lookup to avoid scanning all_docs per call
    doc_by_ctrl = {d["Control Number"]: d for d in all_docs}

    def find_or_stub(ctrl, msg, all_docs, custs, dr, wf, tier_name):
        existing = doc_by_ctrl.get(ctrl)
        if existing: return existing
        cust_name = msg["from_name_tier"].get(tier_name, custs[0]["name"])
        cust = next((c for c in custs if c["name"]==cust_name), custs[0])
        org  = cust.get("org","Mallinckrodt")
        d = make_doc(ctrl, cust, "Email - MSG", FILE_TYPES["Email - MSG"], dr, custs, wf, msg["phase"], org)
        d["Email Subject"]  = msg["subject"]
        d["Primary Date"]   = f"{msg['date']} 09:00:00"
        d["Sort Date"]      = d["Primary Date"]
        d["Workflow Stage"] = "Review: Reviewed"
        d["Responsiveness"] = "Responsive"
        d["Issue Tags"]     = msg.get("issue_tags","")
        if msg.get("privilege"):
            d["Privilege"]        = "Privileged"
            d["Privilege Reason"] = msg["privilege"]
            d["_force_privilege"] = True
        all_docs.append(d)
        doc_by_ctrl[ctrl] = d
        return d

    for thread in SCRIPTED_THREADS:
        if tier_name not in thread.get("tiers",["small","medium","large"]): continue
        msgs     = thread["messages"]
        parent_d = find_or_stub(msgs[0]["ctrl"], msgs[0], all_docs, custs, dr, wf, tier_name)
        sfam     = thread["family_id"]; sthr = thread["thread_id"]
        children_ids = []
        parent_d["Family ID"] = sfam; parent_d["Email Thread ID"] = sthr
        parent_d["Email Threading Inclusive"] = "No"
        for j, msg in enumerate(msgs[1:], 1):
            child_d = find_or_stub(msg["ctrl"], msg, all_docs, custs, dr, wf, tier_name)
            child_d["Family ID"]     = sfam
            child_d["Email Thread ID"] = sthr
            child_d["Parent Document ID"] = parent_d["Control Number"]
            child_d["In Reply To"]   = parent_d.get("Message ID","")
            child_d["Email Threading Inclusive"] = "Yes" if msg.get("inclusive") else "No"
            children_ids.append(child_d["Control Number"])
        families.append({"family_id":sfam,"thread_id":sthr,"parent_doc_id":parent_d["Control Number"],
                         "children":children_ids,"subject":msgs[0]["subject"],"family_size":len(msgs),"scripted":True})

    # Organic email threading
    organic_emails = [d for d in email_docs if d.get("Family ID","") == ""]
    n_standalone   = int(len(organic_emails) * 0.22)
    random.shuffle(organic_emails)
    standalone  = organic_emails[:n_standalone]
    threaded    = organic_emails[n_standalone:]

    for d in standalone:
        fam_id += 1
        fk = f"FAM-{fam_id:06d}"
        d["Family ID"] = fk; d["Email Thread ID"] = ""; d["Email Threading Inclusive"] = "Yes"
        families.append({"family_id":fk,"thread_id":None,"parent_doc_id":d["Control Number"],
                         "children":[],"subject":d.get("Email Subject",""),"family_size":1})

    i = 0
    while i < len(threaded):
        fam_id += 1; thr_id += 1
        sz    = random.choices([2,3,4,5,6,8],weights=[20,25,20,15,10,10])[0]
        group = threaded[i:i+sz]; i += sz
        fk = f"FAM-{fam_id:06d}"; tk = f"THR-{thr_id:06d}"
        parent = group[0]
        inclusive_idx = random.randint(max(0,len(group)-2), len(group)-1)
        for j, d in enumerate(group):
            d["Family ID"] = fk; d["Email Thread ID"] = tk
            d["Parent Document ID"]      = "" if j==0 else parent["Control Number"]
            d["Email Threading Inclusive"] = "Yes" if j==inclusive_idx else "No"
            if j > 0:
                d["In Reply To"]   = parent.get("Message ID","")
                d["Email Subject"] = "RE: " + parent.get("Email Subject","").lstrip("RE: ").lstrip("FW: ")
        families.append({"family_id":fk,"thread_id":tk,"parent_doc_id":parent["Control Number"],
                         "children":[d["Control Number"] for d in group[1:]],"subject":parent.get("Email Subject",""),"family_size":len(group)})

    # ── Batches ──
    batch_sets = {
        "small":  [("First Pass Review",0.85),("QC Review",0.15)],
        "medium": [("First Pass Review",0.70),("Privilege Review",0.15),("QC Review",0.10),("Hot Docs",0.05)],
        "large":  [("First Pass Review",0.60),("Privilege Review",0.15),("QC Review",0.12),("Hot Docs",0.05),("Second Pass",0.05),("Clawback Review",0.03)],
    }[tier_name]
    reviewer_pool = {
        "small":  ["Jordan Lee","Sam Rivera","Taylor Kim"],
        "medium": ["Jordan Lee","Sam Rivera","Taylor Kim","Morgan Chen","Alex Patel","Casey Wu"],
        "large":  ["Jordan Lee","Sam Rivera","Taylor Kim","Morgan Chen","Alex Patel","Casey Wu",
                   "Riley Zhao","Devon Scott","Avery Nguyen","Quinn Torres","Blake Fisher","Skylar Osei","Jamie Brooks"],
    }[tier_name]

    batches  = []; batch_id = 0
    bsz_min, bsz_max = (150,350) if tier_name=="small" else (200,500) if tier_name=="medium" else (300,800)
    rev_pool = reviewed[:]; random.shuffle(rev_pool); cursor = 0
    for bset, pct in batch_sets:
        bdocs = rev_pool[cursor:cursor+int(len(rev_pool)*pct)]; cursor += len(bdocs)
        j = 0
        while j < len(bdocs):
            batch_id += 1; bsz = random.randint(bsz_min,bsz_max); batch = bdocs[j:j+bsz]; j += bsz
            rev    = random.choice(reviewer_pool)
            status = random.choices(["Completed","In Progress","Not Started"],weights=[70,20,10])[0]
            adate  = random_date("2018-09-01","2019-03-01")
            cdate  = adate + timedelta(days=random.randint(3,14)) if status=="Completed" else None
            bname  = f"{bset[:4].upper()}-{batch_id:04d}"
            for d in batch: d["Batch Name"]=bname; d["Batch Status"]=status; d["Reviewer"]=rev; d["Date First Assigned"]=fmt_d(adate)
            batches.append({"batch_name":bname,"batch_set":bset,"status":status,"reviewer":rev,
                            "doc_count":len(batch),"date_assigned":fmt_d(adate),"date_completed":fmt_d(cdate),
                            "document_ids":[d["Control Number"] for d in batch]})

    # ── Edge cases (opt in) ──
    # Applied last, on its own RNG stream, so the default output is byte-identical
    # and the committed tiers plus the CI determinism check are unaffected.
    edge_report = None
    if edge_cases_on:
        import edge_cases as edge
        edge_report = edge.apply(all_docs, families, custs, seed)
        affected = sum(len(v) for v in edge_report.values())
        print(f"\n  Edge cases applied: {affected:,} documents across "
              f"{len(edge_report)} scenarios")

    # ── Write outputs ──
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Remove internal field before writing
    for d in all_docs:
        d.pop("_force_privilege", None)

    docs_path = os.path.join(out_dir,"documents.csv")
    with open(docs_path,"w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_docs[0].keys()))
        writer.writeheader(); writer.writerows(all_docs)
    print(f"  Written {docs_path} ({os.path.getsize(docs_path)/1e6:.1f} MB, {len(all_docs):,} docs)")

    outputs = [
        ("custodians.json",     [{**c,"actual_doc_count":sum(1 for d in all_docs if d["Custodian"]==c["name"])} for c in custs]),
        ("email-families.json", families),
        ("batches.json",        batches),
    ]
    if edge_report is not None:
        import edge_cases as edge
        outputs.append(("edge-cases.json", {
            "note": "Documents deliberately starved of an input. They process cleanly; "
                    "the question is what a feature does with them.",
            "scenarios": {k: {"starves": edge.STARVES.get(k,""), "count": len(v), "documents": v}
                          for k, v in edge_report.items()},
        }))
    for fname, data in outputs:
        path = os.path.join(out_dir, fname)
        with open(path,"w") as f: json.dump(data, f, indent=2)
        print(f"  Written {path}")

    # Summary
    resp  = sum(1 for d in all_docs if d.get("Responsiveness")=="Responsive")
    priv  = sum(1 for d in all_docs if d.get("Privilege")=="Privileged")
    hot   = sum(1 for d in all_docs if d.get("Hot Doc")=="Yes")
    prod  = sum(1 for d in all_docs if d.get("Bates Begin","")!="")
    print(f"\n  Story summary:")
    print(f"    Reviewed:   {len(reviewed):,}   Responsive: {resp:,}   Privileged: {priv:,}")
    print(f"    Hot docs:   {hot:,} ({len(scripted_hot_ids)} scripted)   Produced: {prod:,}")
    print(f"    Families:   {len(families):,}   Batches: {len(batches)}")
    print(f"\n  Done — {tier_name} tier written to {out_dir}")


def main():
    p = argparse.ArgumentParser(description="Generate MDL 2804 OIDA Relativity mock data")
    p.add_argument("--tier",  required=True, choices=["small","medium","large"])
    p.add_argument("--out",   default=None)
    p.add_argument("--seed",  type=int, default=DEFAULT_SEED)
    p.add_argument("--edge-cases", action="store_true",
                   help="Starve a slice of documents of custodian, date, text, or family "
                        "so the failure paths of aggregating features can be tested. "
                        "Off by default; the default output is byte-identical without it.")
    args = p.parse_args()
    generate(args.tier, args.out or os.path.join("mock-data", args.tier), args.seed,
             args.edge_cases)

if __name__ == "__main__":
    main()
