#!/usr/bin/env python3
"""
language_mix.py — Give Primary Language Composition something to compose

RULES.md Rule 17. The generated tiers set Language = English on every row, so the
Primary Language widget has one bar and nothing to test: no second slice, no small
slice that has to stay visible next to a large one, no sort order to get wrong.

The second-language documents are deliberately unrelated to the matter — facilities
notices, canteen closures, parking markings. A German slice about suspicious order
monitoring would leave a reviewer wondering whether the foreign-language population
is secretly responsive. This one answers that question up front.

Applied after generation on its own RNG stream, so the narrative is untouched. Only
documents that are non-responsive or unreviewed are drawn: rewriting a document a
reviewer coded Responsive into a canteen notice contradicts its own coding.
"""

import random

# Share of the tier per second language. Small enough that the widget has to keep a
# minor slice legible, large enough to be more than a rounding error.
LANGUAGE_MIX = {
    "small":  {"German": 0.020},
    "medium": {"German": 0.015, "Polish": 0.010},
    "large":  {"German": 0.012, "Polish": 0.008, "Spanish": 0.004},
    "xlarge": {"German": 0.012, "Polish": 0.008, "Spanish": 0.004},
}

# One line per document. Real sentences: a language classifier fed lorem ipsum
# reports Latin, and a classifier fed one word reports nothing.
BODIES = {
    "German": [
        "Sehr geehrte Kolleginnen und Kollegen, die Kantine bleibt am Freitag wegen "
        "Wartungsarbeiten geschlossen. Warme Getraenke stehen im Foyer bereit. "
        "Wir bitten um Ihr Verstaendnis. Mit freundlichen Gruessen, Facility Management",
        "Die Parkplaetze im Untergeschoss werden in der naechsten Woche neu markiert. "
        "Bitte nutzen Sie in dieser Zeit den Besucherparkplatz an der Nordseite. "
        "Die Arbeiten dauern voraussichtlich drei Tage.",
        "Hinweis zur Brandschutzuebung am kommenden Dienstag um 10 Uhr. Bitte verlassen "
        "Sie das Gebaeude ueber den naechstgelegenen Ausgang und sammeln Sie sich auf "
        "dem Parkplatz. Die Uebung dauert etwa zwanzig Minuten.",
        "Die neuen Zugangskarten werden ab Montag am Empfang ausgegeben. Alte Karten "
        "verlieren am Ende des Monats ihre Gueltigkeit. Bitte bringen Sie einen "
        "Lichtbildausweis mit.",
        "Wir stellen die Abfalltrennung im Buero um. Ab Mitte des Monats stehen auf "
        "jeder Etage getrennte Behaelter fuer Papier, Verpackungen und Restmuell "
        "bereit. Die Reinigung erfolgt weiterhin taeglich.",
    ],
    "Polish": [
        "Szanowni Panstwo, w piatek stolowka bedzie zamknieta z powodu prac "
        "konserwacyjnych. Cieple napoje beda dostepne w holu glownym. "
        "Przepraszamy za utrudnienia.",
        "Miejsca parkingowe w garazu podziemnym zostana w przyszlym tygodniu ponownie "
        "oznakowane. Prosimy w tym czasie korzystac z parkingu dla gosci od strony "
        "polnocnej. Prace potrwaja okolo trzech dni.",
        "Informujemy o probnej ewakuacji w najblizszy wtorek o godzinie dziesiatej. "
        "Prosimy opuscic budynek najblizszym wyjsciem i zebrac sie na parkingu. "
        "Cwiczenia potrwaja okolo dwudziestu minut.",
        "Nowe karty dostepu bedziemy wydawac od poniedzialku w recepcji. Stare karty "
        "przestana dzialac z koncem miesiaca. Prosimy o zabranie dokumentu ze zdjeciem.",
    ],
    "Spanish": [
        "Estimados companeros, el comedor permanecera cerrado el viernes por trabajos "
        "de mantenimiento. Habra bebidas calientes disponibles en el vestibulo. "
        "Gracias por su comprension.",
        "Las plazas de aparcamiento del sotano se volveran a senalizar la proxima "
        "semana. Durante esos dias utilicen el aparcamiento de visitantes situado en "
        "el lado norte. Los trabajos duraran unos tres dias.",
        "Les informamos del simulacro de evacuacion del proximo martes a las diez de "
        "la manana. Salgan por la puerta mas cercana y reunanse en el aparcamiento. "
        "El simulacro durara unos veinte minutos.",
    ],
}

TITLES = {
    "German": ["Kantine — Wartungsarbeiten am Freitag", "Parkhaus — Neue Markierungen",
               "Brandschutzuebung — Termin und Ablauf", "Neue Zugangskarten ab Montag",
               "Abfalltrennung im Buero — Umstellung"],
    "Polish": ["Stolowka — prace konserwacyjne w piatek", "Garaz — nowe oznakowanie miejsc",
               "Probna ewakuacja — termin", "Nowe karty dostepu od poniedzialku"],
    "Spanish": ["Comedor — cierre por mantenimiento", "Aparcamiento — nueva senalizacion",
                "Simulacro de evacuacion — martes"],
}

# The point of the slice is that nobody has to wonder whether it is responsive.
NOTE = ("Facilities and office administration notices, deliberately unrelated to the "
        "matter. A reviewer who reads one learns nothing about the case, which is what "
        "makes the language slice safe to test against.")


def shares(tier_name, override=None):
    """{language: share}. An override replaces the tier default for one language."""
    mix = dict(LANGUAGE_MIX.get(tier_name, LANGUAGE_MIX["small"]))
    if override is not None:
        first = next(iter(mix))
        mix = {first: override}
    return mix


def apply(all_docs, tier_name, seed=42, override=None):
    """Mutate `all_docs` in place. Returns {language: {...}} for the report.

    Text-bearing documents only: setting Language on a media file or a container
    claims a classification that nothing could have produced.
    """
    rng   = random.Random(seed ^ 0x1A9C)      # own stream: never perturbs default output
    total = len(all_docs)
    mix   = shares(tier_name, override)

    pool = [d for d in all_docs
            if not d["Control Number"].startswith("HOT-")
            and str(d.get("Level", "")) != "0"
            and d.get("Has Natives", "") != "No"
            and d.get("Responsiveness", "") in ("", "Non-Responsive")
            and d.get("Privilege", "") != "Privileged"
            and not d.get("Bates Begin", "")
            and (d.get("File Type Category", "").startswith(("Email -", "Office -", "PDF")))]
    rng.shuffle(pool)

    report = {}
    for lang, share in mix.items():
        count = max(1, round(total * share))
        taken, pool = pool[:count], pool[count:]
        for d in taken:
            d["Language"]     = lang
            d["Issue Tags"]   = ""          # a canteen notice is not evidence of anything
            body_pool  = BODIES[lang]
            title_pool = TITLES[lang]
            title = rng.choice(title_pool)
            if d.get("File Type Category", "").startswith("Email -"):
                d["Email Subject"]      = title
                d["Conversation Topic"] = title
            else:
                d["Title"] = title
            d["Extracted Text Preview"] = rng.choice(body_pool)[:200]
            d["_language_body"] = rng.choice(body_pool)
        report[lang] = {
            "share":     round(len(taken) / total, 4),
            "requested": share,
            "count":     len(taken),
            "note":      NOTE,
            "documents": [{"control_number": d["Control Number"],
                           "body": d.pop("_language_body")} for d in taken],
        }
    return report
