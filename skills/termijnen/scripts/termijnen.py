#!/usr/bin/env python3
"""Rekenhulp procestermijnen (Nederlands recht).

Computes the last day of a procedural deadline and applies the Algemene
termijnenwet (Atw). Standard library only. Every rule below cites its source;
see references/bronnen.md for the verbatim texts and how they were checked.

Usage (from this skill's folder):
  python3 scripts/termijnen.py hoger-beroep-civiel --uitspraak 2026-01-31
  python3 scripts/termijnen.py hoger-beroep-civiel --uitspraak 2026-03-10 --kort-geding
  python3 scripts/termijnen.py cassatie-civiel --uitspraak 2026-02-27
  python3 scripts/termijnen.py bezwaar-beroep-awb --bekendmaking 2026-04-24
  python3 scripts/termijnen.py hoger-beroep-straf --uitspraak 2026-04-14
  python3 scripts/termijnen.py generiek --datum 2026-06-01 --aantal 10 --eenheid dagen --wettelijk
Add --json for machine-readable output.
"""
import argparse
import calendar
import datetime as dt
import json
import os
import sys

DISCLAIMER = "Controleer de uitkomst zelf; dit is een rekenhulp, geen advies."

WEEKDAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "feestdagen.json")

HR_2017 = ("HR 1 september 2017, ECLI:NL:HR:2017:2225, r.o. 3.4.1-3.4.4 (dag van de uitspraak "
           "telt niet mee; termijn eindigt aan het einde van de dag met hetzelfde nummer drie maanden "
           "later; bestaat die dag niet, dan op de laatste dag van die maand)")
HR_2004 = "HR 12 maart 2004, ECLI:NL:HR:2004:AO1315 (uitspraak 29-11-2002: cassatietermijn eindigde 28-02-2003)"


class Weigering(Exception):
    """Input outside what this tool can compute reliably. Message is Dutch."""


def fmt(d):
    return "%s %d %s %d" % (WEEKDAGEN[d.weekday()], d.day, MAANDEN[d.month - 1], d.year)


def parse_datum(s):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        raise Weigering("Ongeldige datum '%s'. Gebruik JJJJ-MM-DD, bijvoorbeeld 2026-01-31." % s)


def load_data(path=DATA_FILE):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    extra = {}
    for row in data["gelijkgestelde_dagen"]:
        extra[dt.date.fromisoformat(row["datum"])] = row["bron"]
    return {"jaren": tuple(data["gedekte_jaren"]), "extra": extra, "peildatum": data["peildatum"]}


def pasen(jaar):
    """Easter Sunday, Gregorian calendar (anonymous Gregorian / Meeus-Jones-Butcher algorithm).
    Checked in tests against the Hemelvaart dates implied by the Stcrt besluiten 2020-2028."""
    a = jaar % 19
    b, c = divmod(jaar, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    ll = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ll) // 451
    maand, dag = divmod(h + ll - 7 * m + 114, 31)
    return dt.date(jaar, maand, dag + 1)


def feestdagen(jaar, data):
    """Algemeen erkende feestdagen per art. 3 Atw for one year: {date: description}."""
    lo, hi = data["jaren"]
    if not lo <= jaar <= hi:
        raise Weigering(
            "Het jaar %d valt buiten de feestdagentabel (%d-%d). Gelijkgestelde dagen (art. 3 lid 3 Atw, "
            "Staatscourant) zijn voor dat jaar niet gecontroleerd; bereken deze termijn zelf." % (jaar, lo, hi))
    p = pasen(jaar)
    dagen = {
        dt.date(jaar, 1, 1): "Nieuwjaarsdag (art. 3 lid 1 Atw)",
        p - dt.timedelta(days=2): "Goede Vrijdag (art. 3 lid 2 Atw)",
        p + dt.timedelta(days=1): "tweede Paasdag (art. 3 lid 1 Atw)",
        dt.date(jaar, 5, 5): "5 mei (art. 3 lid 1 Atw)",
        p + dt.timedelta(days=39): "Hemelvaartsdag (art. 3 lid 1 Atw)",
        p + dt.timedelta(days=50): "tweede Pinksterdag (art. 3 lid 1 Atw)",
        dt.date(jaar, 12, 25): "eerste Kerstdag (art. 3 lid 1 Atw)",
        dt.date(jaar, 12, 26): "tweede Kerstdag (art. 3 lid 1 Atw)",
    }
    # Koningsdag: 'de dag waarop de verjaardag van de Koning wordt gevierd' (art. 3 lid 1 Atw).
    # Birthday 27 April. If 27 April is a Sunday it is celebrated on Saturday 26 April; both are
    # weekend days, so only 27 April on a weekday changes the outcome. Covered years start in 2020.
    koningsdag = dt.date(jaar, 4, 27)
    if koningsdag.weekday() < 5:
        dagen[koningsdag] = "Koningsdag (art. 3 lid 1 Atw)"
    for d, bron in data["extra"].items():
        if d.year == jaar:
            dagen[d] = "gelijkgestelde dag, %s (art. 3 lid 3 Atw)" % bron
    return dagen


