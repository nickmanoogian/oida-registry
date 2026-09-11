#!/usr/bin/env python3
"""
collection_shape.py — A gap, a spike, and a population that straddles two categories

RULES.md Rule 22. Two of the last gaps in the widget coverage table, and they share a
shape: both are about giving a widget something *hard* rather than something more.

**The date axis had nothing to detect.** Measured on the small tier before this rule:
48 months running 15 to 48 documents, a 3.2x spread with no anomaly in it. That is
organic variation, and a feature that claims to surface collection gaps could not be
tested against it either way, because there was no gap to find and no spike to
explain.

**Document Categories had no ambiguous case.** Every document sat squarely in one
topic, so categorisation was only ever asked easy questions. A population that
plausibly belongs to two categories is the one that tells you whether a classifier
commits, hedges, or picks at random.

Nothing is deleted or invented here. The gap and the spike are made by **moving dates**,
so the tier keeps its size and its file type shares, and every move stays inside the
matter window and inside the document's own narrative phase. A document that moves does
not change what it is about.
"""

import calendar
import collections
import random
from datetime import datetime

# A quarter with nothing in it, for one custodian. Per custodian rather than across the
# whole collection, because that is how a real hole appears: one person's mailbox was
# preserved late, or a migration lost a period, and everybody else's data is fine.
GAP_MONTHS = 3

# The spike, as a multiple of the median month. 3.5x is past anything the organic
# variation reaches, so it is unambiguous rather than a judgement call.
SPIKE_MULTIPLE = 3.5

# The ambiguous population: two issue tags that genuinely co-occur in this matter. A
# speaker-bureau payment to a physician whose office also ran prior-authorisation calls
# belongs to both, and no amount of reading settles it into one.
STRADDLE_TAGS = ("Speaker Bureau Payments", "Prior Auth Fraud")
STRADDLE_COUNT = {"small": 25, "medium": 90, "large": 900, "xlarge": 1700}

STRADDLE_TITLES = [
    "Speaker program honoraria and prior authorization support — {place} practice",
    "Q{q} speaker payments and IRC call volume — {place}",
    "KOL engagement and reimbursement assistance — {place} clinic review",
    "Speaker bureau roster and prior auth approval rates — {place}",
    "{place}: honoraria schedule with prior authorization outcomes attached",
]

STRADDLE_PLACES = ["Butner", "Chillicothe", "Valleyview", "Harborside", "Kermit",
                   "Williamson", "Oceana", "Hurricane", "Logan", "Matewan"]

STRADDLE_BODY = (
    "Attaching the honoraria schedule alongside the prior authorization outcomes for the "
    "same practice, because the two keep getting discussed in the same meeting and "
    "nobody can agree which file they belong in.\n\n"
    "The speaker payments are straightforward: four programs, four honoraria, all within "
    "the approved band. The prior authorization numbers for the same office are the part "
    "that needs a second look, since the approval rate moved after the speaker programs "
    "started and the reimbursement team handled those calls directly.\n\n"
    "Filing this under speaker programs for now. It sits as comfortably under "
    "reimbursement, which is the problem."
)

DATE_FIELDS = ("Primary Date", "Sort Date", "Date Sent", "Date Received",
               "Date Created", "Date Last Modified", "Date Taken",
               "Rsmf/BeginDate", "Rsmf/EndDate")

NOTE = ("A planted gap and a planted spike on the date axis, and a population that "
        "belongs to two categories at once. Made by moving dates and adding a second "
        "tag, so the tier keeps its size and its file type shares.")


def _month(value):
    return (value or "")[:7]


def _retarget(value, year, month):
    """Move one date value to a target month, keeping day-of-month and time."""
    raw = (value or "").strip()
    if not raw:
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw[:19] if len(fmt) > 10 else raw[:10], fmt)
        except ValueError:
            continue
        day = min(dt.day, calendar.monthrange(year, month)[1])
        moved = dt.replace(year=year, month=month, day=day)
        return moved.strftime(fmt if len(fmt) > 10 else "%Y-%m-%d")
    return value


