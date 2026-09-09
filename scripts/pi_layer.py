#!/usr/bin/env python3
"""
pi_layer.py — Personal information, where it actually lives

RULES.md Rule 16. Nothing in the generated tiers carries personal information, so
PI Detect could only ever be tested by starving it (Rule 13's no_extracted_text) or
by hand-editing a native. A widget whose whole job is finding PI has never been run
against a corpus that has any.

Two things matter more than volume:

  * **Distribution.** PI concentrated in one spreadsheet is the easy case. Most of
    the instances here sit in email bodies, which is where it really accumulates
    and the harder catch, and the rest spread across a roster, a form and a chat.
  * **Irrelevance.** One document is dense with PI and has nothing to do with the
    matter, so the widget has to surface something nobody asked about.

Every value is non-issuable or a published test value. Nothing here can collide
with a real person:

  * SSN — area 900-999, which the SSA has never issued. `--ssn-range 666` switches
    to area 666, also never allocated, for detectors that score the 9xx block low.
  * Payment cards — the standard published test numbers.
  * Phones — the 555-01xx block, reserved for fiction.
  * Email — the reserved `.invalid` TLD, which cannot resolve.

The ground truth is emitted at generation time as one row per instance, so it can be
diffed straight against a PI Detect export. The native text is rendered *from* those
rows by `render`, so the corpus and its ground truth cannot drift apart.
"""

import random

# Documents per scenario per tier. Counted, not sampled: the ground truth is exact.
SCENARIOS = {
    "email_body_ssn":              {"small": 6, "medium": 30, "large": 300},
    "email_body_card":             {"small": 3, "medium": 15, "large": 150},
    "spreadsheet_roster":          {"small": 2, "medium": 8,  "large": 60},
    "benefits_form_pdf":           {"small": 3, "medium": 12, "large": 90},
    "chat_phone_numbers":          {"small": 3, "medium": 12, "large": 90},
    "irrelevant_high_sensitivity": {"small": 1, "medium": 2,  "large": 4},
}

WHERE = {
    "email_body_ssn":              "email body",
    "email_body_card":             "email body",
    "spreadsheet_roster":          "spreadsheet cells",
    "benefits_form_pdf":           "pdf body",
    "chat_phone_numbers":          "chat message",
    "irrelevant_high_sensitivity": "document body",
}

# Which file types each scenario can land on. A roster in an .eml is not a roster.
TYPES = {
    "email_body_ssn":              ("Email -",),
    "email_body_card":             ("Email -",),
    "spreadsheet_roster":          ("Office - Excel",),
    "benefits_form_pdf":           ("PDF",),
    "chat_phone_numbers":          ("Chat -",),
    "irrelevant_high_sensitivity": ("Office - Word", "PDF"),
}

# Published test card numbers. These are the numbers the card networks hand out for
# exactly this purpose; none of them is a live account.
TEST_CARDS = [
    ("Visa",             "4111 1111 1111 1111"),
    ("Visa",             "4012 8888 8888 1881"),
    ("Mastercard",       "5555 5555 5555 4444"),
    ("Mastercard",       "5105 1051 0510 5100"),
    ("American Express", "3782 822463 10005"),
    ("Discover",         "6011 1111 1111 1117"),
]

SSN_RANGES = {
    # label → (area low, area high, why it is safe)
    "9xx": (900, 999, "the SSA has never issued an area number above 899"),
    "666": (666, 666, "the SSA has never allocated area number 666"),
}
DEFAULT_SSN_RANGE = "9xx"

# The 9xx block is genuinely never-issued, and that is exactly why some detectors
# score it as low confidence and a widget can appear to under-report.
SSN_CAVEAT = {
    "9xx": "area 900-999 is never issued, and some detectors score it low confidence. "
           "Rebuild with --ssn-range 666 to test a standard-format area instead.",
    "666": "area 666 is never allocated but scores as a standard-format SSN.",
}

# Names that appear nowhere in the custodian roster or the narrative, so a planted
# SSN can never be read as a fact about a person in the story.
PI_NAMES = [
    "Dana Whitlock", "Marcus Feeney", "Priya Raman", "Colin Ashworth",
    "Teresa Vance", "Omar Haddad", "Nina Petrov", "Grant Mueller",
    "Alice Okonkwo", "Ruben Cortes", "Hana Sato", "Devon Mbeki",
    "Karin Lindqvist", "Sofia Duarte", "Ethan Boyle", "Maya Tran",
]

# 555-01xx is the block reserved for fiction, and these area codes place the
# numbers where the custodians actually sit.
AREA_CODES = ["314", "212", "602", "617"]

