#!/usr/bin/env python3
"""
entity_population.py — Give Key Relationships a real entity population

RULES.md Rule 20. Rule 14 fixed the *custodian* side: ten custodians give 45
internal pairs, past the top-25 cut production applies. The non-custodian side was
never fixed, and it is half of what the widget shows.

Measured on the small tier before this rule: **15 distinct email addresses** in the
whole collection, against a production cap of 25 non-custodian entities. The tier
could not reach the cut, so the "entities below the cut are not listed" behaviour
was untestable with the package most people download. There was exactly **one**
entity carrying a single document, and it was planted by Rule 18, so there was no
organic long tail either. And **no person used two addresses**, so name
normalisation had never been run against this data at all.

Three things, therefore:

  * **An external correspondent roster** wide enough to pass the cap, on a skewed
    volume distribution rather than a flat one.
  * **A long tail that is mostly singletons**, because that is the shape a real
    collection has and it is the part a cap hides.
  * **Alias addresses**: a few people reachable at two addresses, so resolving
    them to one person is something that can be got right or wrong. Both counts
    below census all four address fields, so Rule 24 can turn one of these
    documents around without changing what the alias is worth.

Applied after generation on its own RNG stream, so the narrative, the file type
shares and the review coding are untouched.
"""

import random

# Externals per tier. Small needs to clear 25 comfortably, not squeak past it: a
# tier that lands on 26 tests the cap only until someone reseeds it.
ROSTER_SIZE = {"small": 40, "medium": 60, "large": 120, "xlarge": 120}

# People reachable at two addresses.
ALIAS_COUNT = {"small": 2, "medium": 3, "large": 5, "xlarge": 5}

# The volume shape. A real external population is mostly singletons with a short
# heavy head, which is exactly the distribution a top-N cap flattens.
HEAVY_SHARE   = 0.08      # of the roster: many documents each
MODERATE_SHARE = 0.22     # a handful each
# the remainder get exactly one document, and that remainder is the point

HEAVY_DOCS    = (25, 60)
MODERATE_DOCS = (3, 9)

