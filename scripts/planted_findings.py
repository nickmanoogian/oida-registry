#!/usr/bin/env python3
"""
planted_findings.py — Known-answer findings, one per detection method

RULES.md Rule 18. The thirteen scripted hot documents are all the same kind of
finding: surface the document, read it, and the story is on the page. That tests
review. It cannot test the claim early case assessment actually makes, which is
about what metadata surfaces *before* anyone reads anything.

So each tier plants a matched pair and a decoy:

  1. **metadata_only** — a single outbound message to an address that appears
     exactly once in the corpus, carrying an encrypted attachment. There is nothing
     to read: the body is two words and the attachment will not open. Findable on
     the communication pattern alone.
  2. **content_only** — a document with zero hits against any matter keyword, naming
     no company, no file and no person in full. No filter reaches it. Findable only
     by reading it.
  3. **decoy** — the same metadata shape as the principal, and innocent. The
     distinguisher is a second record showing who the address belongs to, which
     you only reach by walking the entity rather than by reading the first document.
  4. **buried_deep** — the relevant sentence sits on the eleventh tab of a twelve
     tab workbook, so shallow extraction misses it and reports the document clean.

Emitted at generation time as findings.json, with the expected answer and how to
verify it, so a tester can tell a product bug from a data artifact.
"""

import random

# What a reviewer would actually put in the search box on this matter. The
# content_only finding must not hit any of them, and the validator enforces it.
MATTER_KEYWORDS = [
    "som", "suspicious order", "override", "opioid", "oxycodone", "fentanyl",
    "subsys", "dea", "diversion", "speaker bureau", "prior authorization",
    "prior auth", "subpoena", "whistleblower", "legal hold", "quota",
    "mallinckrodt", "insys", "mckinsey", "cardinal", "mdl", "kol",
]

# The principal's counterparty. The domain is invented and reserved: .invalid
# cannot resolve, so the address can never reach a real mailbox.
PRINCIPAL_ADDRESS = ("M. Delacroix", "m.delacroix@harbor-line-consulting.invalid")

# The decoy's counterparty, and the record that explains it.
DECOY_ADDRESS = ("R. Okafor", "r.okafor@ledgerline-assurance.invalid")

CONTENT_ONLY_BODY = """Notes from Thursday.

He was clear that the number should not move again before the end of the quarter,
and that nobody outside the room needs to see the working. I said I would keep my
own copy of the earlier version. J. will take the part that touches the field team,
so it stays out of my folder.

If anyone asks later, the decision was made in the room and not in writing. That
was the point of doing it that way.

I am not putting the rest of this in an email."""

METADATA_ONLY_BODY = "Per our call. Attached."

DECOY_BODY = "As discussed. Attached, same password as last time."

DECOY_EXPLAINER_BODY = """Confirming the walkthrough for Thursday at 2pm.

Our external assurance provider will attend. Their engagement letter for the
internal controls review is on file with the finance team, and the working papers
come back to us encrypted as usual. Nothing in scope for the litigation hold.

Please have the reconciliation ready."""

# The workbook whose relevant sentence sits on a late tab.
BURIED_SHEETS = ["Summary", "Q1", "Q2", "Q3", "Q4", "Territory Detail",
                 "Rebates", "Chargebacks", "Adjustments", "Notes",
                 "Reconciliation", "Change Log"]
BURIED_SHEET = "Reconciliation"
BURIED_PAYLOAD = [
    ["Row", "Order", "Account", "Note"],
    ["41", "SO-114872", "Butner NC cluster",
     "Released without documented justification — flag cleared manually"],
    ["42", "SO-114910", "Butner NC cluster",
     "Released without documented justification — flag cleared manually"],
    ["43", "SO-115003", "Chillicothe OH",
     "Threshold raised after release, no approval on file"],
]


def _pick(rng, pool):
    return pool[rng.randrange(len(pool))] if pool else None


def _outbound_email_with_no_attachments(all_docs, custodian_name):
    return [d for d in all_docs
            if d.get("Record Type") == "Email"
            and d.get("Custodian") == custodian_name
            and d.get("Email From SMTP")
            and d.get("Has Attachments") == "No"
            and int(d.get("Attachment Count") or 0) == 0
            and not d["Control Number"].startswith("HOT-")
            and not d.get("Email Thread ID")
            and not d.get("PI Seeded")
            and d.get("Language", "English") == "English"]


def _loose_edoc(all_docs, custodian_name):
    return [d for d in all_docs
            if d.get("Record Type") == "EDoc"
            and d.get("Custodian") == custodian_name
            and not d.get("Parent Document ID")
            and not d["Control Number"].startswith("HOT-")
            and not d.get("PI Seeded")
            and (d.get("Processing Error Type", "") or "").strip() == ""
            and d.get("Has Natives", "") != "No"]


