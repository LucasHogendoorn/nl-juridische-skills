#!/usr/bin/env python3
"""Live smoke test: realistic daily tuchtrecht questions against the KOOP SRU service (needs network).

Run from the skill folder:  python3 tests/smoke_live.py
Each case runs the CLI with --json and checks the records themselves (domain, dates, and
whether the inhoudsindicatie is about the topic), not only that something came back.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "scripts", "tuchtrecht.py")


def run(args):
    proc = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True, timeout=300)
    return proc.returncode, proc.stdout, proc.stderr


def zoek(args):
    rc, out, err = run(["zoek"] + args + ["--json"])
    if rc != 0:
        raise AssertionError(f"exit {rc}: {err[:400]}")
    return json.loads(out)


def summary(rec):
    return " ".join(rec["descriptions"]).lower()


def topical_share(records, words):
    hits = sum(1 for r in records if any(w in summary(r) for w in words))
    return hits, len(records)


CASES = []


def case(titel, cmd):
    def deco(fn):
        CASES.append((titel, cmd, fn))
        return fn
    return deco


@case("Advocaat belangenverstrengeling 2024 (strikt)",
      ["belangenverstrengeling", "--domein", "advocaten", "--van", "2024-01-01", "--tot", "2024-12-31",
       "--strikt", "-n", "25"])
def _(d):
    recs = d["records"]
    assert d["total"] >= 10, d["total"]
    assert all(r["meta"]["instantieDomein"] == ["Advocaten"] for r in recs)
    assert all("2024-01-01" <= r["date"] <= "2024-12-31" for r in recs), [r["date"] for r in recs]
    hits, n = topical_share(recs, ["belangenverstrengeling"])
    assert hits == n, f"{hits}/{n}"
    return f"{d['total']} treffers; {hits}/{n} inhoudsindicaties noemen belangenverstrengeling"


@case("Advocaat belangenverstrengeling 2024 (volledige tekst, zonder --strikt)",
      ["belangenverstrengeling", "--domein", "advocaten", "--van", "2024-01-01", "--tot", "2024-12-31",
       "-n", "25"])
def _(d):
    hits, n = topical_share(d["records"], ["belangenverstrengeling", "belangenconflict", "tegenstrijdig belang"])
    return f"{d['total']} treffers; {hits}/{n} inhoudsindicaties gaan (ook) over belangenverstrengeling"


@case("Huisarts dossiervoering tuchtcollege (strikt)",
      ["dossiervoering", "--beroep", "huisarts", "--strikt", "-n", "20"])
def _(d):
    recs = d["records"]
    assert d["total"] >= 10, d["total"]
    assert recs[0]["date"] >= "2025-01-01", recs[0]["date"]  # recent decisions must be found too
    hits, n = topical_share(recs, ["huisarts"])
    dos, _ = topical_share(recs, ["dossier"])
    assert hits == n and dos == n, (hits, dos, n)
    return (f"{d['total']} treffers; {hits}/{n} over een huisarts, {dos}/{n} noemen dossiervoering; "
            f"nieuwste {recs[0]['identifier']} ({recs[0]['date']})")


@case("Notaris zorgplicht (strikt)", ["zorgplicht", "--domein", "notarissen", "--strikt", "-n", "20"])
def _(d):
    recs = d["records"]
    assert d["total"] >= 10, d["total"]
    assert all(r["meta"]["instantieDomein"] == ["Notarissen"] for r in recs)
    hits, n = topical_share(recs, ["zorgplicht"])
    assert hits == n
    return f"{d['total']} treffers; nieuwste {recs[0]['identifier']} ({recs[0]['date']})"


@case("Accountants, eerste helft 2025 (datumgrens)",
      ["--domein", "accountants", "--van", "2025-01-01", "--tot", "2025-06-30", "-n", "50"])
def _(d):
    recs = d["records"]
    assert d["total"] >= 10, d["total"]
    assert all("2025-01-01" <= r["date"] <= "2025-06-30" for r in recs), [r["date"] for r in recs]
    assert all(r["meta"]["instantieDomein"] == ["Accountants"] for r in recs)
    return f"{d['total']} uitspraken; data {recs[-1]['date']} … {recs[0]['date']}"


@case("Tandarts implantaat", ["implantaat", "--beroep", "tandarts", "--strikt", "-n", "15"])
def _(d):
    recs = d["records"]
    assert d["total"] >= 5
    assert recs[0]["date"] >= "2025-01-01", recs[0]["date"]
    hits, n = topical_share(recs, ["implanta"])
    assert hits == n
    return f"{d['total']} treffers; {hits}/{n} over implantaten; nieuwste {recs[0]['date']}"


@case("Gerechtsdeurwaarder beslag 2023-2025",
      ["beslag", "--domein", "deurwaarder", "--van", "2023-01-01", "--tot", "2025-12-31", "--strikt", "-n", "15"])
def _(d):
    recs = d["records"]
    assert d["total"] >= 5
    assert all(r["meta"]["instantieDomein"] == ["Gerechtsdeurwaarders"] for r in recs)
    hits, n = topical_share(recs, ["beslag"])
    assert hits == n
    return f"{d['total']} treffers"


@case("Advocaat berisping 2025 (uitkomst)",
      ["--domein", "advocaten", "--uitkomst", "berisping", "--van", "2025-01-01", "--tot", "2025-12-31", "-n", "20"])
def _(d):
    recs = d["records"]
    hits, n = topical_share(recs, ["berisping"])
    assert d["total"] >= 10 and hits >= n * 0.8, (d["total"], hits, n)
    return f"{d['total']} treffers; {hits}/{n} noemen berisping in de inhoudsindicatie"


def main():
    failures = 0
    eerste_ecli = None
    for titel, cmd, check in CASES:
        shown = "python3 scripts/tuchtrecht.py zoek " + " ".join(f'"{a}"' if " " in a else a for a in cmd)
        try:
            data = zoek(cmd)
            info = check(data)
            eerste_ecli = eerste_ecli or (data["records"][0]["identifier"] if data["records"] else None)
            print(f"[OK ] {titel}: {info}\n      $ {shown}")
        except (AssertionError, ValueError, KeyError) as exc:
            failures += 1
            print(f"[FAIL] {titel}: {exc!r}\n      $ {shown}")
    # Full text of the first hit
    total = len(CASES) + 1
    rc, out, err = run(["haal", eerste_ecli or "ECLI:NL:TADRSHE:2011:YA2031"])
    ok = rc == 0 and "## Inhoudsindicatie" in out and "## Uitspraak" in out and len(out) > 3000
    failures += 0 if ok else 1
    print(f"[{'OK ' if ok else 'FAIL'}] Volledige tekst {eerste_ecli}: {len(out)} tekens"
          f"\n      $ python3 scripts/tuchtrecht.py haal {eerste_ecli}")
    if not ok:
        print("      " + (out + err)[:600])
    print(f"\n{total - failures}/{total} geslaagd")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