# Fictional people at the real organisations this matter involves, which is the
# convention the custodian roster already follows. Nobody here is a real person.
EXTERNALS = [
    # Distributor compliance and order-management contacts
    ("Dana Kirchner",    "dana.kirchner@cardinalhealth.com",       "Cardinal Health",        "Distributor compliance"),
    ("Owen Basara",      "owen.basara@cardinalhealth.com",         "Cardinal Health",        "Distributor compliance"),
    ("Renee Colquitt",   "renee.colquitt@mckesson.com",            "McKesson",               "Distributor compliance"),
    ("Victor Amundsen",  "victor.amundsen@mckesson.com",           "McKesson",               "Order management"),
    ("Priya Deshmukh",   "priya.deshmukh@amerisourcebergen.com",   "AmerisourceBergen",      "Distributor compliance"),
    ("Grant Oyelaran",   "grant.oyelaran@amerisourcebergen.com",   "AmerisourceBergen",      "Diversion control"),
    # Regulators, on the generic inboxes the existing roster already used
    ("DEA Diversion Control",   "diversion@dea.gov",               "DEA",                    "Regulator"),
    ("DEA Detroit Field Div",   "detroit.diversion@dea.gov",       "DEA",                    "Regulator"),
    ("DEA St Louis Field Div",  "stlouis.diversion@dea.gov",       "DEA",                    "Regulator"),
    ("FDA CDER",                "cder@fda.hhs.gov",                "FDA",                    "Regulator"),
    ("Ohio AG Office",          "inquiry@ag.state.us",             "State AG",               "Regulator"),
    ("Oklahoma AG Office",      "civil.enforcement@ag.state.us",   "State AG",               "Regulator"),
    ("West Virginia AG Office", "consumer@ag.state.us",            "State AG",               "Regulator"),
    ("State Board of Pharmacy", "licensing@pharmacyboard.state.us","State Board",            "Regulator"),
    # Outside counsel and experts
    ("Marguerite Ivey",  "m.ivey@harlowbrandt.example",            "Harlow Brandt LLP",      "Outside counsel"),
    ("Curtis Nakamura",  "c.nakamura@harlowbrandt.example",        "Harlow Brandt LLP",      "Outside counsel"),
    ("Ilse Fontaine",    "i.fontaine@brightwaterlaw.example",      "Brightwater Law",        "Outside counsel"),
    ("Terrence Aboagye", "t.aboagye@brightwaterlaw.example",       "Brightwater Law",        "Outside counsel"),
    ("Solveig Brandt",   "s.brandt@meridianforensics.example",     "Meridian Forensics",     "Expert witness"),
    # Speaker bureau physicians, the population Rule 4's narrative already names
    ("Dr. Alan Foster",   "a.foster@lakeshoreclinic.example",      "Lakeshore Clinic",       "Speaker bureau KOL"),
    ("Dr. Maria Santos",  "m.santos@santospaincare.example",       "Santos Pain Care",       "Speaker bureau KOL"),
    ("Dr. Susan Ellis",   "s.ellis@ellisneurology.example",        "Ellis Neurology",        "Speaker bureau KOL"),
    ("Dr. Robert Kim",    "r.kim@midstatepain.example",            "Midstate Pain",          "Speaker bureau KOL"),
    ("Dr. Patricia Quinn","p.quinn@quinnfamilymed.example",        "Quinn Family Medicine",  "Speaker bureau KOL"),
    ("Dr. Halvor Jessen", "h.jessen@northreachpain.example",       "Northreach Pain",        "Speaker bureau KOL"),
    ("Dr. Adaeze Nwosu",  "a.nwosu@nwosuspine.example",            "Nwosu Spine",            "Speaker bureau KOL"),
    # Pharmacy and dispensing
    ("Rowena Escobar",   "r.escobar@butnerpharmacy.example",       "Butner Pharmacy",        "Dispensing pharmacy"),
    ("Lyle Tomczak",     "l.tomczak@chillicothedrug.example",      "Chillicothe Drug",       "Dispensing pharmacy"),
    ("Anika Sorenson",   "a.sorenson@valleyviewrx.example",        "Valleyview Rx",          "Dispensing pharmacy"),
    ("Marcus Delacroix-Bell","m.bell@harborsiderx.example",        "Harborside Rx",          "Dispensing pharmacy"),
    # Vendors, labs and service providers
    ("Yevgenia Kaplan",  "y.kaplan@stratafieldresearch.example",   "Stratafield Research",   "Market research vendor"),
    ("Bo Lindqvist",     "b.lindqvist@axiomclinicallabs.example",  "Axiom Clinical Labs",    "Laboratory"),
    ("Chidi Okafor",     "c.okafor@pinnaclefreight.example",       "Pinnacle Freight",       "Logistics"),
    ("Simone Vasquez",   "s.vasquez@corveltmedia.example",         "Corvelt Media",          "Advertising agency"),
    ("Hector Ramallo",   "h.ramallo@bridgepointaudit.example",     "Bridgepoint Audit",      "External audit"),
    ("Ingrid Salvesen",  "i.salvesen@calderapackaging.example",    "Caldera Packaging",      "Supplier"),
    ("Tobias Wren",      "t.wren@wrenactuarial.example",           "Wren Actuarial",         "Consultant"),
    ("Fatima Belkacem",  "f.belkacem@northgatebenefits.example",   "Northgate Benefits",     "Benefits administrator"),
    ("Desmond Achebe",   "d.achebe@sentinelriskgroup.example",     "Sentinel Risk Group",    "Insurance broker"),
    ("Noor Rahimi",      "n.rahimi@veritasstaffing.example",       "Veritas Staffing",       "Staffing vendor"),
    ("Elke Wendt",       "e.wendt@lumenpharmaservices.example",    "Lumen Pharma Services",  "Contract services"),
    ("Casimir Nowak",    "c.nowak@aegisdatasystems.example",       "Aegis Data Systems",     "IT vendor"),
    ("Beatriz Alencar",  "b.alencar@corradofacilities.example",    "Corrado Facilities",     "Facilities vendor"),
    ("Sunil Varadarajan","s.varadarajan@keystoneprintworks.example","Keystone Printworks",   "Printing vendor"),
]

