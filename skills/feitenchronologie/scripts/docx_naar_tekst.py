#!/usr/bin/env python3
"""Haal platte tekst uit een .docx (alleen standaardbibliotheek) met genummerde alinea's.

Gebruik (vanuit de skillmap):
    python3 scripts/docx_naar_tekst.py stuk.docx            # naar scherm
    python3 scripts/docx_naar_tekst.py stuk.docx -o stuk.txt

Elke niet-lege alinea krijgt een nummer [1], [2], ... zodat je in de chronologie naar
"D3, alinea 12" kunt verwijzen. Tabellen worden per rij weergegeven (cellen gescheiden door ' | ').
Voetnoten, opmerkingen en bijgehouden wijzigingen worden niet meegenomen (verwijderde tekst niet,
ingevoegde tekst wel).
"""
import argparse
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _para_text(p):
    parts = []
    for el in p.iter():
        if el.tag == W + "t":
            parts.append(el.text or "")
        elif el.tag == W + "tab":
            parts.append("\t")
        elif el.tag in (W + "br", W + "cr"):
            parts.append("\n")
        elif el.tag == W + "delText":
            continue
    return "".join(parts).strip()


def docx_paragraphs(path):
    """Return a list of paragraph strings (tables flattened per row)."""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError, OSError) as exc:
        raise ValueError("Geen leesbaar .docx-bestand: %s (%s)" % (path, exc))
    root = ET.fromstring(xml)
    body = root.find(W + "body")
    out = []
    for child in list(body) if body is not None else []:
        if child.tag == W + "p":
            t = _para_text(child)
            if t:
                out.append(t)
        elif child.tag == W + "tbl":
            for tr in child.iter(W + "tr"):
                cells = [" ".join(_para_text(p) for p in tc.iter(W + "p")).strip() for tc in tr.iter(W + "tc")]
                if any(cells):
                    out.append(" | ".join(cells))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Platte tekst uit .docx met genummerde alinea's.")
    ap.add_argument("bestand")
    ap.add_argument("-o", "--uitvoer")
    args = ap.parse_args(argv)
    try:
        paras = docx_paragraphs(args.bestand)
    except ValueError as exc:
        print("Fout: %s" % exc, file=sys.stderr)
        return 1
    text = "\n".join("[%d] %s" % (i, p) for i, p in enumerate(paras, 1)) + "\n"
    if args.uitvoer:
        with open(args.uitvoer, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("Geschreven: %s (%d alinea's)" % (args.uitvoer, len(paras)))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