def _attach(parent, child, families):
    """Re-parent `child` onto `parent` and keep both sides' claims true (Rule 15)."""
    family_id = parent.get("Family ID") or f"PFAM-{parent['Control Number']}"
    parent["Family ID"]        = family_id
    parent["Has Attachments"]  = "Yes"
    parent["Attachment Count"] = 1
    child["Record Type"]       = "Attachment"
    child["Parent Document ID"] = parent["Control Number"]
    child["Family ID"]         = family_id
    child["Custodian"]         = parent["Custodian"]
    child["Custodian Email"]   = parent.get("Custodian Email", "")
    child["Custodian Org"]     = parent.get("Custodian Org", "")
    child["Custodian Department"] = parent.get("Custodian Department", "")
    child["Primary Date"]      = parent.get("Primary Date", "")
    child["Sort Date"]         = parent.get("Sort Date", "")
    families.append({"family_id": family_id, "thread_id": "",
                     "parent_doc_id": parent["Control Number"],
                     "children": [child["Control Number"]],
                     "subject": parent.get("Email Subject", ""),
                     "family_size": 2, "scripted": True, "planted": True})


def _encrypt(child):
    """Flag the attachment so Rule 12 fabricates a genuinely encrypted native."""
    child["Processing Status"]     = "Error"
    child["Processing Error Type"] = "Password Protected"
    child["Workflow Stage"]        = "Pre-Review: Processing Error"
    child["Responsiveness"]        = ""
    child["Privilege"]             = ""
    child["Privilege Reason"]      = ""
    child["Bates Begin"]           = ""
    child["Bates End"]             = ""
    child["Production Set"]        = ""
    child["Redacted"]              = "No"
    child["TAR Score"]             = ""
    child["AL Predicted Relevant"] = ""
    child["Is Encrypted"]          = "Yes"