# The second address a person sends from. Legacy and personal domains are the two
# realistic reasons a single custodian shows up twice.
ALIAS_PATTERNS = [
    ("{first}.{last}@covidien.com",        "legacy domain from before the spin-off"),
    ("{f}{last}@mallinckrodt.com",         "an older account format still in use"),
    ("{first}.{last}@mnk-corp.example",    "a subsidiary domain"),
    ("{first}{last}@mailbox.invalid",      "a personal address used for work mail"),
]

# The hand-authored roster above carries the narrative: named counterparties a
# reviewer could plausibly chase. A large matter also has hundreds of dispensing
# counterparties that appear once each, and that tail is precisely what a top-N cap
# hides, so it is generated rather than written out.
TAIL_PLACES = ["Butner", "Chillicothe", "Valleyview", "Harborside", "Kermit", "Mount Gay",
               "Williamson", "Stollings", "Oceana", "Ceredo", "Hurricane", "Wayne",
               "Logan", "Gilbert", "Man", "Delbarton", "Matewan", "Sophia", "Rainelle",
               "Elkview", "Nitro", "Poca", "Sissonville", "Cross Lanes", "Dunbar",
               "Belle", "Cedar Grove", "Glasgow", "Marmet", "Chesapeake"]
TAIL_KINDS = [("{place} Family Pharmacy", "contact@{slug}familyrx.example"),
              ("{place} Drug Center",     "orders@{slug}drug.example"),
              ("{place} Apothecary",      "rx@{slug}apothecary.example"),
              ("{place} Community Rx",    "info@{slug}communityrx.example")]


def _tail_entities(n, taken):
    """Dispensing counterparties for the singleton tail, generated in order."""
    out = []
    for place in TAIL_PLACES:
        for name_t, mail_t in TAIL_KINDS:
            if len(out) >= n:
                return out
            slug = place.lower().replace(" ", "")
            name, email = name_t.format(place=place), mail_t.format(slug=slug)
            if email in taken:
                continue
            out.append((name, email, name, "Dispensing pharmacy"))
    return out


NOTE = ("The non-custodian half of Key Relationships. A skewed external roster with a "
        "long singleton tail, plus people reachable at two addresses so name "
        "normalisation has something to resolve.")


def _eligible(all_docs, protected):
    """Ordinary email that no other rule has claimed."""
    return [d for d in all_docs
            if d.get("Record Type") == "Email"
            and d["Control Number"] not in protected
            and not d["Control Number"].startswith("HOT-")
            and not str(d.get("Email Thread ID", "")).startswith("STHR-")
            and d.get("Email To SMTP")]


