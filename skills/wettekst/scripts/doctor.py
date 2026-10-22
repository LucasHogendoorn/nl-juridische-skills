#!/usr/bin/env python3
"""Controleer of de officiële BWB-repository bereikbaar is en waar de cache staat.

Gebruik: python3 scripts/doctor.py
Exitcode 0 = bereikbaar, 3 = onbereikbaar.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nl_http  # noqa: E402
import wet_client as wc  # noqa: E402


def main() -> int:
    print(f"Python {sys.version.split()[0]}, User-Agent: {nl_http.USER_AGENT}")
    ok, msg = nl_http.check_host(f"{wc.REPO}/BWBR0005289/manifest.xml", accept="application/xml")
    print(f"[{'OK' if ok else 'FOUT'}] BWB-repository (manifest BW Boek 6): {msg}")
    print(f"Cachemap: {wc._cache_dir()} (instelbaar met NLJS_CACHE_DIR)")
    if ok:
        return 0
    print("\nDe repository is niet bereikbaar. Controleer de internetverbinding en of "
          "repository.officiele-overheidspublicaties.nl is toegestaan in je omgeving.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
