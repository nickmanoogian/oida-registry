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
#
# WRITTEN WITH THEIR DIACRITICS, AND THAT IS THE WHOLE POINT. Every string here was
# once ASCII-folded: "Parkplaetze" for "Parkplätze", "Buero" for "Büro", "stolowka"
# for "stołówka". It reads as German and Polish to a person and costs a classifier
# its strongest signal, because the characters that make a language identifiable are
# exactly the ones folding removes. Measured against a run over the medium tier:
# 150 planted German documents came back as 122, and 100 Polish as 81. Roughly a
# fifth of the population this rule exists to create was invisible to the widget it
# exists to test.
#
# The bodies are also longer than they were. The folded set had a median of about
# 190 characters of extracted text, which is short enough that detection is a coin
# flip on its own, independent of the characters.
#
# So: if you add a language, write it properly. No transliteration, no "ss" for "ß",
# no "ue" for "ü". If your editor cannot hold the characters, that is a problem with
# the editor.
BODIES = {
    "German": [
        "Sehr geehrte Kolleginnen und Kollegen, die Kantine bleibt am Freitag wegen "
        "Wartungsarbeiten geschlossen. Warme Getränke stehen im Foyer bereit. Der "
        "Automat im zweiten Obergeschoss wird in dieser Zeit täglich nachgefüllt. "
        "Wir bitten um Ihr Verständnis. Mit freundlichen Grüßen, Facility Management",
        "Die Parkplätze im Untergeschoss werden in der nächsten Woche neu markiert. "
        "Bitte nutzen Sie in dieser Zeit den Besucherparkplatz an der Nordseite. Die "
        "Zufahrt über die Seitenstraße bleibt geöffnet, die Schranke wird tagsüber "
        "besetzt. Die Arbeiten dauern voraussichtlich drei Tage.",
        "Hinweis zur Brandschutzübung am kommenden Dienstag um zehn Uhr. Bitte "
        "verlassen Sie das Gebäude über den nächstgelegenen Ausgang und sammeln Sie "
        "sich auf dem Parkplatz. Die Stockwerksbeauftragten prüfen anschließend die "
        "Räume und melden die Vollzähligkeit. Die Übung dauert etwa zwanzig Minuten.",
        "Die neuen Zugangskarten werden ab Montag am Empfang ausgegeben. Alte Karten "
        "verlieren am Ende des Monats ihre Gültigkeit und können nicht verlängert "
        "werden. Bitte bringen Sie einen Lichtbildausweis mit. Für Besucherausweise "
        "wenden Sie sich bitte weiterhin an das Sekretariat.",
        "Wir stellen die Abfalltrennung im Büro um. Ab Mitte des Monats stehen auf "
        "jeder Etage getrennte Behälter für Papier, Verpackungen und Restmüll bereit. "
        "Die bisherigen Einzelkörbe an den Arbeitsplätzen entfallen. Die Reinigung "
        "erfolgt weiterhin täglich.",
    ],
    "Polish": [
        "Szanowni Państwo, w piątek stołówka będzie zamknięta z powodu prac "
        "konserwacyjnych. Ciepłe napoje będą dostępne w holu głównym przez cały "
        "dzień. Automat na drugim piętrze będzie uzupełniany codziennie. "
        "Przepraszamy za utrudnienia.",
        "Miejsca parkingowe w garażu podziemnym zostaną w przyszłym tygodniu ponownie "
        "oznakowane. Prosimy w tym czasie korzystać z parkingu dla gości od strony "
        "północnej. Wjazd od ulicy bocznej pozostaje otwarty, a szlaban będzie "
        "obsługiwany w ciągu dnia. Prace potrwają około trzech dni.",
        "Informujemy o próbnej ewakuacji w najbliższy wtorek o godzinie dziesiątej. "
        "Prosimy opuścić budynek najbliższym wyjściem i zebrać się na parkingu. "
        "Osoby odpowiedzialne za piętra sprawdzą pomieszczenia i zgłoszą stan "
        "osobowy. Ćwiczenia potrwają około dwudziestu minut.",
        "Nowe karty dostępu będziemy wydawać od poniedziałku w recepcji. Stare karty "
        "przestaną działać z końcem miesiąca i nie będą przedłużane. Prosimy o "
        "zabranie dokumentu ze zdjęciem. W sprawie kart dla gości prosimy kontaktować "
        "się z sekretariatem.",
    ],
    "Spanish": [
        "Estimados compañeros, el comedor permanecerá cerrado el viernes por trabajos "
        "de mantenimiento. Habrá bebidas calientes disponibles en el vestíbulo "
        "durante toda la jornada. La máquina de la segunda planta se repondrá cada "
        "día. Gracias por su comprensión.",
        "Las plazas de aparcamiento del sótano se volverán a señalizar la próxima "
        "semana. Durante esos días utilicen el aparcamiento de visitantes situado en "
        "el lado norte. El acceso por la calle lateral seguirá abierto y la barrera "
        "estará atendida durante el día. Los trabajos durarán unos tres días.",
        "Les informamos del simulacro de evacuación del próximo martes a las diez de "
        "la mañana. Salgan por la puerta más cercana y reúnanse en el aparcamiento. "
        "Los responsables de planta revisarán las salas y confirmarán el recuento. "
        "El simulacro durará unos veinte minutos.",
    ],
}

TITLES = {
    "German": ["Kantine — Wartungsarbeiten am Freitag", "Parkhaus — Neue Markierungen",
               "Brandschutzübung — Termin und Ablauf", "Neue Zugangskarten ab Montag",
               "Abfalltrennung im Büro — Umstellung"],
    "Polish": ["Stołówka — prace konserwacyjne w piątek", "Garaż — nowe oznakowanie miejsc",
               "Próbna ewakuacja — termin", "Nowe karty dostępu od poniedziałku"],
    "Spanish": ["Comedor — cierre por mantenimiento", "Aparcamiento — nueva señalización",
                "Simulacro de evacuación — martes"],
}

# File types whose native is written from the body, and therefore the only ones a
# language body can reach the extracted text through.
#
# This used to read ("Email -", "Office -", "PDF"), which swept in spreadsheets and
# presentations. Their writers take no body: make_xlsx and make_pptx have no such
# parameter, and build a metadata grid instead. A planted German spreadsheet came out
# of extraction as "Field Value Control Number DOC-0007214 Custodian Sandra Nguyen
# ... Title Neue Zugangskarten ab Montag" — English metadata with a German title
# stapled on. Nothing a classifier could call German, and 26 of the 250 planted
# documents on the medium tier were like that.
#
# Documents planted with a processing error are excluded for the same reason from the
# other end: Rule 12 gives them an empty sidecar on purpose, so a language planted
# there is a language nothing can read. That was another 17.
#
# Between them those two groups are the whole of the gap the widget showed: 150
# German planted and 122 reported, 100 Polish and 81. Not a classifier being
# imprecise, just documents that never carried the language in the first place.
#
# Rule 23 records the same shape of mistake for PI, and for the same reason: a
# body-derived sidecar held 39 of 102 seeded values because the spreadsheet scenario
# writes into cells and never touches the body. Anything that must survive extraction
# has to go through a writer that reads it.
BODY_BEARING = ("Email -", "Office - Word", "PDF")

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
            # Only file types whose native actually carries the body, and only
            # documents whose extraction is supposed to succeed. See BODY_BEARING.
            and d.get("Processing Status", "") != "Error"
            and d.get("File Type Category", "").startswith(BODY_BEARING)]
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