def vrije_dag(d, data):
    """Returns a description if d is a Saturday, Sunday or Atw holiday, else None."""
    if d.weekday() == 5:
        return "zaterdag"
    if d.weekday() == 6:
        return "zondag"
    return feestdagen(d.year, data).get(d)


def plus_maanden(d, n):
    """Same day number n months later; last day of that month if it does not exist.
    Source: HR 2017:2225 r.o. 3.4.4 and HR 2004:AO1315."""
    y, m = divmod(d.month - 1 + n, 12)
    jaar, maand = d.year + y, m + 1
    laatste = calendar.monthrange(jaar, maand)[1]
    return dt.date(jaar, maand, min(d.day, laatste)), d.day > laatste


def ruwe_einde(datum, aantal, eenheid, stappen):
    """Last day before Atw. The day of `datum` itself is not counted; day 1 is the next day."""
    if eenheid == "dagen":
        einde = datum + dt.timedelta(days=aantal)
        stappen.append("Dag 1 is %s (de dag na %s telt als eerste dag). %d dagen: laatste dag %s."
                       % (fmt(datum + dt.timedelta(days=1)), fmt(datum), aantal, fmt(einde)))
    elif eenheid == "weken":
        einde = datum + dt.timedelta(days=7 * aantal)
        stappen.append("Dag 1 is %s. %d weken = %d dagen: laatste dag %s (zelfde weekdag als %s)."
                       % (fmt(datum + dt.timedelta(days=1)), aantal, 7 * aantal, fmt(einde), fmt(datum)))
    elif eenheid == "maanden":
        einde, afgekapt = plus_maanden(datum, aantal)
        if afgekapt:
            stappen.append("%d maanden na %s: de maand %s %d heeft geen dag %d, dus de termijn eindigt op de "
                           "laatste dag van die maand: %s." % (aantal, fmt(datum), MAANDEN[einde.month - 1],
                                                               einde.year, datum.day, fmt(einde)))
        else:
            stappen.append("%d maanden na %s: de dag met hetzelfde nummer is %s."
                           % (aantal, fmt(datum), fmt(einde)))
    else:
        raise Weigering("Onbekende eenheid '%s'. Kies dagen, weken of maanden." % eenheid)
    return einde


def atw_uitgesloten(aantal, eenheid):
    """Art. 4 sub a Atw: Atw does not apply to terms in hours, >90 days, >12 weeks, >3 months, or years."""
    if eenheid == "dagen" and aantal > 90:
        return "meer dan 90 dagen"
    if eenheid == "weken" and aantal > 12:
        return "meer dan twaalf weken"
    if eenheid == "maanden" and aantal > 3:
        return "meer dan drie maanden"
    return None


