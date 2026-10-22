#!/usr/bin/env python3
"""Rekenhulp wettelijke rente (art. 6:119 BW) en wettelijke handelsrente (art. 6:119a BW).

Standard library only. Sources per rule are cited in comments; verbatim texts and
checks are in references/bronnen.md; the rate table with a source per row is in
data/rentetabel.json.

Usage (from this skill's folder):
  python3 scripts/wettelijke_rente.py --soort niet-handel --hoofdsom 12500 \
      --vanaf 2019-03-01 --tot 2026-03-01 --betaling 2022-06-15:5000
  python3 scripts/wettelijke_rente.py --soort handel --overeenkomst-datum 2023-05-01 \
      --hoofdsom 8000 --vanaf 2024-02-01 --tot 2026-08-31
Add --json for machine-readable output.
"""
import argparse
import datetime as dt
import json
import os
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

DISCLAIMER = "Controleer de uitkomst zelf; dit is een rekenhulp, geen advies."
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "rentetabel.json")
CENT = Decimal("0.01")
NIEUWE_HANDELSRENTE = dt.date(2013, 3, 16)  # Stb. 2012, 647 in force (Stb. 2013, 9)
EEN_DAG = dt.timedelta(days=1)


class Weigering(Exception):
    """Input outside what this tool can compute reliably. Message is Dutch."""


