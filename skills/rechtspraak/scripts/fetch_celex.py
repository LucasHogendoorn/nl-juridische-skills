#!/usr/bin/env python3
"""Haal een EU-document op (HvJ/Gerecht-uitspraak, verordening, richtlijn, verdrag)
via het Publicatiebureau van de EU (publications.europa.eu), als markdown.

Invoer: een CELEX-nummer (32016R0679), een Europese ECLI (ECLI:EU:C:2014:317)
of een zaaknummer (C-131/12; wordt omgezet naar het CELEX-nummer van het arrest,
of met --soort naar de conclusie/beschikking).

Voorbeelden:
    python3 scripts/fetch_celex.py 62012CJ0131
    python3 scripts/fetch_celex.py C-131/12
    python3 scripts/fetch_celex.py C-131/12 --soort conclusie
    python3 scripts/fetch_celex.py ECLI:EU:C:2014:317 --uitvoer google-spain.md
    python3 scripts/fetch_celex.py 32016R0679 --alleen-meta

Exitcodes: 0 = gelukt, 1 = ongeldige invoer of niet gevonden, 2 = netwerk-/serverfout.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import celex_client as cc  # noqa: E402
import nl_http  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Haal een EU-document op via CELEX, ECLI:EU of zaaknummer.")
    ap.add_argument("id", help="CELEX-nummer, ECLI:EU of zaaknummer (C-131/12).")
    ap.add_argument("--taal", default="nld", choices=cc.TALEN, help="Voorkeurstaal (standaard nld).")
    ap.add_argument("--soort", default="arrest", choices=["arrest", "conclusie", "beschikking"],
                    help="Alleen bij een zaaknummer: welk document (standaard arrest).")
    ap.add_argument("--alleen-meta", action="store_true", help="Alleen kop en bron, geen tekst.")
    ap.add_argument("--ruwe-html", action="store_true", help="Geef de ruwe XHTML (debuggen).")
    ap.add_argument("--uitvoer", help="Schrijf naar dit bestand.")
    args = ap.parse_args(argv)

    ident = args.id
    try:
        if cc.ZAAK_RE.match(ident.strip()):
            ident = cc.zaak_naar_celex(ident, args.soort)
            print(f"zaaknummer {args.id} -> CELEX {ident} ({args.soort})", file=sys.stderr)
        if args.ruwe_html:
            text = cc.fetch_html(ident, args.taal)["html"]
        else:
            text = cc.fetch_markdown(ident, taal=args.taal, meta_only=args.alleen_meta)
    except cc.CelexError as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        return 1
    except nl_http.FetchError as exc:
        print(f"NETWERKFOUT: {exc}", file=sys.stderr)
        return 2
    if args.uitvoer:
        with open(args.uitvoer, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"geschreven: {args.uitvoer} ({len(text)} tekens)", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