CARRIERS = ["Meridian Health Plan", "Northgate Benefit Administrators",
            "Cordell Mutual", "Baywood Insurance Services"]


def _ssn(rng, ssn_range):
    lo, hi = SSN_RANGES[ssn_range][:2]
    return f"{rng.randint(lo, hi):03d}-{rng.randint(1, 99):02d}-{rng.randint(1, 9999):04d}"


def _phone(rng):
    return f"({rng.choice(AREA_CODES)}) 555-01{rng.randint(0, 99):02d}"


def _personal_email(rng, name):
    first, last = name.lower().split()[0], name.lower().split()[-1]
    return f"{first}.{last}@{rng.choice(['mailbox', 'homemail', 'personal'])}.invalid"


def _dob(rng):
    return f"{rng.randint(1, 12):02d}/{rng.randint(1, 28):02d}/{rng.randint(1955, 1992)}"


def _instance(doc, scenario, pi_type, value, ssn_range, subject=""):
    caveat = SSN_CAVEAT[ssn_range] if pi_type == "SSN" else ""
    return {
        "Control Number":     doc["Control Number"],
        "Custodian":          doc.get("Custodian", ""),
        "Scenario":           scenario,
        "PI Type":            pi_type,
        "Where It Lives":     WHERE[scenario],
        "Subject":            subject,
        "Value":              value,
        "Expected To Detect": "maybe" if pi_type == "SSN" and ssn_range == "9xx" else "yes",
        "Caveat":             caveat,
    }


def apply(all_docs, tier_name, seed=42, ssn_range=DEFAULT_SSN_RANGE):
    """Mutate `all_docs` in place, adding the `PI Seeded` column to every row.

    Returns the ground-truth rows, one per PI instance.
    """
    rng = random.Random(seed ^ 0x5C11)        # own stream: never perturbs default output
    for d in all_docs:
        d.setdefault("PI Seeded", "")

    def pool_for(scenario):
        prefixes = TYPES[scenario]
        # The irrelevant document gets recoded Non-Responsive, so it cannot be one
        # that was already produced: a document with a Bates number is responsive
        # by definition (Rule 10).
        unproduced = scenario == "irrelevant_high_sensitivity"
        return [d for d in all_docs
                if not (unproduced and (d.get("Bates Begin", "")
                                        or d.get("Privilege", "") == "Privileged"))
                and not d["Control Number"].startswith("HOT-")
                and str(d.get("Level", "")) != "0"
                and d.get("Has Natives", "") != "No"
                and not d.get("PI Seeded")
                and d.get("Language", "English") == "English"
                and d.get("File Type Category", "").startswith(prefixes)
                and (d.get("Processing Error Type", "") or "").strip() == ""]

    rows: list[dict] = []
    for scenario, per_tier in SCENARIOS.items():
        want = per_tier.get(tier_name, per_tier["small"])
        pool = pool_for(scenario)
        rng.shuffle(pool)
        for doc in pool[:want]:
            rows.extend(_seed_document(doc, scenario, rng, ssn_range))
    return rows


def _seed_document(doc, scenario, rng, ssn_range):
    """Seed one document. Sets `PI Seeded`; returns that document's instances."""
    out = []
    if scenario == "email_body_ssn":
        name = rng.choice(PI_NAMES)
        out.append(_instance(doc, scenario, "SSN", _ssn(rng, ssn_range), ssn_range, name))
        out.append(_instance(doc, scenario, "Date of Birth", _dob(rng), ssn_range, name))

    elif scenario == "email_body_card":
        brand, number = rng.choice(TEST_CARDS)
        out.append(_instance(doc, scenario, "Payment Card", number, ssn_range, brand))

    elif scenario == "spreadsheet_roster":
        for name in rng.sample(PI_NAMES, rng.randint(8, 14)):
            out.append(_instance(doc, scenario, "SSN", _ssn(rng, ssn_range), ssn_range, name))
            out.append(_instance(doc, scenario, "Phone", _phone(rng), ssn_range, name))
            out.append(_instance(doc, scenario, "Personal Email",
                                 _personal_email(rng, name), ssn_range, name))

    elif scenario == "benefits_form_pdf":
        name = rng.choice(PI_NAMES)
        out.append(_instance(doc, scenario, "SSN", _ssn(rng, ssn_range), ssn_range, name))
        out.append(_instance(doc, scenario, "Date of Birth", _dob(rng), ssn_range, name))
        out.append(_instance(doc, scenario, "Phone", _phone(rng), ssn_range, name))

    elif scenario == "chat_phone_numbers":
        for name in rng.sample(PI_NAMES, rng.randint(2, 4)):
            out.append(_instance(doc, scenario, "Phone", _phone(rng), ssn_range, name))

    elif scenario == "irrelevant_high_sensitivity":
        name = rng.choice(PI_NAMES)
        out.append(_instance(doc, scenario, "SSN", _ssn(rng, ssn_range), ssn_range, name))
        out.append(_instance(doc, scenario, "Date of Birth", _dob(rng), ssn_range, name))
        out.append(_instance(doc, scenario, "Phone", _phone(rng), ssn_range, name))
        out.append(_instance(doc, scenario, "Personal Email",
                             _personal_email(rng, name), ssn_range, name))
        out.append(_instance(doc, scenario, "Member ID",
                             f"MBR-{rng.randint(10**7, 10**8 - 1)}", ssn_range,
                             rng.choice(CARRIERS)))
        # The point of this one: high sensitivity, zero relevance. A reviewer who
        # opens it learns nothing about the matter and still has to act on it.
        doc["Responsiveness"] = "Non-Responsive" if doc.get("Responsiveness") else ""
        doc["Issue Tags"]     = ""
        doc["Title"]          = "Explanation of Benefits — Claim Summary"

    doc["PI Seeded"] = "; ".join(dict.fromkeys(r["PI Type"] for r in out))
    return out


