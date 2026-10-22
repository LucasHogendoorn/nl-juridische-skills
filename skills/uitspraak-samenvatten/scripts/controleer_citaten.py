#!/usr/bin/env python3
"""Controleer of elk citaat in een samenvatting letterlijk in de uitspraaktekst staat.

Gebruik (vanuit de skillmap):
    python3 scripts/controleer_citaten.py samenvatting.md uitspraak.md

Een citaat is tekst tussen "...", “...” of „...” van minstens vier woorden. Witruimte,
markdown-vet (**) en voetnootmarkeringen ([^2]) worden genormaliseerd; verder moet het
citaat exact overeenkomen.
Exitcode 0 = alle citaten gevonden, 1 = een of meer niet gevonden.
"""
import re
import sys

# "...", “...” and the Dutch „...” (closed by ” or “ or ").
QUOTE_RE = re.compile(r'"([^"\n]+)"|“([^”\n]+)”|„([^”“"\n]+)[”“"]')
FOOTNOTE_RE = re.compile(r"\[\^\d+\]")


def normalize(text):
    text = text.replace("**", "")
    text = FOOTNOTE_RE.sub("", text)
    text = text.replace("’", "'").replace("‘", "'")
    return " ".join(text.split())


def extract_quotes(summary, min_words=4):
    quotes = []
    for m in QUOTE_RE.finditer(summary):
        q = next(g for g in m.groups() if g is not None).strip()
        if len(q.split()) >= min_words:
            quotes.append(q)
    return quotes


def check(summary, source):
    src = normalize(source)
    results = []
    for q in extract_quotes(summary):
        nq = normalize(q).rstrip(".,;:")
        results.append((q, nq in src))
    return results


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print(__doc__.strip())
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        summary = fh.read()
    with open(argv[1], encoding="utf-8") as fh:
        source = fh.read()
    results = check(summary, source)
    missing = [q for q, ok in results if not ok]
    for q, ok in results:
        print("%s  %s" % ("OK       " if ok else "NIET GEVONDEN", q[:100]))
    print("%d citaten, %d niet gevonden." % (len(results), len(missing)))
    if not results:
        print("Let op: geen citaten van vier woorden of meer gevonden. Staan de citaten tussen "
              "dubbele aanhalingstekens (\"...\", “...” of „...”)?")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
