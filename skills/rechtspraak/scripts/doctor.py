#!/usr/bin/env python3
"""Controleer of de bronnen van deze skill bereikbaar zijn.

Gebruik: python3 scripts/doctor.py
Exitcode 0 = alles bereikbaar, 3 = een of meer bronnen onbereikbaar.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nl_http  # noqa: E402

CHECKS = [
    ("Rechtspraak open data (zoeken)", "https://data.rechtspraak.nl/uitspraken/zoeken?max=1",
     "application/atom+xml", None),
    ("Rechtspraak open data (uitspraak)",
     "https://data.rechtspraak.nl/uitspraken/content?id=ECLI:NL:HR:1981:AG4158&return=META", "application/xml", None),
    ("EU Publicatiebureau (ECLI:EU)", "https://publications.europa.eu/resource/ecli/ECLI%3AEU%3AC%3A2014%3A317",
     "text/html, application/xhtml+xml;q=0.9", {"Accept-Language": "nld"}),
]


def main() -> int:
    print(f"Python {sys.version.split()[0]}, User-Agent: {nl_http.USER_AGENT}")
    ok_all = True
    for label, url, accept, headers in CHECKS:
        ok, msg = nl_http.check_host(url, accept=accept, headers=headers)
        ok_all &= ok
        print(f"[{'OK' if ok else 'FOUT'}] {label}: {msg}")
    if ok_all:
        print("\nAlle bronnen zijn bereikbaar.")
        return 0
    print("\nNiet alles is bereikbaar. Controleer de internetverbinding en of deze domeinen zijn toegestaan:\n"
          "  data.rechtspraak.nl, publications.europa.eu\n"
          "Bij HTTP 503: de server is tijdelijk overbelast; probeer het over enkele minuten opnieuw.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