# ── Rendering: the native text is built from the ground truth, never beside it ──

def render(rows):
    """Text and spreadsheet rows for one document, from its ground-truth rows.

    The load package builder calls this. Deriving the native's content from the
    same rows a tester diffs against is what keeps the two from drifting.
    """
    scenario = rows[0]["Scenario"]
    by_subject: dict[str, dict[str, str]] = {}
    for r in rows:
        by_subject.setdefault(r["Subject"], {})[r["PI Type"]] = r["Value"]

    if scenario == "email_body_ssn":
        name, vals = next(iter(by_subject.items()))
        return {"text": (
            f"Adding this to the benefits file before Friday.\n\n"
            f"{name}\nSSN: {vals.get('SSN','')}\nDOB: {vals.get('Date of Birth','')}\n\n"
            f"Let me know if payroll needs anything else from my side."), "rows": []}

    if scenario == "email_body_card":
        brand, vals = next(iter(by_subject.items()))
        return {"text": (
            f"Use the corporate card for the registration, the PO will not clear in time.\n\n"
            f"{brand} {vals.get('Payment Card','')}\n\n"
            f"Forward the receipt to me and I will code it."), "rows": []}

    if scenario == "spreadsheet_roster":
        out = [["Employee", "SSN", "Phone", "Personal Email"]]
        for name, vals in by_subject.items():
            out.append([name, vals.get("SSN", ""), vals.get("Phone", ""),
                        vals.get("Personal Email", "")])
        return {"text": "", "rows": out, "sheet": "Roster"}

    if scenario == "benefits_form_pdf":
        name, vals = next(iter(by_subject.items()))
        return {"text": (
            f"EMPLOYEE BENEFIT ELECTION FORM\n\n"
            f"Name: {name}\nSocial Security Number: {vals.get('SSN','')}\n"
            f"Date of Birth: {vals.get('Date of Birth','')}\n"
            f"Daytime Phone: {vals.get('Phone','')}\n\n"
            f"Signature on file. Return the completed form to Human Resources."), "rows": []}

    if scenario == "chat_phone_numbers":
        lines = [f"{name}: {vals.get('Phone','')}" for name, vals in by_subject.items()]
        return {"text": "Numbers for the on-call list:\n" + "\n".join(lines), "rows": []}

    if scenario == "irrelevant_high_sensitivity":
        person = next((s for s in by_subject if "SSN" in by_subject[s]), "")
        vals   = by_subject.get(person, {})
        carrier = next((s for s in by_subject if "Member ID" in by_subject[s]), "")
        member  = by_subject.get(carrier, {}).get("Member ID", "")
        return {"text": (
            f"{carrier}\nEXPLANATION OF BENEFITS — THIS IS NOT A BILL\n\n"
            f"Member: {person}\nMember ID: {member}\n"
            f"Social Security Number: {vals.get('SSN','')}\n"
            f"Date of Birth: {vals.get('Date of Birth','')}\n"
            f"Phone: {vals.get('Phone','')}\n"
            f"Email: {vals.get('Personal Email','')}\n\n"
            f"Your claim has been processed. The amount shown as patient responsibility "
            f"reflects your plan's deductible. Keep this statement for your records.\n\n"
            f"Questions about this statement should go to Member Services."), "rows": []}

    return {"text": "", "rows": []}


GROUND_TRUTH_COLUMNS = ["Control Number", "Custodian", "Scenario", "PI Type",
                        "Where It Lives", "Subject", "Value",
                        "Expected To Detect", "Caveat"]
