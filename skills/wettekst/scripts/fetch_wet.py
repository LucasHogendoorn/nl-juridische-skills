#!/usr/bin/env python3
"""Haal de officiële tekst van een wetsartikel (per lid) op uit het Basiswettenbestand (BWB).

Bron: de officiële XML-repository achter wetten.overheid.nl
(repository.officiele-overheidspublicaties.nl). Met --datum krijg je de tekst
zoals die op die dag gold (beschikbaar vanaf ongeveer 2002).

Voorbeelden:
    python3 scripts/fetch_wet.py "6:162 BW"
    python3 scripts/fetch_wet.py "art. 7:673 lid 2 BW"
    python3 scripts/fetch_wet.py "art. 7:673 lid 2 BW" --datum 2016-01-01
    python3 scripts/fetch_wet.py "art. 8:1 Awb" "art. 350 Sr" "art. 3:40 BW"
    python3 scripts/fetch_wet.py --bwb BWBR0002448 --artikel 1      # Algemene termijnenwet (geen afkorting)
    python3 scripts/fetch_wet.py "art. 7:673 BW" --versies           # welke versies bestaan er

Exitcodes: 0 = gelukt, 1 = ongeldige invoer of niet gevonden, 2 = netwerk-/serverfout.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nl_http  # noqa: E402
import wet_client as wc  # noqa: E402


def one(cit, args) -> str:
    if args.versies:
        versies = wc.list_versies(cit.bwb_id)
        lines = [f"# Versies van {cit.wet} ({cit.bwb_id}) in de BWB-repository", "",
                 "| Geldig van | Geldig tot | Label |", "|---|---|---|"]
        for v in versies:
            tot = "heden" if v.geldig_tot.startswith("9999") else v.geldig_tot
            lines.append(f"| {v.geldig_van} | {tot} | {v.label} |")
        return "\n".join(lines) + "\n"
    result = wc.fetch_artikel(cit, datum=args.datum, lid=args.lid)
    if args.json:
        return json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    return wc.render_artikel(result)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Haal wetsartikelen op uit het officiële Basiswettenbestand.")
    ap.add_argument("citaat", nargs="*", help="Bijvoorbeeld '6:162 BW', 'art. 7:673 lid 2 BW', 'art. 8:1 Awb'.")
    ap.add_argument("--datum", help="Peildatum JJJJ-MM-DD: de tekst zoals die toen gold (standaard: vandaag).")
    ap.add_argument("--lid", help="Alleen dit lid (overschrijft 'lid' in het citaat).")
    ap.add_argument("--bwb", help="BWB-id voor een regeling zonder bekende afkorting, bv. BWBR0002448.")
    ap.add_argument("--artikel", help="Artikelnummer bij --bwb, bv. 7 of 1:1.")
    ap.add_argument("--versies", action="store_true", help="Toon alle beschikbare versies van de regeling.")
    ap.add_argument("--json", action="store_true", help="Uitvoer als JSON.")
    ap.add_argument("--uitvoer", help="Schrijf naar dit bestand.")
    args = ap.parse_args(argv)

    try:
        cits = [wc.parse_citation(c) for c in args.citaat]
        if args.bwb:
            if not args.artikel and not args.versies:
                raise wc.WetError("Geef bij --bwb ook --artikel op.")
            cits.append(wc.citation_from_bwb(args.bwb, args.artikel or "1"))
        if not cits:
            ap.print_usage(sys.stderr)
            print("FOUT: geef een citaat, bv. \"6:162 BW\", of --bwb met --artikel.", file=sys.stderr)
            return 1
    except wc.WetError as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        return 1

    out, status = [], 0
    for cit in cits:
        try:
            out.append(one(cit, args))
        except wc.WetError as exc:
            print(f"FOUT: {exc}", file=sys.stderr)
            status = max(status, 1)
        except nl_http.FetchError as exc:
            print(f"NETWERKFOUT: {exc}", file=sys.stderr)
            status = 2
    text = "\n---\n\n".join(out)
    if args.uitvoer and text:
        with open(args.uitvoer, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"geschreven: {args.uitvoer} ({len(text)} tekens)", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return status


if __name__ == "__main__":
    sys.exit(main())
