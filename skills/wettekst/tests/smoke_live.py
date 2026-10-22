#!/usr/bin/env python3
"""Live rooktest: realistische dagelijkse verzoeken tegen de officiële BWB-repository.

Gebruik (vanuit de skill-map):  python3 tests/smoke_live.py
Gebruikt een tijdelijke, lege cachemap (tenzij NLJS_CACHE_DIR al is gezet), zodat
elke regeling echt wordt gedownload. Exitcode 0 = alles geslaagd, 1 = iets mislukt.
"""
from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "fetch_wet.py")
DOCTOR = os.path.join(HERE, "..", "scripts", "doctor.py")

# (omschrijving, argumenten, verwachte exitcode, fragmenten die in de uitvoer moeten staan)
CASES = [
    ("Onrechtmatige daad", ["6:162 BW"], 0,
     ["Hij die jegens een ander een onrechtmatige daad pleegt", "**3.**"]),
    ("Nietigheid rechtshandeling", ["art. 3:40 BW"], 0, ["goede zeden of de openbare orde, is nietig"]),
    ("Taak bestuurder, één lid", ["art. 2:9 lid 1 BW"], 0, ["behoorlijke vervulling van zijn taak"]),
    ("Transitievergoeding lid 2, vandaag", ["art. 7:673 lid 2 BW"], 0, ["een derde van het loon per maand"]),
    ("Transitievergoeding lid 2 op 1-1-2016", ["art. 7:673 lid 2 BW", "--datum", "2016-01-01"], 0,
     ["eerste 120 maanden", "geldig van 2016-01-01"]),
    ("Redelijke grond ontslag (lijst a-...)", ["art. 7:669 lid 3 BW"], 0, ["\na. het vervallen van arbeidsplaatsen"]),
    ("Beroep bestuursrechter", ["art. 8:1 Awb"], 0, ["beroep instellen bij de bestuursrechter"]),
    ("Vernieling", ["art. 350 Sr"], 0, ["vernielt, beschadigt, onbruikbaar maakt of wegmaakt"]),
    ("Verdachte", ["art. 27 lid 1 Sv"], 0, ["redelijk vermoeden van schuld"]),
    ("Exhibitieplicht oud (2024)", ["art. 843a lid 1 Rv", "--datum", "2024-06-01"], 0,
     ["inzage, afschrift of uittreksel"]),
    ("Exhibitieplicht vandaag vervallen", ["art. 843a Rv"], 0, ["vervallen"]),
    ("Gelijke behandeling", ["art. 1 Grondwet"], 0, ["in gelijke gevallen gelijk behandeld"]),
    ("Actio pauliana", ["art. 42 lid 1 Fw"], 0, ["benadeling van de schuldeisers"]),
    ("Bijzondere persoonsgegevens", ["art. 22 UAVG"], 0, ["Verwerkingsverbod bijzondere categorieën"]),
    ("Regeling zonder afkorting via BWB-id", ["--bwb", "BWBR0002448", "--artikel", "1"], 0,
     ["zaterdag, zondag of algemeen erkende feestdag"]),
    ("Niet-bestaand artikel", ["art. 6:9999 BW"], 1, ["niet gevonden"]),
    ("AVG wordt doorverwezen", ["art. 6 AVG"], 1, ["EU-verordening"]),
]


def run(args, env):
    start = time.monotonic()
    proc = subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=300, env=env)
    return proc, time.monotonic() - start


def main() -> int:
    env = dict(os.environ)
    tmp = None
    if not env.get("NLJS_CACHE_DIR"):
        tmp = tempfile.mkdtemp(prefix="nljs-smoke-")
        env["NLJS_CACHE_DIR"] = tmp
    failures = 0
    print(f"Live rooktest wettekst — {dt.datetime.now().isoformat(timespec='seconds')} "
          f"(cache: {env['NLJS_CACHE_DIR']})\n")
    try:
        for label, args, want, fragments in CASES:
            proc, secs = run([SCRIPT, *args], env)
            text = proc.stdout + proc.stderr
            missing = [f for f in fragments if f not in text]
            ok = proc.returncode == want and not missing
            failures += not ok
            shown = " ".join(f'"{a}"' if " " in a else a for a in args)
            print(f"[{'PASS' if ok else 'FAIL'}] {label} ({secs:.1f}s)\n       python3 scripts/fetch_wet.py {shown}")
            if not ok:
                print(f"       exitcode {proc.returncode} (verwacht {want}); ontbrekend: {missing!r}")
                print("       " + text[:600].replace("\n", "\n       "))
        proc, secs = run([DOCTOR], env)
        ok = proc.returncode == 0
        failures += not ok
        print(f"[{'PASS' if ok else 'FAIL'}] Connectiviteitscheck ({secs:.1f}s)\n       python3 scripts/doctor.py")
        total = len(CASES) + 1
        print(f"\n{total - failures}/{total} geslaagd.")
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
