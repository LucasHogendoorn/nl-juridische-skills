#!/usr/bin/env python3
"""Tuchtrechtuitspraken zoeken en ophalen via de officiële KOOP SRU-dienst.

Gebruik (vanuit de skillmap):
    python3 scripts/tuchtrecht.py zoek belangenverstrengeling --domein advocaten --van 2024-01-01 --tot 2024-12-31
    python3 scripts/tuchtrecht.py zoek huisarts dossiervoering --beroep arts
    python3 scripts/tuchtrecht.py zoek zorgplicht --domein notarissen -n 20
    python3 scripts/tuchtrecht.py haal ECLI:NL:TGZRAMS:2024:123            # volledige tekst
    python3 scripts/tuchtrecht.py haal ECLI:NL:TGZRAMS:2024:123 -o uitspraak.md
    python3 scripts/tuchtrecht.py waarden                                # geldige domeinen/beroepen

Bron: https://repository.overheid.nl/sru, collectie c.product-area==tuchtrecht
(dezelfde uitspraken als tuchtrecht.overheid.nl). Alleen gepubliceerde uitspraken.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import koop_sru_client as k  # noqa: E402
import nl_http  # noqa: E402

# Values of w.instantieDomein and w.beroepsgroep (SRU scan, 2026-09-23).
DOMEINEN = {
    "advocaten": "Advocaten", "advocaat": "Advocaten",
    "gezondheidszorg": "Gezondheidszorg", "zorg": "Gezondheidszorg",
    "notarissen": "Notarissen", "notaris": "Notarissen",
    "gerechtsdeurwaarders": "Gerechtsdeurwaarders", "deurwaarder": "Gerechtsdeurwaarders",
    "accountants": "Accountants", "accountant": "Accountants",
    "diergeneeskundigen": "Diergeneeskundigen", "dierenarts": "Diergeneeskundigen",
    "scheepvaart": "Scheepvaart",
    "akkerbouw": "Akkerbouw", "pluimvee en eieren": "Pluimvee en eieren", "vee en vlees": "Vee en vlees",
}
BEROEPEN = {
    "arts": "Arts", "huisarts": "Arts", "medisch specialist": "Arts",
    "tandarts": "Tandarts", "verpleegkundige": "Verpleegkundige",
    "gezondheidszorgpsycholoog": "Gezondheidszorgpsycholoog", "gz-psycholoog": "Gezondheidszorgpsycholoog",
    "psychotherapeut": "Psychotherapeut", "fysiotherapeut": "Fysiotherapeut",
    "apotheker": "Apotheker", "verloskundige": "Verloskundige",
}
DATUM = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def domein_waarde(naam: str | None) -> str | None:
    if not naam:
        return None
    w = DOMEINEN.get(naam.strip().lower())
    if not w:
        raise SystemExit(f"Onbekend --domein '{naam}'. Kies uit: "
                         + ", ".join(sorted(set(DOMEINEN.values()))))
    return w


# Word used to find the profession in the inhoudsindicatie. Needed because decisions
# published after ±september 2021 carry no w.beroepsgroep metadata (checked 2026-09-23).
BEROEP_WOORD = {
    "gz-psycholoog": "psycholoog", "gezondheidszorgpsycholoog": "psycholoog",
    "medisch specialist": "specialist",
}


def beroep_clause(naam: str | None) -> str:
    """CQL for a health profession: metadata field (pre-±2021 decisions) OR the word in the
    inhoudsindicatie (all years). 'huisarts' has no own field: Arts + the word 'huisarts'."""
    if not naam:
        return ""
    key = naam.strip().lower()
    waarde = BEROEPEN.get(key)
    if not waarde:
        raise SystemExit(f"Onbekend --beroep '{naam}'. Kies uit: " + ", ".join(sorted(set(BEROEPEN))))
    woord = BEROEP_WOORD.get(key, key)
    in_samenvatting = k.cql_clause("dt.description", woord, "=")
    if key == "huisarts":
        veld = f'({k.cql_clause("w.beroepsgroep", waarde)} AND {k.cql_clause("cql.textAndIndexes", woord, "=")})'
    else:
        veld = k.cql_clause("w.beroepsgroep", waarde)
    return f"({in_samenvatting} OR {veld})"


def bouw_zoekvraag(termen: list, domein: str | None = None, beroep: str | None = None,
                   van: str | None = None, tot: str | None = None, college: str | None = None,
                   uitkomst: str | None = None, sorteer: str = "datum", strikt: bool = False,
                   onderwerp: str | None = None) -> str:
    clauses = [k.cql_clause("c.product-area", "tuchtrecht")]
    dom = domein_waarde(domein)
    if beroep and not dom:
        dom = "Gezondheidszorg"
    if dom:
        clauses.append(k.cql_clause("w.instantieDomein", dom))
    clauses.append(beroep_clause(beroep))
    index = "dt.description" if strikt else "cql.textAndIndexes"
    for t in termen:
        clauses.append(k.cql_clause(index, t, "="))
    if onderwerp:
        clauses.append("(" + k.cql_clause("w.subonderwerp", onderwerp, "=") + " OR "
                       + k.cql_clause("dt.subject", onderwerp, "=") + ")")
    for label, d in (("--van", van), ("--tot", tot)):
        if d and not DATUM.match(d):
            raise SystemExit(f"{label} verwacht een datum als JJJJ-MM-DD, niet '{d}'.")
    if van:
        clauses.append(f"w.uitspraakdatum>={van}")
    if tot:
        clauses.append(f"w.uitspraakdatum<={tot}")
    if college:
        clauses.append(k.cql_clause("dt.creator", college, "="))
    if uitkomst:
        clauses.append("(" + k.cql_clause("w.beslissing", uitkomst, "=") + " OR "
                       + k.cql_clause("dt.description", uitkomst, "=") + ")")
    q = k.cql_and(*clauses)
    if sorteer == "datum":
        q = k.with_sort(q, "w.uitspraakdatum")
    return q


def samenvatting(record: k.Record, max_len: int = 600) -> str:
    tekst = " ".join(record.descriptions).strip()
    if len(tekst) > max_len:
        tekst = tekst[:max_len].rsplit(" ", 1)[0] + " […]"
    return tekst


def regel(record: k.Record, i: int) -> str:
    college = record.creator or record.type
    onderwerpen = list(dict.fromkeys(record.subjects + record.getall("subonderwerp")))
    onderwerp = "; ".join(onderwerpen)
    bits = [f"{i}. **{record.identifier}** — {college}, {record.date}"]
    meta = []
    if record.get("zaaknummer"):
        meta.append(f"zaaknr. {record.get('zaaknummer')}")
    if record.get("beroepsgroep"):
        meta.append(record.get("beroepsgroep"))
    if record.get("beslissing"):
        meta.append(f"beslissing: {record.get('beslissing')}")
    if onderwerp:
        meta.append(f"onderwerp: {onderwerp}")
    if meta:
        bits.append("   " + " · ".join(meta))
    sam = samenvatting(record)
    if sam:
        bits.append(textwrap.indent(textwrap.fill(sam, 100), "   > "))
    bits.append(f"   {record.preferred_url}")
    return "\n".join(bits)


def cmd_zoek(args) -> int:
    if not (args.termen or args.domein or args.beroep):
        print("Geef minstens een zoekterm, --domein of --beroep.", file=sys.stderr)
        return 2
    q = bouw_zoekvraag(args.termen, args.domein, args.beroep, args.van, args.tot, args.college,
                       args.uitkomst, args.sorteer, args.strikt, args.onderwerp)
    res = k.search(q, max_records=args.n)
    if args.json:
        print(json.dumps({"query": q, "total": res.total, "records": [r.as_dict() for r in res.records]},
                         ensure_ascii=False, indent=1))
        return 0
    volgorde = "nieuwste eerst" if args.sorteer == "datum" else "volgorde van de zoekdienst"
    print(f"Zoekvraag (CQL): `{q}`\n{res.total} uitspraken; eerste {len(res.records)} ({volgorde}):\n")
    for i, r in enumerate(res.records, 1):
        print(regel(r, i) + "\n")
    if res.total == 0:
        print("Geen resultaten. Tips: minder of andere termen (elke term moet voorkomen), "
              "ruimere datumgrenzen, of zonder --domein.")
    return 0


def cmd_haal(args) -> int:
    ecli = args.ecli.strip()
    if not re.match(r"^ECLI:NL:[A-Z0-9]+:\d{4}:[A-Z0-9.]+$", ecli, re.I):
        print(f"'{ecli}' lijkt geen ECLI (verwacht bijv. ECLI:NL:TADRAMS:2024:20).", file=sys.stderr)
        return 2
    record = k.get_record(ecli.upper(), product_area="tuchtrecht")
    if record is None:
        print(f"{ecli} niet gevonden in de tuchtrechtcollectie. Uitspraken van de gewone rechter "
              "(ECLI:NL:HR, RBAMS, ...) staan op rechtspraak.nl, niet hier.", file=sys.stderr)
        return 1
    md = k.uitspraak_to_markdown(k.fetch_xml(record))
    if args.meta:
        md = md.split("\n## Uitspraak", 1)[0]
    if args.uitvoer:
        with open(args.uitvoer, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"Geschreven: {args.uitvoer} ({len(md)} tekens).")
    else:
        print(md)
    return 0


def cmd_waarden(args) -> int:
    print("Domeinen (--domein):", ", ".join(sorted(set(DOMEINEN.values()))))
    print("Beroepen gezondheidszorg (--beroep):", ", ".join(sorted(set(BEROEPEN))))
    print("(--beroep zoekt het beroepsveld óf het woord in de inhoudsindicatie: na ±2021 ontbreekt het veld.)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Tuchtrechtuitspraken via de KOOP SRU-dienst.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    z = sub.add_parser("zoek", help="uitspraken zoeken")
    z.add_argument("termen", nargs="*", help="zoektermen; elke term/zinsnede moet voorkomen")
    z.add_argument("--domein", help="advocaten, gezondheidszorg, notarissen, gerechtsdeurwaarders, "
                                    "accountants, diergeneeskundigen, ...")
    z.add_argument("--beroep", help="gezondheidszorg: arts, huisarts, tandarts, verpleegkundige, ...")
    z.add_argument("--van", help="uitspraakdatum vanaf (JJJJ-MM-DD)")
    z.add_argument("--tot", help="uitspraakdatum tot en met (JJJJ-MM-DD)")
    z.add_argument("--college", help="woord(en) uit de naam van het college, bijv. 'Hof van Discipline'")
    z.add_argument("--uitkomst", help="woord in beslissing of inhoudsindicatie, bijv. 'berisping', 'gegrond'")
    z.add_argument("--onderwerp", help="onderwerp/subonderwerp, bijv. 'Belangenconflict'")
    z.add_argument("--strikt", action="store_true",
                   help="zoektermen moeten in de inhoudsindicatie staan (preciezer, minder treffers)")
    z.add_argument("--sorteer", choices=["datum", "relevantie"], default="datum")
    z.add_argument("-n", type=int, default=10)
    z.add_argument("--json", action="store_true")
    z.set_defaults(func=cmd_zoek)

    h = sub.add_parser("haal", help="volledige uitspraak ophalen")
    h.add_argument("ecli")
    h.add_argument("--meta", action="store_true", help="alleen kop en inhoudsindicatie")
    h.add_argument("-o", "--uitvoer")
    h.set_defaults(func=cmd_haal)

    w = sub.add_parser("waarden", help="geldige waarden voor --domein en --beroep")
    w.set_defaults(func=cmd_waarden)

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except (k.SruError, nl_http.FetchError) as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
