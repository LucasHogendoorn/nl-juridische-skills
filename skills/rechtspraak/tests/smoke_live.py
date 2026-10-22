#!/usr/bin/env python3
"""Live rooktest: realistische dagelijkse verzoeken tegen de echte bronnen.

Gebruik (vanuit de skill-map):  python3 tests/smoke_live.py
Maakt netwerkverbindingen met data.rechtspraak.nl en publications.europa.eu.
Exitcode 0 = alle controles geslaagd, 1 = een of meer mislukt.
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "scripts")

today = dt.date.today()
month_ago = (today - dt.timedelta(days=30)).isoformat()
year_start = f"{today.year}-01-01"

# (omschrijving, script, argumenten, verwachte exitcode, tekstfragmenten die in stdout+stderr moeten staan)
CASES = [
    ("Haviltex (HR 1981) volledig", "fetch_ecli.py", ["ECLI:NL:HR:1981:AG4158"], 0,
     ["Haviltex", "maatschappelijke kringen", "## Uitspraak", "NJ 1981/635"]),
    ("Recent HR-arrest met r.o.-nummers", "fetch_ecli.py", ["ECLI:NL:HR:2025:667"], 0,
     ["**2.1**", "**3.4**", "Art. 236 Rv", "[^1]:"]),
    ("Kelderluik alleen metadata", "fetch_ecli.py", ["ECLI:NL:HR:1965:AB7079", "--alleen-meta"], 0,
     ["1965-11-05", "Kelderluik-arrest", "NJ 1966, 136"]),
    ("HR-uitspraken laatste 30 dagen", "zoek_uitspraken.py",
     ["--instantie", "HR", "--soort", "uitspraak", "--van", month_ago, "--tot", today.isoformat(), "--max", "5"], 0,
     ["| ECLI:NL:HR:", "Aantal ECLI's"]),
    ("Rechtbank Amsterdam arbeidsrecht, met tekst", "zoek_uitspraken.py",
     ["--instantie", "RBAMS", "--rechtsgebied", "arbeidsrecht", "--van", month_ago, "--tot", today.isoformat(),
      "--met-tekst", "--max", "5"], 0, ["| ECLI:NL:RBAMS:"]),
    ("Lokaal trefwoordfilter (geen full-text)", "zoek_uitspraken.py",
     ["--instantie", "GHARL", "--rechtsgebied", "arbeidsrecht", "--van", year_start, "--tot", today.isoformat(),
      "--trefwoord", "ontslag", "--max", "5"], 0, ["Lokaal gefilterd", "geen full-text"]),
    ("LJN AG4158 naar ECLI", "zoek_uitspraken.py", ["--ljn", "AG4158"], 0, ["ECLI:NL:HR:1981:AG4158"]),
    ("HvJ Google Spain via zaaknummer", "fetch_celex.py", ["C-131/12"], 0,
     ["62012CJ0131", "Google Spain", "**80**"]),
    ("HvJ via ECLI:EU in fetch_ecli", "fetch_ecli.py", ["ECLI:EU:C:2014:317", "--alleen-meta"], 0,
     ["ECLI:EU:C:2014:317", "publications.europa.eu"]),
    ("AVG (verordening) volledige tekst", "fetch_celex.py", ["32016R0679"], 0,
     ["Artikel 17", "gegevenswissing"]),
    ("Niet-bestaande ECLI geeft nette fout", "fetch_ecli.py", ["ECLI:NL:HR:2005:AU6093"], 1, ["niet gevonden"]),
    ("Connectiviteitscheck", "doctor.py", [], 0, ["Alle bronnen zijn bereikbaar"]),
]


def main() -> int:
    failures = 0
    print(f"Live rooktest rechtspraak — {dt.datetime.now().isoformat(timespec='seconds')}\n")
    for label, script, args, want_code, fragments in CASES:
        start = time.monotonic()
        proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args],
                              capture_output=True, text=True, timeout=300)
        secs = time.monotonic() - start
        text = proc.stdout + proc.stderr
        missing = [f for f in fragments if f not in text]
        ok = proc.returncode == want_code and not missing
        failures += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label} ({secs:.1f}s)")
        print(f"       python3 scripts/{script} {' '.join(repr(a) if ' ' in a else a for a in args)}")
        if not ok:
            print(f"       exitcode {proc.returncode} (verwacht {want_code}); ontbrekend: {missing}")
            print("       " + text[:600].replace("\n", "\n       "))
    print(f"\n{len(CASES) - failures}/{len(CASES)} geslaagd.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
