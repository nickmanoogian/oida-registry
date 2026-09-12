#!/usr/bin/env python3
"""
mail_direction.py — Give the email graph a direction, and more than one recipient

RULES.md Rule 24. Rule 14 fixed the custodian side of Key Relationships and Rule 20
fixed the external side. Both are about *who* is in the graph. This is about which
way the edges point, which is the part that was wrong in every tier ever shipped.

Measured on the medium tier before this rule, over its 5,214 emails:

  * **5,214 of 5,214 were sent by the custodian.** Not most. All of them. The
    generator sets `Email From` to the custodian's own name unconditionally, so the
    corpus contained no inbound mail at all. A collection is a set of mailboxes, and
    a mailbox is mostly things other people sent you. Ten custodians radiating
    outward with nothing coming back is not a shape a real matter produces, and it
    is the one shape a relationship graph makes look deliberate.
  * **396 were addressed to their own sender**, 7.6% of the email population. The
    recipient was drawn from a pool that included the custodian without excluding
    them, so one email in thirteen is a person writing to themselves. A self edge
    carries no relationship and production has to special-case it.
  * **Every single email had exactly one To recipient.** CC went multi-value under
    Rule 20 and To never did, so the semicolon path in the To column, which is the
    one an importer is most likely to get wrong, was never exercised by any tier.

### What this pass does

**Direction by swap, not by rewrite.** An inbound email is made by exchanging the
From pair with the first To pair. The two people on the document do not change and
neither does any address count, because `entity_population.recount` censuses all
four address fields rather than the To column alone. Only the arrow moves. That
matters: rewriting a participant would falsify Rule 20's entity census and Rule 18's
findings, and this cannot, by construction.

`Custodian` is deliberately left alone on a flipped document. The mail is in that
custodian's mailbox because they received it, which is the ordinary case.

**Protected documents are skipped**, the same set the edge cases honour: anything
carrying a planted finding, a PI instance, a second language or a Rule 20 entity
rewrite. A swap preserves counts, but Rule 18 asserts correspondence it describes
in prose, and prose has a direction in it.

Applied after generation on its own RNG stream, so the file type shares, the
narrative and the review coding are untouched.
"""

import random

# Share of unprotected email that arrives rather than departs. Real collections run
# further than this toward inbound, but the custodians are the narrative's authors:
# push it past half and the planted story stops being told by the people it is about.
INBOUND_SHARE = 0.45

# Share that carries more than one To recipient, and how many extra they get.
MULTI_TO_SHARE = 0.30
EXTRA_TO_CHOICES = [1, 1, 1, 2, 2, 3]


def _people(value_name, value_addr):
    """Split a parallel name/address pair into a list of (name, addr)."""
    names = [p.strip() for p in (value_name or "").split(";") if p.strip()]
    addrs = [p.strip() for p in (value_addr or "").split(";") if p.strip()]
    if len(names) != len(addrs):
        # Mismatched halves mean something upstream rewrote one side only. Trust
        # the addresses, which are what every census counts.
        names = names[:len(addrs)] + [""] * max(0, len(addrs) - len(names))
    return list(zip(names, addrs))


def _pack(pairs):
    return "; ".join(n for n, _ in pairs), "; ".join(a for _, a in pairs)


def apply(all_docs, custodians, tier_name, seed=42, protected=None):
    rng = random.Random(f"mail-direction:{tier_name}:{seed}")
    protected = protected or set()

    emails = [d for d in all_docs
              if d.get("Email From SMTP") and d.get("Email To SMTP")]
    eligible = [d for d in emails if d["Control Number"] not in protected]

    report = {
        "note": "Which way the email edges point, and how many people are on them. "
                "Before this rule every email in every tier was sent by its own "
                "custodian to exactly one recipient.",
        "emails": len(emails),
        "eligible": len(eligible),
        "protected": len(emails) - len(eligible),
    }

    # 1. A person writing to themselves is not a relationship. Redraw the recipient
    #    from the custodian roster, which keeps it inside Rule 14's internal pairs
    #    and so leaves Rule 20's external census exactly where it was.
    deselfed = 0
    for d in eligible:
        frm = d["Email From SMTP"].strip().lower()
        to = _people(d.get("Email To"), d.get("Email To SMTP"))
        if not to or to[0][1].strip().lower() != frm:
            continue
        others = [c for c in custodians if c["email"].strip().lower() != frm]
        if not others:
            continue
        pick = rng.choice(others)
        to[0] = (pick["name"], pick["email"])
        d["Email To"], d["Email To SMTP"] = _pack(to)
        deselfed += 1
    report["self_addressed_repaired"] = deselfed

    # 2. More than one recipient, drawn from the custodians only. Adding an external
    #    here would move a Rule 20 singleton off the singleton tail, and that tail is
    #    an asserted number in entities.json.
    widened = 0
    for d in eligible:
        if rng.random() >= MULTI_TO_SHARE:
            continue
        to = _people(d.get("Email To"), d.get("Email To SMTP"))
        seen = {d["Email From SMTP"].strip().lower()} | {a.strip().lower() for _, a in to}
        seen |= {a.strip().lower()
                 for a in (d.get("Email CC SMTP") or "").replace(";", ",").split(",") if a.strip()}
        pool = [c for c in custodians if c["email"].strip().lower() not in seen]
        if not pool:
            continue
        extra = rng.sample(pool, min(len(pool), rng.choice(EXTRA_TO_CHOICES)))
        to += [(c["name"], c["email"]) for c in extra]
        d["Email To"], d["Email To SMTP"] = _pack(to)
        widened += 1
    report["multi_recipient"] = widened

    # 3. The direction itself. Swap the From pair with the first To pair, so the
    #    custodian receives. Everything else on the document stays where it is.
    flipped = 0
    for d in eligible:
        if rng.random() >= INBOUND_SHARE:
            continue
        to = _people(d.get("Email To"), d.get("Email To SMTP"))
        if not to:
            continue
        sender = (d.get("Email From", ""), d["Email From SMTP"])
        d["Email From"], d["Email From SMTP"] = to[0][0], to[0][1]
        to[0] = sender
        d["Email To"], d["Email To SMTP"] = _pack(to)
        flipped += 1
    report["inbound"] = flipped

    return recount(all_docs, report)


def recount(all_docs, report):
    """Census the direction as it finally stands.

    Called at the end of this pass and again after the edge cases, which blank
    recipients outright. Ground truth has to describe the data that shipped, not
    the data this rule handed on.
    """
    emails = [d for d in all_docs
              if d.get("Email From SMTP") and d.get("Email To SMTP")]
    custodian_sent = sum(1 for d in emails
                         if d.get("Email From", "") == d.get("Custodian", ""))
    self_addressed = sum(1 for d in emails
                         if d["Email From SMTP"].strip().lower()
                         in {a.strip().lower()
                             for a in d["Email To SMTP"].replace(";", ",").split(",")})
    multi = sum(1 for d in emails
                if len([p for p in d["Email To SMTP"].split(";") if p.strip()]) > 1)
    senders = {d["Email From SMTP"].strip().lower() for d in emails}
    report["measured"] = {
        "emails_with_both_ends": len(emails),
        "sent_by_their_own_custodian": custodian_sent,
        "received_by_their_own_custodian": len(emails) - custodian_sent,
        "still_self_addressed": self_addressed,
        "with_more_than_one_recipient": multi,
        "distinct_senders": len(senders),
    }
    return report