def pas_atw_toe(eerste_dag, einde, data, stappen):
    """Art. 1 lid 1 and art. 2 Atw. Returns the (possibly extended) last day."""
    reden = vrije_dag(einde, data)
    if not reden:
        stappen.append("Art. 1 lid 1 Atw: %s is geen zaterdag, zondag of algemeen erkende feestdag; "
                       "geen verlenging." % fmt(einde))
    while reden:
        stappen.append("Art. 1 lid 1 Atw: %s valt op een niet-werkdag (%s); de termijn wordt verlengd." % (fmt(einde), reden))
        einde = einde + dt.timedelta(days=1)
        reden = vrije_dag(einde, data)
    # Art. 2 Atw: a term of at least three days must contain at least two days that are not a
    # Saturday, Sunday or holiday.
    if (einde - eerste_dag).days + 1 >= 3:
        while sum(1 for i in range((einde - eerste_dag).days + 1)
                  if not vrije_dag(eerste_dag + dt.timedelta(days=i), data)) < 2:
            einde = einde + dt.timedelta(days=1)
            while vrije_dag(einde, data):
                einde = einde + dt.timedelta(days=1)
            stappen.append("Art. 2 Atw: de termijn bevatte minder dan twee werkdagen; verlengd tot %s."
                           % fmt(einde))
    stappen.append("Na toepassing van de Algemene termijnenwet: laatste dag %s." % fmt(einde))
    return einde


def controleer_dekking(eerste, laatste, data):
    lo, hi = data["jaren"]
    if eerste.year < lo or laatste.year > hi:
        raise Weigering(
            "De termijn loopt (deels) buiten %d-%d, de jaren waarvoor de feestdagen en de in de Staatscourant "
            "gelijkgestelde dagen (art. 3 lid 3 Atw) zijn gecontroleerd. Bereken deze termijn zelf." % (lo, hi))


def bereken(datum, aantal, eenheid, atw, data, grondslag, waarschuwingen, soort, invoer):
    stappen = []
    eerste_dag = datum + dt.timedelta(days=1)
    einde = ruwe_einde(datum, aantal, eenheid, stappen)
    # Coverage check on the raw window plus a margin for Atw extensions (max. a few days).
    controleer_dekking(eerste_dag, einde + dt.timedelta(days=7), data)
    if atw:
        uitsluiting = atw_uitgesloten(aantal, eenheid)
        if uitsluiting:
            stappen.append("Art. 4 onder a Atw: de wet geldt niet voor termijnen van %s; geen verlenging." % uitsluiting)
            grondslag.append("Art. 4 onder a Algemene termijnenwet")
        else:
            einde = pas_atw_toe(eerste_dag, einde, data, stappen)
            grondslag.append("Art. 1, 2 en 3 Algemene termijnenwet (BWBR0002448); gelijkgestelde dagen volgens "
                             "Stcrt. 2019/53179, 2022/7812 en 2025/24713")
    return {
        "soort": soort,
        "invoer": invoer,
        "laatste_dag": einde.isoformat(),
        "laatste_dag_tekst": fmt(einde),
        "stappen": stappen,
        "grondslag": grondslag,
        "waarschuwingen": waarschuwingen,
        "feestdagentabel_peildatum": data["peildatum"],
        "disclaimer": DISCLAIMER,
    }


def hoger_beroep_civiel(uitspraak, kort_geding, data):
    if kort_geding:
        grondslag = ["Art. 339 lid 2 Rv: termijn van beroep van een vonnis in kort geding is vier weken, "
                     "te rekenen van de dag van de uitspraak (lid 1)", HR_2017]
        waarsch = ["De telling in weken (dag van de uitspraak telt niet mee) is afgeleid van de regel in "
                   "HR 2017:2225 voor de driemaandentermijn; niet door de HR voor weken uitgesproken."]
        return bereken(uitspraak, 4, "weken", True, data, grondslag, waarsch,
                       "Hoger beroep civiel, kort geding (art. 339 lid 2 Rv)",
                       {"uitspraak": uitspraak.isoformat(), "kort_geding": True})
    grondslag = ["Art. 339 lid 1 Rv: drie maanden, te rekenen van de dag van de uitspraak", HR_2017, HR_2004]
    waarsch = ["Geldt voor vonnissen (dagvaardingsprocedure). Voor beschikkingen geldt art. 358 Rv; "
               "tussenvonnissen: zie art. 337 Rv. Niet door deze rekenhulp gecontroleerd."]
    return bereken(uitspraak, 3, "maanden", True, data, grondslag, waarsch,
                   "Hoger beroep civiel (art. 339 lid 1 Rv)", {"uitspraak": uitspraak.isoformat(), "kort_geding": False})


