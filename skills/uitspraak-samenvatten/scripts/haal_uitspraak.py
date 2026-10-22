#!/usr/bin/env python3
"""Haal een Nederlandse uitspraak op via de open data van de Rechtspraak en toon hem als markdown.

Gebruik (vanuit de skillmap):
    python3 scripts/haal_uitspraak.py ECLI:NL:HR:1981:AG4158
    python3 scripts/haal_uitspraak.py ECLI:NL:HR:1981:AG4158 --meta      # alleen metadata (zonder inhoudsindicatie)
    python3 scripts/haal_uitspraak.py ECLI:NL:HR:1981:AG4158 -o uitspraak.md

Bron: https://data.rechtspraak.nl/uitspraken/content?id=<ECLI> (officiële open data).
Rechtsoverwegingen staan in de uitvoer als **<nr>** aan het begin van de alinea.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nl_http  # noqa: E402
import rechtspraak_client as rc  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Haal een uitspraak op via data.rechtspraak.nl.")
    ap.add_argument("ecli", help="bijv. ECLI:NL:HR:1981:AG4158")
    ap.add_argument("--meta", action="store_true", help="alleen metadata (de open data geven dan geen inhoudsindicatie)")
    ap.add_argument("-o", "--uitvoer", help="schrijf markdown naar dit bestand")
    args = ap.parse_args(argv)
    try:
        md = rc.fetch_ecli_markdown(args.ecli, meta_only=args.meta)
    except rc.RechtspraakError as exc:
        print("Fout: %s" % exc, file=sys.stderr)
        return 1
    except nl_http.FetchError as exc:
        print("Netwerkfout: %s" % exc, file=sys.stderr)
        return 3
    if args.uitvoer:
        with open(args.uitvoer, "w", encoding="utf-8") as fh:
            fh.write(md)
        print("Geschreven: %s (%d tekens)" % (args.uitvoer, len(md)))
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
