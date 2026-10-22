#!/usr/bin/env python3
"""Live smoke test: realistic daily questions against the KOOP SRU service (needs network).

Run from the skill folder:  python3 tests/smoke_live.py
Each case runs the CLI exactly as a user/agent would and checks that the answer contains
the document or passage a lawyer would expect (not just that it is non-empty).
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "parlgesch.py")

CASES = [
    ("Welk dossier is de Wet werk en zekerheid?",
     ["wet", "Wet werk en zekerheid"], ["**33818**"]),
    ("MvT bij de transitievergoeding (WWZ)",
     ["zoek", "transitievergoeding", "--soort", "mvt", "--dossier", "33818"],
     ["Kamerstukken II 2013/14, 33818, nr. 3"]),
    ("Alle stukken dossier 33818",
     ["dossier", "33818"],
     ["33818, nr. 3", "33818, nr. 7", "Nota naar aanleiding van het verslag", "33818, nr. C",
      "## Handelingen", "Handelingen II 2013/14, nr. 54, item 9", "Stb. 2014, 216"]),
    ("Wat zei de wetgever over art. 7:673 lid 7 BW (WWZ-MvT)",
     ["haal", "kst-33818-3", "--artikel", "7:673 lid 7", "--trefwoord", "transitievergoeding",
      "--max-passages", "3"],
     ["Onderdeel V (artikel 7:673 BW)", "Het zevende lid voorziet", "33818, nr. 3, p. 112"]),
    ("Nota n.a.v. verslag Wet arbeidsmarkt in balans",
     ["zoek", "--wet", "Wet arbeidsmarkt in balans", "--soort", "nnavv"],
     ["Kamerstukken II 2018/19, 35074, nr. 9"]),
    ("Transitievergoeding in de NnavV WAB, met pagina",
     ["haal", "kst-35074-9", "--trefwoord", "transitievergoeding", "--trefwoord", "eerste dag",
      "--max-passages", "3"],
     ["Kamerstukken II 2018/19, 35074, nr. 9, p. "]),
    ("Amendementen over de transitievergoeding (WWZ)",
     ["zoek", "transitievergoeding", "--soort", "amendement", "--dossier", "33818", "-n", "30"],
     ["33818, nr. 13", "33818, nr. 27"]),
    ("Memorie van antwoord Eerste Kamer WWZ",
     ["zoek", "--dossier", "33818", "--soort", "mva", "--kamer", "ek"],
     ["Kamerstukken I 2013/14, 33818, nr. C"]),
    ("Parlementaire geschiedenis art. 6:162 BW (NBW, vóór 1995) — vinden",
     ["zoek", "onrechtmatige daad", "--voor-1995", "--dossier", "7729"],
     ["Kamerstukken II 1975/76, 7729, nr. 6", "MEMORIE VAN ANTWOORD"]),
    ("Parlementaire geschiedenis art. 6:162 BW (NBW) — passage in MvA (OCR, pagina 150-160)",
     ["haal", "0000194825", "--artikel", "6.3.1.1", "--trefwoord", "onrechtmatige daad",
      "--paginas", "150-160", "--max-passages", "3"],
     ["Artikel 6.3.1.1", "Kamerstukken II 1975/76, 7729, nr. 6, p. 157", "OCR-tekst"]),
]


def main():
    failures = 0
    for titel, args, verwacht in CASES:
        t0 = time.time()
        proc = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True, timeout=600)
        out = proc.stdout + proc.stderr
        missing = [v for v in verwacht if v not in out]
        ok = proc.returncode == 0 and not missing
        failures += 0 if ok else 1
        print(f"[{'OK ' if ok else 'FAIL'}] {titel} ({time.time() - t0:.0f}s)")
        print("      $ python3 scripts/parlgesch.py " + " ".join(f'"{a}"' if " " in a else a for a in args))
        if not ok:
            print(f"      exit {proc.returncode}; ontbreekt: {missing}")
            print("      " + out[:800].replace("\n", "\n      "))
    print(f"\n{len(CASES) - failures}/{len(CASES)} geslaagd")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