def cassatie_civiel(uitspraak, kort_geding, data):
    if kort_geding:
        grondslag = ["Art. 402 lid 2 Rv: bij een verkorte appeltermijn is de cassatietermijn het dubbele "
                     "daarvan; kort geding (art. 339 lid 2 Rv: vier weken) geeft acht weken", HR_2017]
        waarsch = ["De telling in weken is afgeleid van de regel in HR 2017:2225; niet door de HR voor weken "
                   "uitgesproken."]
        return bereken(uitspraak, 8, "weken", True, data, grondslag, waarsch,
                       "Cassatie civiel, kort geding (art. 402 lid 2 Rv)",
                       {"uitspraak": uitspraak.isoformat(), "kort_geding": True})
    grondslag = ["Art. 402 lid 1 Rv: drie maanden, te rekenen van de dag van de uitspraak", HR_2017, HR_2004]
    waarsch = ["Andere wettelijk verkorte cassatietermijnen (bijv. in faillissementszaken) worden niet "
               "ondersteund; controleer of er een bijzondere termijn geldt."]
    return bereken(uitspraak, 3, "maanden", True, data, grondslag, waarsch,
                   "Cassatie civiel (art. 402 lid 1 Rv)", {"uitspraak": uitspraak.isoformat(), "kort_geding": False})


def bezwaar_beroep_awb(bekendmaking, data):
    grondslag = ["Art. 6:7 Awb: termijn voor bezwaar- of beroepschrift is zes weken",
                 "Art. 6:8 lid 1 Awb: de termijn vangt aan met ingang van de dag na die waarop het besluit op de "
                 "voorgeschreven wijze is bekendgemaakt"]
    waarsch = ["Alleen art. 6:8 lid 1 Awb (bekendmaking). Andere aanvangsmomenten (art. 6:8 lid 2-4 Awb) en "
               "bijzondere wetten met afwijkende termijnen worden niet ondersteund.",
               "Tijdigheid: art. 6:9 Awb (ontvangst voor einde termijn; bij verzending per post volstaat terpostbezorging "
               "voor einde termijn mits ontvangst binnen een week daarna)."]
    return bereken(bekendmaking, 6, "weken", True, data, grondslag, waarsch,
                   "Bezwaar of beroep bestuursrecht (art. 6:7 en 6:8 lid 1 Awb)",
                   {"bekendmaking": bekendmaking.isoformat()})


def hoger_beroep_straf(uitspraak, data):
    grondslag = ["Art. 408 lid 1 Sv: hoger beroep binnen veertien dagen na de einduitspraak (in de gevallen "
                 "van lid 1 onder a-d)",
                 "Art. 136 lid 1 Sv verwijst voor 'dag' naar de Algemene termijnenwet"]
    waarsch = ["Alleen de gevallen van art. 408 lid 1 Sv. In andere gevallen loopt de termijn van veertien dagen "
               "vanaf het moment dat de einduitspraak de verdachte bekend is (lid 2): gebruik dan 'generiek' met "
               "die datum en --wettelijk."]
    return bereken(uitspraak, 14, "dagen", True, data, grondslag, waarsch,
                   "Hoger beroep strafrecht (art. 408 lid 1 Sv)", {"uitspraak": uitspraak.isoformat()})


