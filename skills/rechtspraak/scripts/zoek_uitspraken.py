#!/usr/bin/env python3
"""Zoek in de ECLI-index van de open data van de Rechtspraak (data.rechtspraak.nl).

Let op: de officiële API filtert alleen op metadata (instantie, datum, rechtsgebied,
soort, wijzigingsdatum, LJN). Er is GEEN zoeken op trefwoord in de tekst.
Met --trefwoord wordt lokaal gefilterd op de titel en de (ingekorte) samenvatting
van de opgehaalde resultaten; dat is geen full-text search.

Voorbeelden:
    python3 scripts/zoek_uitspraken.py --instantie HR --van 2026-09-01 --tot 2026-09-22 --soort uitspraak
    python3 scripts/zoek_uitspraken.py --instantie RBAMS --rechtsgebied arbeidsrecht --van 2026-08-01 --tot 2026-08-31 --met-tekst
    python3 scripts/zoek_uitspraken.py --instantie GHARL --rechtsgebied arbeidsrecht --van 2026-01-01 --trefwoord concurrentiebeding
    python3 scripts/zoek_uitspraken.py --ljn AG4158
    python3 scripts/zoek_uitspraken.py --lijst-instanties

Exitcodes: 0 = gelukt, 1 = ongeldige invoer, 2 = netwerk-/serverfout.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nl_http  # noqa: E402
import rechtspraak_client as rc  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Zoek uitspraken op metadata via data.rechtspraak.nl.")
    ap.add_argument("--instantie", action="append",
                    help="ECLI-code van de instantie (HR, PHR, RVS, CRVB, CBB, GHAMS, RBAMS, ...) of volledige URI. "
                         "Herhaal voor meerdere (OF).")
    ap.add_argument("--van", help="Uitspraakdatum vanaf (JJJJ-MM-DD).")
    ap.add_argument("--tot", help="Uitspraakdatum tot en met (JJJJ-MM-DD).")
    ap.add_argument("--rechtsgebied", action="append",
                    help="Rechtsgebied, bv. civiel, arbeidsrecht, strafrecht, bestuursrecht. Herhaal voor meerdere (OF).")
    ap.add_argument("--soort", choices=["uitspraak", "conclusie"], help="Alleen uitspraken of alleen conclusies.")
    ap.add_argument("--met-tekst", action="store_true", help="Alleen ECLI's waarvan de volledige tekst gepubliceerd is.")
    ap.add_argument("--gewijzigd-van", help="Gewijzigd vanaf (JJJJ-MM-DD of JJJJ-MM-DDTUU:MM:SS).")
    ap.add_argument("--gewijzigd-tot", help="Gewijzigd tot (JJJJ-MM-DD of JJJJ-MM-DDTUU:MM:SS).")
    ap.add_argument("--ljn", help="Zoek de ECLI bij een oud LJN-nummer, bv. AG4158.")
    ap.add_argument("--trefwoord", action="append",
                    help="Lokaal filter op titel + samenvatting (alle woorden moeten voorkomen). Geen full-text.")
    ap.add_argument("--max", type=int, default=20, help="Maximaal aantal getoonde resultaten (1-1000, standaard 20).")
    ap.add_argument("--scan-max", type=int, default=1000,
                    help="Bij --trefwoord: hoeveel items ophalen om lokaal te filteren (standaard 1000).")
    ap.add_argument("--offset", type=int, help="Paginering: begin bij resultaat n.")
    ap.add_argument("--sorteer", choices=["ASC", "DESC"],
                    help="Sortering van de server; sorteert op wijzigingsdatum, niet op uitspraakdatum.")
    ap.add_argument("--json", action="store_true", help="Uitvoer als JSON.")
    ap.add_argument("--toon-url", action="store_true", help="Toon alleen de API-URL en stop.")
    ap.add_argument("--lijst-instanties", action="store_true", help="Toon bekende instantiecodes en stop.")
    ap.add_argument("--lijst-rechtsgebieden", action="store_true", help="Toon bekende rechtsgebieden en stop.")
    args = ap.parse_args(argv)

    if args.lijst_instanties:
        for code, uri in rc.INSTANTIES.items():
            print(f"{code:6} {uri}")
        return 0
    if args.lijst_rechtsgebieden:
        for code, uri in rc.RECHTSGEBIEDEN.items():
            print(f"{code:30} {uri}")
        return 0

    filters = dict(instanties=args.instantie, datum_van=args.van, datum_tot=args.tot,
                   rechtsgebieden=args.rechtsgebied, soort=args.soort, alleen_met_tekst=args.met_tekst,
                   max_resultaten=args.max, offset=args.offset, sorteer=args.sorteer,
                   gewijzigd_van=args.gewijzigd_van, gewijzigd_tot=args.gewijzigd_tot, ljn=args.ljn)
    try:
        if args.toon_url:
            if args.trefwoord:
                filters["max_resultaten"] = args.scan_max
            print(rc.build_search_url(**filters))
            return 0
        if not any([args.instantie, args.van, args.tot, args.rechtsgebied, args.ljn, args.gewijzigd_van]):
            print("FOUT: geef minstens één filter (--instantie, --van/--tot, --rechtsgebied, --ljn of "
                  "--gewijzigd-van); zonder filter doorzoekt de API alle 3,7 miljoen ECLI's.", file=sys.stderr)
            return 1
        result = rc.zoek(trefwoorden=args.trefwoord, scan_max=args.scan_max, **filters)
    except rc.RechtspraakError as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        return 1
    except nl_http.FetchError as exc:
        print(f"NETWERKFOUT: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(rc.render_search(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