def apply(all_docs, families, custodians, tier_name, seed=42):
    """Mutate `all_docs` and `families` in place. Returns the findings list.

    Every finding reports what it is findable by and what it is invisible to, so a
    tester who gets a negative result knows whether that is the right answer.
    """
    rng = random.Random(seed ^ 0x7F1D)        # own stream: never perturbs default output
    findings = []

    # Two custodians with enough traffic to make a single message inconspicuous.
    ranked = sorted({c["name"] for c in custodians},
                    key=lambda n: -sum(1 for d in all_docs if d.get("Custodian") == n))
    principal_cust = ranked[0] if ranked else ""
    decoy_cust     = ranked[1] if len(ranked) > 1 else principal_cust

    # ── 1. Findable on metadata, unreadable by content analysis ──
    parent = _pick(rng, _outbound_email_with_no_attachments(all_docs, principal_cust))
    child  = _pick(rng, _loose_edoc(all_docs, principal_cust))
    if parent and child:
        name, addr = PRINCIPAL_ADDRESS
        parent["Email To"]           = name
        parent["Email To SMTP"]      = addr
        parent["Email CC"]           = ""
        parent["Email CC SMTP"]      = ""
        parent["Email Subject"]      = "Per our call"
        parent["Conversation Topic"] = "Per our call"
        parent["Issue Tags"]         = ""
        _attach(parent, child, families)
        _encrypt(child)
        findings.append({
            "id": "metadata_only",
            "control_number": parent["Control Number"],
            "custodian": parent["Custodian"],
            "date": parent.get("Primary Date", ""),
            "findable_by": "metadata: one message to an address that appears once in the corpus",
            "invisible_to": "content analysis: a two-word body and an attachment that will not open",
            "unique_address": addr,
            "attachment": {"control_number": child["Control Number"],
                           "error_type": "Password Protected"},
            "expected_answer": (
                f"{addr} is a single-document entity in Key Relationships, on one "
                f"outbound message from {parent['Custodian']} carrying an encrypted "
                f"attachment. Nothing in the text says so."),
            "how_to_verify": (
                "Key Relationships: the address appears as a non-custodian entity with "
                "exactly one document. Searching the extracted text for it returns the "
                "one email and nothing else."),
            "body": METADATA_ONLY_BODY,
        })

    # ── 2. Findable only by reading, zero keyword hits ──
    pool = [d for d in all_docs
            if d.get("File Type Category", "").startswith("Office - Word")
            and not d["Control Number"].startswith("HOT-")
            and not d.get("PI Seeded")
            and d.get("Language", "English") == "English"
            and (d.get("Processing Error Type", "") or "").strip() == ""
            and d.get("Custodian") == principal_cust]
    doc = _pick(rng, pool)
    if doc:
        doc["Title"]                  = "Notes"
        doc["Email Subject"]          = ""
        doc["Issue Tags"]             = ""
        doc["Extracted Text Preview"] = CONTENT_ONLY_BODY.split("\n\n")[1][:200]
        findings.append({
            "id": "content_only",
            "control_number": doc["Control Number"],
            "custodian": doc["Custodian"],
            "date": doc.get("Primary Date", ""),
            "findable_by": "reading it",
            "invisible_to": "every keyword filter on the matter, and every metadata cut",
            "expected_answer": (
                "A contemporaneous note describing a decision kept out of writing. It "
                "names no company, no file and no person in full, and hits none of the "
                "matter's search terms."),
            "how_to_verify": (
                "Search the extracted text for any matter keyword: this document is not "
                "in the results. It is reachable only through a topic or summary pass, "
                "or by a reviewer opening it."),
            "keywords_checked": len(MATTER_KEYWORDS),
            "body": CONTENT_ONLY_BODY,
        })

    # ── 3. The decoy: same shape as the principal, innocent ──
    parent = _pick(rng, _outbound_email_with_no_attachments(all_docs, decoy_cust))
    child  = _pick(rng, _loose_edoc(all_docs, decoy_cust))
    explain = _pick(rng, [d for d in _outbound_email_with_no_attachments(all_docs, decoy_cust)
                          if parent and d["Control Number"] != parent["Control Number"]])
    if parent and child and explain:
        name, addr = DECOY_ADDRESS
        parent["Email To"]           = name
        parent["Email To SMTP"]      = addr
        parent["Email Subject"]      = "As discussed"
        parent["Conversation Topic"] = "As discussed"
        parent["Issue Tags"]         = ""
        _attach(parent, child, families)
        _encrypt(child)

        explain["Email To"]           = name
        explain["Email To SMTP"]      = addr
        explain["Email Subject"]      = "Internal controls walkthrough — Thursday 2pm"
        explain["Conversation Topic"] = "Internal controls walkthrough — Thursday 2pm"
        explain["Issue Tags"]         = ""
        findings.append({
            "id": "decoy",
            "control_number": parent["Control Number"],
            "custodian": parent["Custodian"],
            "date": parent.get("Primary Date", ""),
            "findable_by": "the same filter that catches the principal",
            "invisible_to": "nothing — it is meant to be caught",
            "decoy_address": addr,
            "attachment": {"control_number": child["Control Number"],
                           "error_type": "Password Protected"},
            "distinguisher": {
                "control_number": explain["Control Number"],
                "why": ("A second message to the same address explains it: an external "
                        "assurance provider on an internal controls review, working papers "
                        "returned encrypted. The address therefore appears twice, and the "
                        "principal's appears once."),
            },
            "expected_answer": (
                f"{addr} matches the principal's pattern and is innocent. The right answer "
                f"is reached by walking the entity's other documents, not by reading this one."),
            "how_to_verify": (
                "Key Relationships: this entity carries two documents, not one. Open the "
                "second and the encrypted attachment is accounted for."),
            "body": DECOY_BODY,
            "distinguisher_body": DECOY_EXPLAINER_BODY,
        })

    # ── 4. Relevant content buried on a late tab ──
    pool = [d for d in all_docs
            if d.get("File Type Category", "").startswith("Office - Excel")
            and not d["Control Number"].startswith("HOT-")
            and not d.get("PI Seeded")
            and (d.get("Processing Error Type", "") or "").strip() == ""]
    doc = _pick(rng, pool)
    if doc:
        doc["Sheet Names"] = "; ".join(BURIED_SHEETS)
        doc["Title"]       = "Territory Reconciliation — FY2014"
        findings.append({
            "id": "buried_deep",
            "control_number": doc["Control Number"],
            "custodian": doc.get("Custodian", ""),
            "date": doc.get("Primary Date", ""),
            "findable_by": f"full extraction: the payload is on tab {len(BURIED_SHEETS) - 1} "
                           f"of {len(BURIED_SHEETS)}, '{BURIED_SHEET}'",
            "invisible_to": "any extraction that stops at the first sheet",
            "sheet_count": len(BURIED_SHEETS),
            "payload_sheet": BURIED_SHEET,
            "expected_answer": ("Three released orders with no documented justification, "
                                f"on the '{BURIED_SHEET}' tab. The first tab is a clean summary."),
            "how_to_verify": ("Search the extracted text for 'without documented "
                              "justification'. A hit means the whole workbook was read."),
            "payload_rows": BURIED_PAYLOAD,
        })

    return findings


NOTE = ("Known-answer findings, one per detection method. Each says what it is "
        "findable by and what it is invisible to, so a negative result can be told "
        "apart from a missed one.")
