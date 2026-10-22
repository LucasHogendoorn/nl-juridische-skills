#!/usr/bin/env python3
"""Zet de chronologietabel uit een markdownbestand om naar CSV en/of controleer de regels.

Gebruik (vanuit de skillmap):
    python3 scripts/naar_csv.py chronologie.md --controleer
    python3 scripts/naar_csv.py chronologie.md -o chronologie.csv
    python3 scripts/naar_csv.py chronologie.md -o chronologie.csv --scheidingsteken ,

De tabel is de eerste markdowntabel met de kolommen Datum, Gebeurtenis en Bron
(normaal onder "## Chronologie"). CSV wordt geschreven als UTF-8 met BOM en standaard
met puntkomma als scheidingsteken, zodat Nederlandse Excel het direct opent.
Exitcode bij --controleer: 0 = geen fouten, 1 = fouten gevonden (waarschuwingen tellen niet).
"""
import argparse
import csv
import re
import sys

REQUIRED = ("datum", "gebeurtenis", "bron")

_ISO = r"\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?"
DATE_PATTERNS = [
    re.compile(r"^%s$" % _ISO),
    re.compile(r"^\d{4}-\d{2}$"),
    re.compile(r"^\d{4}$"),
    re.compile(r"^%s\s*[–-]\s*%s$" % (_ISO, _ISO)),
    re.compile(r"^onbekend$", re.I),
]
FIRST_DATE = re.compile(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?")


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    return [c.strip().replace("\\|", "|") for c in cells]


def _is_separator(cells):
    return all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c) and any(cells)


def find_table(text):
    """Return (header, rows) of the first table with Datum/Gebeurtenis/Bron columns, else (None, [])."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and lines[i + 1].lstrip().startswith("|"):
            header = _split_row(lines[i])
            if _is_separator(_split_row(lines[i + 1])):
                norm = [h.lower().strip("* ") for h in header]
                if all(any(r == n or n.startswith(r) for n in norm) for r in REQUIRED):
                    rows = []
                    j = i + 2
                    while j < len(lines) and lines[j].lstrip().startswith("|"):
                        cells = _split_row(lines[j])
                        cells += [""] * (len(header) - len(cells))
                        rows.append(cells[:len(header)])
                        j += 1
                    return header, rows
        i += 1
    return None, []


def _col(header, name):
    norm = [h.lower().strip("* ") for h in header]
    for idx, n in enumerate(norm):
        if n == name or n.startswith(name):
            return idx
    return None


def _clean(cell):
    return cell.replace("**", "").strip()


def date_ok(value):
    v = _clean(value)
    if v.startswith("±") or v.startswith("+-") or v.startswith("ca."):
        return "afgeleid" in v.lower()
    return any(p.match(v) for p in DATE_PATTERNS)


def sort_key(value):
    m = FIRST_DATE.search(_clean(value))
    if not m or _clean(value).lower() == "onbekend":
        return None
    return (int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0))


def check(header, rows):
    """Return (errors, warnings): lists of Dutch messages."""
    errors, warnings = [], []
    if header is None:
        return ["Geen chronologietabel gevonden (kolommen Datum, Gebeurtenis, Bron)."], []
    c_datum, c_geb, c_bron = (_col(header, n) for n in REQUIRED)
    c_status = _col(header, "status")
    if c_status is None:
        warnings.append("Kolom 'Status' ontbreekt (vaststaand / stelling <partij> ...).")
    last = None
    for n, row in enumerate(rows, 1):
        label = "Rij %d" % n
        datum, bron = row[c_datum], row[c_bron]
        if not _clean(row[c_geb]):
            errors.append("%s: gebeurtenis is leeg." % label)
        if not _clean(bron) or _clean(bron) in ("-", "?"):
            errors.append("%s: geen bron. Elk feit heeft een bron (document + pagina/alinea)." % label)
        elif not re.search(r"\bD\d+\b", bron):
            warnings.append("%s: bron '%s' noemt geen stukcode (D1, D2, ...)." % (label, _clean(bron)))
        elif re.fullmatch(r"(D\d+[;,]?\s*)+", _clean(bron)):
            warnings.append("%s: bron '%s' noemt alleen het stuk; voeg pagina/alinea/punt/tijdstip toe." % (label, _clean(bron)))
        if not date_ok(datum):
            errors.append("%s: datum '%s' voldoet niet. Gebruik JJJJ-MM-DD (evt. JJJJ-MM, JJJJ, periode, "
                          "'onbekend') of markeer een afgeleide datum als '± ... (afgeleid: ...)'." % (label, _clean(datum)))
        if c_status is not None:
            st = _clean(row[c_status]).lower()
            if not (st.startswith("vaststaand") or st.startswith("stelling ")):
                errors.append("%s: status '%s' onbekend; gebruik 'vaststaand' of 'stelling <partij> ...'." % (label, _clean(row[c_status])))
            elif "betwist" in st and "onbetwist" not in st and "(" not in st:
                warnings.append("%s: 'betwist' zonder bron van de betwisting tussen haakjes." % label)
        key = sort_key(datum)
        if key is None:  # 'onbekend' rows belong at the bottom
            last = (9999, 99, 99)
        else:
            if last is not None and key < last:
                warnings.append("%s: niet chronologisch gesorteerd (datum '%s')." % (label, _clean(datum)))
            last = key
    return errors, warnings


def write_csv(header, rows, path, delimiter=";"):
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
        w.writerow([_clean(h) for h in header])
        for row in rows:
            w.writerow([_clean(c) for c in row])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Chronologietabel (markdown) naar CSV en/of controle.")
    ap.add_argument("bestand", help="markdownbestand met de chronologie")
    ap.add_argument("-o", "--uitvoer", help="CSV-bestand om te schrijven")
    ap.add_argument("--controleer", action="store_true", help="controleer de regels van de skill")
    ap.add_argument("--scheidingsteken", default=";", help="standaard ';' (Nederlandse Excel)")
    args = ap.parse_args(argv)
    with open(args.bestand, encoding="utf-8") as fh:
        header, rows = find_table(fh.read())
    code = 0
    if args.controleer or not args.uitvoer:
        errors, warnings = check(header, rows)
        for e in errors:
            print("FOUT: " + e)
        for w in warnings:
            print("LET OP: " + w)
        print("%d rijen gecontroleerd: %d fout(en), %d waarschuwing(en)." % (len(rows), len(errors), len(warnings)))
        code = 1 if errors else 0
    if args.uitvoer:
        if header is None:
            print("Geen chronologietabel gevonden; geen CSV geschreven.", file=sys.stderr)
            return 1
        write_csv(header, rows, args.uitvoer, args.scheidingsteken)
        print("CSV geschreven: %s (%d rijen)" % (args.uitvoer, len(rows)))
    return code


if __name__ == "__main__":
    sys.exit(main())