def _move(doc, year, month):
    """Move every date on a document to the target month, together."""
    for field in DATE_FIELDS:
        if doc.get(field):
            doc[field] = _retarget(doc[field], year, month)


def apply(all_docs, tier_name, seed=42):
    """Mutate `all_docs` in place. Returns the manifest.

    Runs before Rule 21, because Processing Folder Path carries year and month and
    Rule 11 makes that path a contract with the tree on disk.
    """
    rng = random.Random(seed ^ 0x1C7B)        # own stream: never perturbs the narrative

    dated = [d for d in all_docs if _month(d.get("Primary Date"))]
    months = sorted({_month(d["Primary Date"]) for d in dated})
    per_month = collections.Counter(_month(d["Primary Date"]) for d in dated)
    median = sorted(per_month.values())[len(per_month) // 2]

    # Which phases occupy which month, so a move never lands a document in a month
    # where its own narrative phase does not belong.
    phases = collections.defaultdict(set)
    for d in dated:
        phases[_month(d["Primary Date"])].add(str(d.get("Narrative Phase", "")))

    report = {"note": NOTE, "baseline_median_documents_per_month": median}

    # ── The gap: one custodian, one quarter, nothing ──
    volumes = collections.Counter(d.get("Custodian", "") for d in dated if d.get("Custodian"))
    gap_cust = volumes.most_common(1)[0][0] if volumes else None
    if gap_cust and len(months) > GAP_MONTHS + 4:
        start = len(months) // 3
        window = months[start:start + GAP_MONTHS]
        moved = []
        for d in dated:
            if d.get("Custodian") != gap_cust or _month(d["Primary Date"]) not in window:
                continue
            phase = str(d.get("Narrative Phase", ""))
            # nearest month outside the window that already holds this phase
            options = [m for m in months if m not in window and phase in phases[m]]
            if not options:
                continue
            target = min(options, key=lambda m: abs(months.index(m) - months.index(window[0])))
            y, mo = int(target[:4]), int(target[5:7])
            _move(d, y, mo)
            moved.append(d["Control Number"])
        report["gap"] = {
            "custodian": gap_cust,
            "months": window,
            "documents_moved_out": len(moved),
            "expected": (f"{gap_cust} has no documents at all in {window[0]} to {window[-1]}, "
                         f"while every other custodian's volume over those months is "
                         f"unchanged. A real hole looks like this: one person's mailbox "
                         f"preserved late, not a collection-wide dip."),
            "how_to_verify": (f"Collection Coverage, custodian by month: the row for "
                              f"{gap_cust} is empty across those three columns and the "
                              f"column totals stay normal."),
            "document_ids": moved[:10] + (["..."] if len(moved) > 10 else []),
        }

    # ── The spike: one month, unmistakably ──
    per_month = collections.Counter(_month(d["Primary Date"]) for d in dated)
    target_month = max(per_month, key=lambda m: per_month[m])
    want = int(median * SPIKE_MULTIPLE)
    ty, tm = int(target_month[:4]), int(target_month[5:7])
    idx = months.index(target_month)
    # A wide donor window on purpose. Pulling 80 documents from two neighbouring
    # months halved them, which is its own anomaly and not one anybody asked for.
    # Spread across eight months the dip is a few documents each.
    donors = [m for m in months[max(0, idx - 4): idx + 5] if m != target_month]
    pulled = []
    pool = [d for d in dated
            if _month(d["Primary Date"]) in donors
            and str(d.get("Narrative Phase", "")) in phases[target_month]
            and d.get("Custodian") != report.get("gap", {}).get("custodian")]
    rng.shuffle(pool)
    for d in pool:
        if per_month[target_month] + len(pulled) >= want:
            break
        _move(d, ty, tm)
        pulled.append(d["Control Number"])
    report["spike"] = {
        "month": target_month,
        "documents": per_month[target_month] + len(pulled),
        "documents_moved_in": len(pulled),
        "baseline_median": median,
        "multiple_of_median": round((per_month[target_month] + len(pulled)) / median, 1),
        "expected": (f"{target_month} carries roughly {SPIKE_MULTIPLE:.1f}x the median month. "
                     f"The documents are drawn from the eight months around it, so the "
                     f"collection does not grow and no single neighbour loses much."),
        "how_to_verify": ("Collection Coverage, documents by month: one bar is far past "
                          "the rest and the neighbouring bars are a little short."),
        "document_ids": pulled[:10] + (["..."] if len(pulled) > 10 else []),
    }

    # ── The population that belongs to two categories ──
    want_n = STRADDLE_COUNT.get(tier_name, STRADDLE_COUNT["small"])
    claimed = set(report.get("gap", {}).get("document_ids", [])) | set(report["spike"]["document_ids"])
    pool = [d for d in all_docs
            if d.get("File Type Category", "").startswith(("Office -", "PDF"))
            and not d["Control Number"].startswith("HOT-")
            and d["Control Number"] not in claimed
            and str(d.get("Level", "")) != "0"
            and d.get("Has Natives", "") != "No"
            and (d.get("Processing Error Type", "") or "").strip() == ""]
    rng.shuffle(pool)
    straddle = []
    for n, d in enumerate(pool[:want_n]):
        place = STRADDLE_PLACES[n % len(STRADDLE_PLACES)]
        title = STRADDLE_TITLES[n % len(STRADDLE_TITLES)].format(
            place=place, q=(n % 4) + 1)
        d["Title"] = title
        d["Issue Tags"] = "; ".join(STRADDLE_TAGS)
        d["Extracted Text Preview"] = STRADDLE_BODY.split("\n\n")[0][:200]
        straddle.append(d["Control Number"])
    report["straddling_categories"] = {
        "categories": list(STRADDLE_TAGS),
        "documents": len(straddle),
        "expected": (f"These documents carry both {STRADDLE_TAGS[0]} and {STRADDLE_TAGS[1]}, "
                     f"and the content supports both: a speaker-bureau honorarium to a "
                     f"practice whose prior authorisation numbers moved afterwards. There is "
                     f"no single right category, so a classifier that commits to one is not "
                     f"wrong, and one that reports both is not hedging."),
        "how_to_verify": ("Document Categories: this population should appear under both "
                          "categories, or be flagged as ambiguous. Either is defensible; "
                          "silently dropping it is not."),
        "document_ids": straddle[:10] + (["..."] if len(straddle) > 10 else []),
        "body": STRADDLE_BODY,
    }
    return recount(all_docs, report)


def recount(all_docs, report):
    """Re-measure the planted shape and write it back into the report.

    Called at the end of this pass and again after the edge cases, because
    `missing_date` and `sentinel_date` move documents off the date axis entirely.
    Two documents leaving the spike month is enough to make the manifest wrong, and a
    manifest that disagrees with the corpus is the one thing a ground-truth file must
    never be.
    """
    per_month = collections.Counter(
        (d.get("Primary Date", "") or "")[:7] for d in all_docs
        if (d.get("Primary Date", "") or "")[:7])
    if not per_month:
        return report
    median = sorted(per_month.values())[len(per_month) // 2]
    report["baseline_median_documents_per_month"] = median

    spike = report.get("spike")
    if spike:
        spike["documents"] = per_month.get(spike["month"], 0)
        spike["baseline_median"] = median
        spike["multiple_of_median"] = round(spike["documents"] / median, 1) if median else 0

    gap = report.get("gap")
    if gap:
        gap["documents_remaining_in_window"] = sum(
            1 for d in all_docs
            if d.get("Custodian") == gap["custodian"]
            and (d.get("Primary Date", "") or "")[:7] in gap["months"])

    strad = report.get("straddling_categories")
    if strad:
        cats = strad["categories"]
        strad["documents"] = sum(1 for d in all_docs
                                 if all(c in (d.get("Issue Tags", "") or "") for c in cats))
    return report