def generiek(datum, aantal, eenheid, wettelijk, data):
    if aantal < 1 or aantal > 3650:
        raise Weigering("Aantal moet tussen 1 en 3650 liggen.")
    grondslag = []
    waarsch = ["Telling: de dag van de startdatum telt niet mee; dag 1 is de volgende dag. Dat volgt de regel voor "
               "'te rekenen van' (HR 2017:2225) en 'na' (art. 6:8 lid 1 Awb). Controleer of de formulering van "
               "uw termijn dezelfde telling meebrengt."]
    if eenheid == "maanden":
        grondslag.append(HR_2017)
    if wettelijk:
        waarsch.append("De Atw geldt alleen voor termijnen gesteld in een wet (art. 1 Atw) of AMvB (art. 5 Atw), "
                       "niet voor terugrekentermijnen (art. 1 lid 2 Atw) of termijnen van vrijheidsbeneming en "
                       "bekendmaking/inwerkingtreding (art. 4 onder b en c Atw).")
    else:
        waarsch.append("Algemene termijnenwet niet toegepast (geen --wettelijk). Contractuele termijnen: de Atw "
                       "geldt niet rechtstreeks.")
    return bereken(datum, aantal, eenheid, wettelijk, data, grondslag, waarsch,
                   "Generieke termijn: %d %s na %s" % (aantal, eenheid, datum.isoformat()),
                   {"datum": datum.isoformat(), "aantal": aantal, "eenheid": eenheid, "wettelijk": wettelijk})


def als_tekst(r):
    regels = [r["soort"], "", "Uitkomst: laatste dag is %s (%s)." % (r["laatste_dag_tekst"], r["laatste_dag"]), "",
              "Berekening:"]
    regels += ["  %d. %s" % (i + 1, s) for i, s in enumerate(r["stappen"])]
    regels += ["", "Juridische grondslag:"] + ["  - " + g for g in r["grondslag"]]
    if r["waarschuwingen"]:
        regels += ["", "Let op:"] + ["  - " + w for w in r["waarschuwingen"]]
    regels += ["  - Feestdagentabel bijgewerkt tot %s; later gepubliceerde gelijkstellingen ontbreken."
               % r["feestdagentabel_peildatum"], "", r["disclaimer"]]
    return "\n".join(regels)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rekenhulp procestermijnen met Algemene termijnenwet.")
    sub = ap.add_subparsers(dest="soort", required=True)
    p = sub.add_parser("hoger-beroep-civiel", help="art. 339 Rv")
    p.add_argument("--uitspraak", required=True, help="datum van de uitspraak, JJJJ-MM-DD")
    p.add_argument("--kort-geding", action="store_true")
    p = sub.add_parser("cassatie-civiel", help="art. 402 Rv")
    p.add_argument("--uitspraak", required=True)
    p.add_argument("--kort-geding", action="store_true")
    p = sub.add_parser("bezwaar-beroep-awb", help="art. 6:7 en 6:8 Awb")
    p.add_argument("--bekendmaking", required=True, help="datum van bekendmaking van het besluit")
    p = sub.add_parser("hoger-beroep-straf", help="art. 408 lid 1 Sv")
    p.add_argument("--uitspraak", required=True)
    p = sub.add_parser("generiek", help="N dagen/weken/maanden na een datum")
    p.add_argument("--datum", required=True)
    p.add_argument("--aantal", required=True, type=int)
    p.add_argument("--eenheid", required=True, choices=["dagen", "weken", "maanden"])
    p.add_argument("--wettelijk", action="store_true", help="wettelijke termijn: pas de Algemene termijnenwet toe")
    for s in sub.choices.values():
        s.add_argument("--json", action="store_true", help="uitvoer als JSON")
    args = ap.parse_args(argv)
    try:
        data = load_data()
        if args.soort == "hoger-beroep-civiel":
            r = hoger_beroep_civiel(parse_datum(args.uitspraak), args.kort_geding, data)
        elif args.soort == "cassatie-civiel":
            r = cassatie_civiel(parse_datum(args.uitspraak), args.kort_geding, data)
        elif args.soort == "bezwaar-beroep-awb":
            r = bezwaar_beroep_awb(parse_datum(args.bekendmaking), data)
        elif args.soort == "hoger-beroep-straf":
            r = hoger_beroep_straf(parse_datum(args.uitspraak), data)
        else:
            r = generiek(parse_datum(args.datum), args.aantal, args.eenheid, args.wettelijk, data)
    except Weigering as e:
        if args.json:
            print(json.dumps({"fout": str(e), "disclaimer": DISCLAIMER}, ensure_ascii=False, indent=2))
        else:
            print("Geen berekening: %s\n\n%s" % (e, DISCLAIMER))
        return 2
    print(json.dumps(r, ensure_ascii=False, indent=2) if args.json else als_tekst(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
