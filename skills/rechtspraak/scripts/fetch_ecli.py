#!/usr/bin/env python3
"""Haal een of meer uitspraken op via de open data van de Rechtspraak (ECLI:NL)
of via het Publicatiebureau van de EU (ECLI:EU), als markdown.

Voorbeelden:
    python3 scripts/fetch_ecli.py ECLI:NL:HR:2025:667
    python3 scripts/fetch_ecli.py ECLI:NL:HR:1981:AG4158 --alleen-meta
    python3 scripts/fetch_ecli.py ECLI:NL:HR:2025:667 ECLI:NL:PHR:2024:1131 --uitvoer-map bronnen/
    python3 scripts/fetch_ecli.py ECLI:EU:C:2014:317

Exitcodes: 0 = gelukt, 1 = ongeldige invoer of niet gevonden, 2 = netwerk-/serverfout.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import celex_client  # noqa: E402
import nl_http  # noqa: E402
import rechtspraak_client as rc  # noqa: E402


def fetch_one(ecli: str, meta_only: bool, as_json: bool, raw_xml: bool) -> str:
    if ecli.strip().upper().startswith("ECLI:EU:"):
        if as_json or raw_xml:
            raise rc.RechtspraakError("--json en --ruwe-xml werken alleen voor ECLI:NL.")
        return celex_client.fetch_markdown(ecli, meta_only=meta_only)
    if raw_xml:
        return rc.fetch_ecli_xml(ecli, meta_only=meta_only).decode("utf-8", "replace")
    parsed = rc.fetch_ecli(ecli, meta_only=meta_only)
    if as_json:
        return json.dumps(parsed, ensure_ascii=False, indent=2) + "\n"
    return rc.render_uitspraak(parsed, meta_only=meta_only)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Haal uitspraken op per ECLI (ECLI:NL via data.rechtspraak.nl, "
                                             "ECLI:EU via publications.europa.eu).")
    ap.add_argument("ecli", nargs="+", help="Een of meer ECLI's, bv. ECLI:NL:HR:2025:667")
    ap.add_argument("--alleen-meta", action="store_true", help="Alleen metadata en inhoudsindicatie, geen volledige tekst.")
    ap.add_argument("--json", action="store_true", help="Geef de geparste velden als JSON (alleen ECLI:NL).")
    ap.add_argument("--ruwe-xml", action="store_true", help="Geef de ruwe XML van de open-data-API (alleen ECLI:NL).")
    ap.add_argument("--uitvoer", help="Schrijf naar dit bestand (alleen bij één ECLI).")
    ap.add_argument("--uitvoer-map", help="Schrijf elke uitspraak naar <map>/<ECLI met _>.md.")
    args = ap.parse_intermixed_args(argv)

    if args.uitvoer and len(args.ecli) > 1:
        print("FOUT: --uitvoer kan maar met één ECLI; gebruik --uitvoer-map.", file=sys.stderr)
        return 1
    status = 0
    for i, ecli in enumerate(args.ecli):
        try:
            text = fetch_one(ecli, args.alleen_meta, args.json, args.ruwe_xml)
        except (rc.RechtspraakError, celex_client.CelexError) as exc:
            print(f"FOUT: {exc}", file=sys.stderr)
            status = max(status, 1)
            continue
        except nl_http.FetchError as exc:
            print(f"NETWERKFOUT: {exc}", file=sys.stderr)
            status = 2
            continue
        if args.uitvoer_map:
            os.makedirs(args.uitvoer_map, exist_ok=True)
            ext = ".json" if args.json else ".xml" if args.ruwe_xml else ".md"
            path = os.path.join(args.uitvoer_map, ecli.strip().upper().replace(":", "_") + ext)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"geschreven: {path} ({len(text)} tekens)", file=sys.stderr)
        elif args.uitvoer:
            with open(args.uitvoer, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"geschreven: {args.uitvoer} ({len(text)} tekens)", file=sys.stderr)
        else:
            if i:
                sys.stdout.write("\n---\n\n")
            sys.stdout.write(text)
    return status


if __name__ == "__main__":
    sys.exit(main())