def c(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def eur(x):
    s = "{:,.2f}".format(c(Decimal(x)))
    return "EUR " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct_tekst(p):
    return ("%s%%" % p.normalize()).replace(".", ",")


def bedrag(s, naam):
    try:
        v = Decimal(str(s).replace(",", "."))
    except InvalidOperation:
        raise Weigering("Ongeldig bedrag voor %s: '%s'." % (naam, s))
    if v < 0:
        raise Weigering("Negatief bedrag voor %s is niet toegestaan." % naam)
    return v


def datum(s, naam):
    try:
        return dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        raise Weigering("Ongeldige datum voor %s: '%s'. Gebruik JJJJ-MM-DD." % (naam, s))


def load_tabel(path=DATA_FILE):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    def rijen(key):
        return [(dt.date.fromisoformat(r["vanaf"]), Decimal(r["pct"]), r["bron"]) for r in data[key]]

    return {"niet-handel": rijen("niet_handel"), "handel": rijen("handel"),
            "tot": dt.date.fromisoformat(data["geldig_tot_en_met"]), "peildatum": data["peildatum"]}


def tarief(tabel, d):
    gevonden = None
    for vanaf, pct, bron in tabel:
        if vanaf <= d:
            gevonden = (vanaf, pct, bron)
    if gevonden is None:
        raise Weigering("Geen rentepercentage bekend voor %s." % d.isoformat())
    return gevonden


def jubileum(start, k):
    """Anniversary k years after start (29 February -> 28 February in non-leap years)."""
    try:
        return start.replace(year=start.year + k)
    except ValueError:
        return start.replace(year=start.year + k, day=28)


def controleer(soort, vanaf, tot, overeenkomst, betalingen, tabel):
    if tot < vanaf:
        raise Weigering("De einddatum ligt voor de begindatum.")
    if tot > tabel["tot"]:
        raise Weigering("Rentepercentages na %s zijn niet bekend of niet gecontroleerd." % tabel["tot"].isoformat())
    if soort == "niet-handel" and vanaf < dt.date(2002, 1, 1):
        raise Weigering("Rente voor 1 januari 2002 wordt niet ondersteund (tabel begint bij Stb. 2001, 630).")
    if soort == "handel":
        if overeenkomst is None:
            raise Weigering("Voor handelsrente is --overeenkomst-datum verplicht.")
        if overeenkomst < NIEUWE_HANDELSRENTE or vanaf < NIEUWE_HANDELSRENTE:
            raise Weigering(
                "Handelsrente voor overeenkomsten gesloten voor 16 maart 2013, of over perioden voor die datum, wordt "
                "niet berekend. Art. 183a Overgangswet NBW sluit art. 6:120 lid 2 (8 procentpunten) niet uit voor "
                "oude overeenkomsten, maar de memorie van toelichting (Kamerstukken II 33171, nr. 3) spreekt van "
                "eerbiedigende werking. Die vraag is niet opgelost; bereken dit zelf.")
        if overeenkomst > vanaf:
            raise Weigering("De overeenkomst kan niet na de eerste rentedag zijn gesloten.")
    for d, _ in betalingen:
        if not vanaf <= d <= tot:
            raise Weigering("Betaling op %s valt buiten de renteperiode %s t/m %s."
                            % (d.isoformat(), vanaf.isoformat(), tot.isoformat()))


def bereken(soort, hoofdsom, vanaf, tot, kosten=Decimal(0), betalingen=(), overeenkomst=None,
            dagbasis="365", tabel=None):
    """Interest per day over [vanaf, tot] inclusive. Rounds each segment's interest to cents."""
    tabel = tabel or load_tabel()
    betalingen = sorted(betalingen)
    controleer(soort, vanaf, tot, overeenkomst, betalingen, tabel)
    rentetabel = tabel[soort]
    stappen, waarsch = [], []
    per_dag_bet = {}
    for d, b in betalingen:
        per_dag_bet[d] = per_dag_bet.get(d, Decimal(0)) + b

    # Split points: the first day of each new segment.
    grenzen = set()
    for vanaf_r, _, _ in rentetabel:
        if vanaf < vanaf_r <= tot:
            grenzen.add(vanaf_r)
    k = 1
    while jubileum(vanaf, k) <= tot:
        grenzen.add(jubileum(vanaf, k))
        k += 1
    for d in per_dag_bet:
        if d < tot:
            grenzen.add(d + EEN_DAG)
    starts = [vanaf] + sorted(grenzen)

    hoofd, kap, open_r, kst = hoofdsom, Decimal(0), Decimal(0), kosten
    totaal_rente = Decimal(0)
    jaar_nr = 1
    for i, s in enumerate(starts):
        e = starts[i + 1] - EEN_DAG if i + 1 < len(starts) else tot
        dagen = (e - s).days + 1
        _, pct, bron = tarief(rentetabel, s)
        basis = hoofd + kap
        jaar_start, jaar_eind = jubileum(vanaf, jaar_nr - 1), jubileum(vanaf, jaar_nr)
        noemer = Decimal(365) if dagbasis == "365" else Decimal((jaar_eind - jaar_start).days)
        rente = c(basis * pct / 100 * dagen / noemer)
        open_r += rente
        totaal_rente += rente
        stappen.append("%s t/m %s: %d %s x %s x %s / %s = %s  [%s]"
                       % (s.isoformat(), e.isoformat(), dagen, "dag" if dagen == 1 else "dagen", eur(basis),
                          pct_tekst(pct), noemer, eur(rente), bron))
        # Payment at the end of day e (interest runs up to and including the payment day, cf. art. 6:119a lid 1).
        if e in per_dag_bet:
            b = per_dag_bet[e]
            deel_k = min(b, kst)
            kst -= deel_k
            rest = b - deel_k
            deel_kap = min(rest, kap)
            kap -= deel_kap
            rest -= deel_kap
            deel_open = min(rest, open_r)
            open_r -= deel_open
            rest -= deel_open
            if rest > hoofd:
                raise Weigering("De betaling van %s op %s is hoger dan het totaal openstaande bedrag."
                                % (eur(b), e.isoformat()))
            hoofd -= rest
            stappen.append("Betaling %s op %s (art. 6:44 lid 1 BW): kosten %s, rente %s, hoofdsom %s. "
                           "Resterende hoofdsom %s." % (eur(b), e.isoformat(), eur(deel_k),
                                                         eur(deel_kap + deel_open), eur(rest), eur(hoofd)))
        # Capitalisation after each full year (art. 6:119 lid 2 / 6:119a lid 3 BW).
        if e + EEN_DAG == jaar_eind:
            if open_r:
                stappen.append("Einde rentejaar %d (%s): rente %s bij de grondslag gevoegd (art. %s BW)."
                               % (jaar_nr, e.isoformat(), eur(open_r),
                                  "6:119 lid 2" if soort == "niet-handel" else "6:119a lid 3"))
            kap += open_r
            open_r = Decimal(0)
            jaar_nr += 1

    rente_open = kap + open_r
    totaal = hoofd + rente_open + kst
    if dagbasis == "365":
        waarsch.append("Dagberekening: rente per dag = jaarpercentage / 365, ook in schrikkeljaren. Wet en besluiten "
                       "schrijven geen dagtelling voor; kies --dagbasis jaar voor delen door de werkelijke lengte "
                       "van het renteljaar.")
    if betalingen:
        waarsch.append("Toerekening van betalingen: eerst kosten, dan alle tot en met de betaaldag opgelopen rente "
                       "(eerst gekapitaliseerde, dan lopende), dan hoofdsom. Het onderscheid 'verschenen' en "
                       "'lopende' rente in art. 6:44 lid 1 BW is zo gelezen; controleer dit.")
    if kosten:
        waarsch.append("Over de opgegeven kosten wordt geen rente berekend.")
    waarsch.append("De rente loopt van de begindatum tot en met de einddatum; controleer zelf de juiste "
                   "begindatum (verzuim, art. 6:119 BW; dag na de uiterste betaaldag, art. 6:119a lid 1-2 BW).")
    grondslag = ["Art. 6:119 lid 1 en 2 BW (wettelijke rente, jaarlijkse kapitalisatie); percentages bij AMvB "
                 "(art. 6:120 lid 1 BW), zie de bron per regel" if soort == "niet-handel" else
                 "Art. 6:119a lid 1 en 3 BW (handelsrente, jaarlijkse kapitalisatie); art. 6:120 lid 2 BW: "
                 "ECB-herfinancieringsrente + 8 procentpunten per halfjaar (Stb. 2012, 647)"]
    if betalingen:
        grondslag.append("Art. 6:44 lid 1 BW (toerekening: kosten, verschenen rente, hoofdsom en lopende rente)")
    return {
        "soort": soort,
        "uitkomst": "Rente %s; openstaand op %s: hoofdsom %s + rente %s + kosten %s = %s"
                    % (eur(totaal_rente), tot.isoformat(), eur(hoofd), eur(rente_open), eur(kst), eur(totaal)),
        "totaal_rente_berekend": str(c(totaal_rente)),
        "open_hoofdsom": str(c(hoofd)), "open_rente": str(c(rente_open)), "open_kosten": str(c(kst)),
        "totaal_open": str(c(totaal)),
        "stappen": stappen, "grondslag": grondslag, "waarschuwingen": waarsch,
        "rentetabel_peildatum": tabel["peildatum"], "disclaimer": DISCLAIMER,
    }


def als_tekst(r):
    titel = ("Wettelijke rente (art. 6:119 BW)" if r["soort"] == "niet-handel"
             else "Wettelijke handelsrente (art. 6:119a BW)")
    regels = [titel, "", "Uitkomst: " + r["uitkomst"], "", "Berekening:"]
    regels += ["  %d. %s" % (i + 1, s) for i, s in enumerate(r["stappen"])]
    regels += ["", "Juridische grondslag:"] + ["  - " + g for g in r["grondslag"]]
    regels += ["", "Let op:"] + ["  - " + w for w in r["waarschuwingen"]]
    regels += ["  - Rentetabel bijgewerkt tot %s." % r["rentetabel_peildatum"], "", r["disclaimer"]]
    return "\n".join(regels)


def parse_betaling(s):
    if ":" not in s:
        raise Weigering("Betaling als DATUM:BEDRAG, bijvoorbeeld 2022-06-15:5000.")
    d, b = s.split(":", 1)
    return datum(d, "--betaling"), bedrag(b, "--betaling")


def main(argv=None):
    p = argparse.ArgumentParser(description="Rekenhulp wettelijke rente en handelsrente.")
    p.add_argument("--soort", required=True, choices=["niet-handel", "handel"])
    p.add_argument("--hoofdsom", required=True)
    p.add_argument("--vanaf", required=True, help="eerste dag waarover rente loopt (JJJJ-MM-DD)")
    p.add_argument("--tot", required=True, help="laatste dag waarover rente loopt, bijv. betaaldag (JJJJ-MM-DD)")
    p.add_argument("--kosten", default="0", help="kosten (bijv. incassokosten), geen rente hierover")
    p.add_argument("--betaling", action="append", default=[], help="deelbetaling DATUM:BEDRAG (herhaalbaar)")
    p.add_argument("--overeenkomst-datum", help="datum sluiten overeenkomst (verplicht bij handel)")
    p.add_argument("--dagbasis", choices=["365", "jaar"], default="365")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    try:
        r = bereken(a.soort, bedrag(a.hoofdsom, "--hoofdsom"), datum(a.vanaf, "--vanaf"), datum(a.tot, "--tot"),
                    bedrag(a.kosten, "--kosten"), [parse_betaling(b) for b in a.betaling],
                    datum(a.overeenkomst_datum, "--overeenkomst-datum") if a.overeenkomst_datum else None,
                    a.dagbasis)
    except Weigering as e:
        if a.json:
            print(json.dumps({"fout": str(e), "disclaimer": DISCLAIMER}, ensure_ascii=False, indent=2))
        else:
            print("Geen berekening: %s\n\n%s" % (e, DISCLAIMER))
        return 2
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else als_tekst(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
