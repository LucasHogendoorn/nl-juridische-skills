"""Live smoke test (dagelijks gebruik): haal twee bekende uitspraken op en controleer het voorbeeld.

Draai vanuit de skillmap: python3 tests/smoke_live.py
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)


def run(args):
    return subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=SKILL)


def main():
    ok = 0
    total = 0
    with tempfile.TemporaryDirectory() as d:
        hav = os.path.join(d, "haviltex.md")
        cases = [
            (["scripts/haal_uitspraak.py", "ECLI:NL:HR:1981:AG4158", "-o", hav], None),
            (["scripts/haal_uitspraak.py", "ECLI:NL:HR:2025:167"], "**3.1.3**"),
            (["scripts/haal_uitspraak.py", "ECLI:NL:HR:2025:727", "--meta"], "Formele relaties"),
            (["scripts/controleer_citaten.py", "examples/haviltex-HR-1981.md", hav], "0 niet gevonden"),
        ]
        for args, needle in cases:
            total += 1
            r = run(args)
            good = r.returncode == 0 and (needle is None or needle in r.stdout)
            ok += good
            print("%s  %s" % ("OK  " if good else "FAIL", " ".join(args[:2])))
            if not good:
                print(r.stdout[-500:], r.stderr[-500:])
    print("%d/%d geslaagd" % (ok, total))
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