def apply(all_docs, custodians, tier_name, seed=42, protected=None):
    """Mutate `all_docs` in place. Returns the report for entities.json."""
    rng = random.Random(seed ^ 0x4B2A)        # own stream: never perturbs the narrative
    protected = set(protected or ())
    want = ROSTER_SIZE.get(tier_name, ROSTER_SIZE["small"])
    roster = EXTERNALS[:want]
    if want > len(roster):
        roster = roster + _tail_entities(want - len(roster),
                                         {e[1] for e in roster})

    pool = _eligible(all_docs, protected)
    rng.shuffle(pool)

    # ── Volume budget: a short heavy head, then singletons ──
    n_heavy = max(1, round(len(roster) * HEAVY_SHARE))
    n_mod   = max(1, round(len(roster) * MODERATE_SHARE))
    budget = []
    for i, (name, email, org, kind) in enumerate(roster):
        if i < n_heavy:
            count = rng.randint(*HEAVY_DOCS)
        elif i < n_heavy + n_mod:
            count = rng.randint(*MODERATE_DOCS)
        else:
            count = 1
        budget.append({"name": name, "email": email, "org": org, "kind": kind,
                       "documents": count})

    # Trim the budget to what the pool can actually carry, so the report cannot
    # claim documents that were never rewritten.
    total = sum(b["documents"] for b in budget)
    while total > len(pool) and budget:
        for b in budget:
            if b["documents"] > 1 and total > len(pool):
                b["documents"] -= 1
                total -= 1
        if all(b["documents"] == 1 for b in budget):
            break
    budget = budget[:len(pool)]

    cursor = 0
    for b in budget:
        assigned = []
        for _ in range(b["documents"]):
            if cursor >= len(pool):
                break
            d = pool[cursor]; cursor += 1
            d["Email To"]      = b["name"]
            d["Email To SMTP"] = b["email"]
            d["Email CC"]      = ""
            d["Email CC SMTP"] = ""
            assigned.append(d["Control Number"])
        b["assigned"] = len(assigned)
        b["document_ids"] = assigned if len(assigned) <= 5 else assigned[:5] + ["..."]
    budget = [b for b in budget if b["assigned"]]

    for b in budget:
        b["assigned_by_this_rule"] = b.pop("assigned")

    # ── Alias addresses: one person, two addresses ──
    named = [c for c in custodians if c.get("email")]
    rng.shuffle(named)
    aliases = []
    for cust in named[:ALIAS_COUNT.get(tier_name, 2)]:
        first, _, last = cust["name"].replace("Dr. ", "").partition(" ")
        last = last or first
        pattern, why = ALIAS_PATTERNS[len(aliases) % len(ALIAS_PATTERNS)]
        alias = pattern.format(first=first.lower(), last=last.lower(), f=first[:1].lower())
        if alias.lower() == str(cust["email"]).lower():
            continue
        # Their own outbound mail, a minority of it, sent from the second address.
        theirs = [d for d in all_docs
                  if d.get("Record Type") == "Email"
                  and d.get("Custodian") == cust["name"]
                  and d.get("Email From SMTP")
                  and d["Control Number"] not in protected
                  and not d["Control Number"].startswith("HOT-")
                  and not str(d.get("Email Thread ID", "")).startswith("STHR-")]
        rng.shuffle(theirs)
        take = theirs[:max(1, len(theirs) // 4)]
        for d in take:
            d["Email From SMTP"] = alias
        if not take:
            continue
        aliases.append({
            "person": cust["name"],
            "primary": cust["email"],
            "alias": alias,
            "why": why,
            "documents_from_primary": sum(
                1 for d in all_docs
                if d.get("Custodian") == cust["name"]
                and d.get("Email From SMTP") == cust["email"]),
            "documents_from_alias": len(take),
        })


    report = {
        "note": NOTE,
        "externals": budget,
        "aliases": aliases,
        "singletons": [],
        "distinct_external_addresses": len({b["email"] for b in budget}),
        "production_entity_cap": 25,
    }
    return recount(all_docs, report)


ADDR_FIELDS = ("Email From SMTP", "Email To SMTP", "Email CC SMTP", "Email BCC SMTP")


def recount(all_docs, report):
    """Census the corpus and write the counts into the report.

    Called at the end of this pass and again after the edge cases, because those
    blank recipients and the ground truth has to describe the data as it finally
    stands rather than as this rule left it. Counting what the pass handed out
    would also understate the three regulator inboxes that the generator's own
    round-robin already used, by an order of magnitude.
    """
    census: dict = {}
    for d in all_docs:
        for field in ADDR_FIELDS:
            for token in (d.get(field, "") or "").replace(";", ",").split(","):
                token = token.strip().lower()
                if token:
                    census[token] = census.get(token, 0) + 1
    for b in report["externals"]:
        b["documents"] = census.get(b["email"].lower(), 0)
    for a in report["aliases"]:
        a["documents_from_primary"] = census.get(a["primary"].lower(), 0)
        a["documents_from_alias"]   = census.get(a["alias"].lower(), 0)
    report["externals"].sort(key=lambda b: -b["documents"])
    report["singletons"] = sorted(b["email"] for b in report["externals"]
                                  if b["documents"] == 1)
    return report
