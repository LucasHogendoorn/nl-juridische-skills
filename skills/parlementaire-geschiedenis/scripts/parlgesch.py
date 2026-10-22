#!/usr/bin/env python3
"""Parlementaire geschiedenis zoeken en ophalen via de officiële KOOP SRU-dienst.

Gebruik (vanuit de skillmap):
    python3 scripts/parlgesch.py dossier 33818                 # kernstukken van een dossier
    python3 scripts/parlgesch.py dossier 33818 --alles         # ook moties, brieven, bijlagen
    python3 scripts/parlgesch.py wet "Wet arbeidsmarkt in balans"   # welk dossiernummer?
    python3 scripts/parlgesch.py zoek transitievergoeding --soort mvt
    python3 scripts/parlgesch.py zoek --artikel "7:673 BW" --soort toelichting
    python3 scripts/parlgesch.py zoek "onrechtmatige daad" --voor-1995 --dossier 7729
    python3 scripts/parlgesch.py haal kst-33818-3 --artikel "7:673 lid 7" --trefwoord transitievergoeding
    python3 scripts/parlgesch.py haal kst-33818-3 --volledig -o mvt.md

Bron: https://repository.overheid.nl/sru (officielepublicaties vanaf ±1995; sgd = Staten-Generaal
Digitaal 1814-1995, OCR). Alleen ruwe Kamerstukken en Handelingen; de samengestelde boekenreeks
"Parlementaire Geschiedenis van het NBW" zit er niet in.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import koop_sru_client as k  # noqa: E402
import nl_http  # noqa: E402

OP = "officielepublicaties"
SGD = "sgd"

SOORTEN = {
    "mvt": ["Memorie van toelichting"],
    "nnavv": ["Nota naar aanleiding van het verslag"],
    "nvw": ["Nota van wijziging"],
    "mva": ["Memorie van antwoord"],
    "verslag": ["Verslag", "Voorlopig verslag"],
    "wetsvoorstel": ["Voorstel van wet", "Gewijzigd voorstel van wet"],
    "raad-van-state": ["Advies Afdeling advisering Raad van State en Nader rapport"],
}
SOORTEN["toelichting"] = (SOORTEN["mvt"] + SOORTEN["nnavv"] + SOORTEN["nvw"] + SOORTEN["mva"]
                          + ["Nadere memorie van antwoord"])
SGD_SOORTEN = {
    "mvt": ["memorie van toelichting"],
    "nnavv": ["nota naar aanleiding van het verslag", "nota naar aanleiding van het eindverslag"],
    "nvw": ["nota van wijziging"],
    "mva": ["memorie van antwoord"],
    "verslag": ["voorlopig verslag", "eindverslag", "verslag"],
    "wetsvoorstel": ["ontwerp van wet", "gewijzigd ontwerp van wet"],
}
SGD_SOORTEN["toelichting"] = (SGD_SOORTEN["mvt"] + SGD_SOORTEN["nnavv"] + SGD_SOORTEN["nvw"]
                              + SGD_SOORTEN["mva"])

# Order in which a dossier overview is printed.
GROEPEN = [
    ("Wetsvoorstel", r"^(koninklijke boodschap|voorstel van wet|gewijzigd voorstel van wet|ontwerp van wet)"),
    ("Memorie van toelichting", r"memorie van toelichting"),
    ("Advies Raad van State / nader rapport", r"raad van state|nader rapport"),
    ("Verslagen", r"^(voorlopig |nader )?(eind)?verslag\b"),
    ("Nota's n.a.v. verslag / memories van antwoord", r"nota naar aanleiding|^nnv$|memorie van antwoord"),
    ("Nota's van wijziging", r"nota van wijziging"),
    ("Amendementen", r"amendement"),
    ("Moties", r"motie"),
    ("Brieven", r"^brief|^reactie|^aanbieding"),
]
KERNGROEPEN = {g for g, _ in GROEPEN[:7]}


# --------------------------------------------------------------------------- pure helpers

def groep_van(record: k.Record) -> str:
    titel = (record.get("documenttitel") or " ".join(record.descriptions[:1])).strip().lower()
    sub = record.get("subrubriek").lower()
    if record.type.lower() == "bijlage":
        return "Bijlagen"
    if sub == "amendement":
        return "Amendementen"
    if sub == "motie":
        return "Moties"
    for naam, patroon in GROEPEN:
        if re.search(patroon, titel):
            return naam
    if sub == "brief":
        return "Brieven"
    return "Overig"


def ondernummer_sleutel(record: k.Record):
    onder = record.get("ondernummer") or record.identifier.rsplit("-", 1)[-1]
    m = re.match(r"(\d+)", onder)
    return (0, int(m.group(1)), onder) if m else (1, 0, onder)


def parse_artikel(text: str) -> dict | None:
    """'art. 7:673 lid 7 BW' -> {'boek': '7', 'nr': '673', 'lid': '7', 'label': '7:673'}.
    Also 'artikel 6.3.1.1' (NBW-ontwerpnummering) and 'art. 3 Awb'."""
    if not text:
        return None
    t = text.strip()
    lid = None
    m_lid = re.search(r"\blid\s+(\d+)|(\d+)(?:e|ste|de)\s+lid", t, re.I)
    if m_lid:
        lid = m_lid.group(1) or m_lid.group(2)
    m = re.search(r"(\d+)\s*:\s*(\d+[a-z]*)", t, re.I)
    if m:
        return {"boek": m.group(1), "nr": m.group(2), "lid": lid, "label": f"{m.group(1)}:{m.group(2)}"}
    m = re.search(r"(\d+(?:\.\d+[a-z]?){2,})", t, re.I)
    if m:
        return {"boek": None, "nr": m.group(1), "lid": lid, "label": m.group(1)}
    m = re.search(r"(?:art(?:ikel)?\.?\s*)?(\d+[a-z]*)", t, re.I)
    if m:
        return {"boek": None, "nr": m.group(1), "lid": lid, "label": m.group(1)}
    return None


RANGTELWOORDEN = ["", "eerste", "tweede", "derde", "vierde", "vijfde", "zesde", "zevende",
                  "achtste", "negende", "tiende", "elfde", "twaalfde", "dertiende", "veertiende",
                  "vijftiende"]


def artikel_patronen(art: dict) -> tuple:
    """(regex for the article, regex for the lid or None). Matches '7:673', 'artikel 673'
    (as used in wijzigingswetten: 'Artikel I, onderdeel K (artikel 673)'), '6.3.1.1'."""
    nr = re.escape(art["nr"])
    if art.get("boek"):
        art_re = rf"\b{art['boek']}\s*:\s*{nr}(?![0-9a-z])|\bartikel(?:en)?\s+{nr}(?![0-9a-z:.])"
    else:
        art_re = rf"(?<![0-9.]){nr}(?![0-9a-z])" if "." in art["nr"] else rf"\bartikel(?:en)?\s+{nr}(?![0-9a-z])"
    lid_re = None
    if art.get("lid"):
        n = int(art["lid"])
        woord = RANGTELWOORDEN[n] if n < len(RANGTELWOORDEN) else ""
        lid_re = rf"\blid\s+{n}\b" + (rf"|\b{woord}\s+lid\b" if woord else "")
    return re.compile(art_re, re.I), (re.compile(lid_re, re.I) if lid_re else None)


# Lowercase "onderdeel a" is a sub-heading of an article; uppercase "Onderdeel V (artikel ...)"
# in a wijzigingswet introduces a new article and must not match.
_SUBKOP = re.compile(r"^\s*(?:(?:[A-Za-z]+|\d+e?)\s+[Ll]id\b|[Ll]id\s+\d+|[Oo]nderdeel\s+[a-z]{1,2}\b)")

_INTRO = re.compile(r"\bartikel(?:en)?\s+(?:\d+\s*:\s*)?\d+[a-z]*\b|^onderdeel\s+[a-z]+\b|^artikel\s+[ivxl]+\b",
                    re.I)


def artikel_context(blocks: list, art_re) -> dict:
    """In an artikelsgewijze toelichting the article under discussion is usually named once
    ("Met dit onderdeel wordt artikel 7:673 BW ingevoegd ...", "Artikel 7:673a BW behelst ...")
    and the following paragraphs ("Het zevende lid ...") do not repeat it. Mark paragraphs
    that follow an introduction of the target article until another article is introduced
    in the opening words of a paragraph or a new heading starts."""
    ctx: dict = {}
    huidig = 0  # 0 = not about the article, 1 = introduced in the text, 2 = under its own heading
    for i, b in enumerate(blocks):
        if b.kind == "kop":
            # "Eerste lid: ...", "Onderdeel a: ..." are sub-headings of the article above.
            if not _SUBKOP.match(b.text):
                huidig = 2 if art_re.search(b.text) else 0
            continue
        opening = b.text[:90]
        intro = _INTRO.search(opening)
        if intro:
            huidig = 1 if (art_re.search(intro.group(0)) or art_re.search(opening)) else 0
        ctx[i] = huidig
    return ctx


def vind_passages(blocks: list, artikel: dict | None, trefwoorden: list, max_passages: int = 8,
                  context: int = 1) -> list:
    """Score each paragraph: article in heading or text (+3), under a heading naming the
    article (+2 extra), lid (+2), each keyword (+1).
    Returns the best passages with neighbouring paragraphs as context."""
    art_re, lid_re = artikel_patronen(artikel) if artikel else (None, None)
    kws = [w.lower() for w in trefwoorden if w.strip()]
    context_van = artikel_context(blocks, art_re) if art_re is not None else {}
    scored = []
    for i, b in enumerate(blocks):
        if b.kind == "kop":
            continue
        tekst = k.normalize(b.text)
        kop = " / ".join(b.headings)
        score = 0
        if art_re is not None:
            if art_re.search(b.text) or context_van.get(i):
                score += 3
                if context_van.get(i) == 2:
                    score += 2  # artikelsgewijze toelichting under a heading naming the article
            elif art_re.search(kop):
                score += 2
        if lid_re is not None and lid_re.search(b.text):
            score += 2
        hits = sum(1 for w in kws if w in tekst)
        score += hits
        if art_re is not None and kws and hits == 0 and score < 5:
            continue  # article-only match without keyword: keep only strong ones
        if score >= (2 if (art_re is not None or len(kws) > 1) else 1):
            scored.append((score, i))
    scored.sort(key=lambda x: (-x[0], x[1]))
    chosen: list = []
    used: set = set()
    for score, i in scored:
        if i in used:
            continue
        lo, hi = max(0, i - context), min(len(blocks), i + context + 1)
        idxs = [j for j in range(lo, hi) if blocks[j].kind != "kop"]
        used.update(range(lo, hi))
        chosen.append({"score": score, "index": i, "kop": " / ".join(blocks[i].headings),
                       "tekst": "\n\n".join(blocks[j].text for j in idxs),
                       "kern": blocks[i].text})
        if len(chosen) >= max_passages:
            break
    return chosen  # best first


def pagina_voor(passage_tekst: str, paginas: list) -> int | None:
    """Find the printed page of a passage by matching a distinctive stretch of it."""
    norm = k.normalize(passage_tekst)
    woorden = norm.split()
    if len(woorden) < 6 or not paginas:
        return None
    genormaliseerd = [(p, k.normalize(t)) for p, t in paginas]
    for start in (0, len(woorden) // 3, max(0, len(woorden) - 10)):
        stuk = " ".join(woorden[start:start + 8])
        for p, t in genormaliseerd:
            if p is not None and stuk in t:
                return p
    return None


def soort_clause(soort: str | None, sgd: bool) -> str:
    if not soort or soort == "alle":
        return ""
    if soort == "amendement" and not sgd:
        return 'w.subrubriek=="Amendement"'
    tabel = SGD_SOORTEN if sgd else SOORTEN
    waarden = tabel.get(soort)
    if not waarden:
        raise SystemExit(f"Onbekende --soort '{soort}'. Kies uit: {', '.join(sorted(tabel))}, alle.")
    index = "dt.description" if sgd else "w.documenttitel"
    parts = [k.cql_clause(index, w, "=") for w in waarden]
    return parts[0] if len(parts) == 1 else "(" + " OR ".join(parts) + ")"


def bouw_zoekvraag(termen: list, soort: str | None = None, dossier: str | None = None,
                   wet: str | None = None, artikel: str | None = None, van: str | None = None,
                   tot: str | None = None, sgd: bool = False, kamer: str | None = None) -> str:
    clauses = [k.cql_clause("c.product-area", SGD if sgd else OP)]
    if not sgd:
        clauses.append(k.cql_clause("dt.type", "Kamerstuk"))
    clauses.append(soort_clause(soort, sgd))
    if dossier:
        clauses.append(k.cql_clause("w.dossiernummer", dossier))
    if wet:
        clauses.append(k.cql_clause("dt.title" if sgd else "w.dossiertitel", wet, "="))
    if artikel:
        art = parse_artikel(artikel)
        if art:
            clauses.append(k.cql_clause("cql.textAndIndexes", art["label"], "="))
    for t in termen:
        clauses.append(k.cql_clause("cql.textAndIndexes", t, "="))
    if van and not sgd:
        clauses.append(f"dt.date>={van}")
    if tot and not sgd:
        clauses.append(f"dt.date<={tot}")
    if kamer and not sgd:
        clauses.append(k.cql_clause("dt.creator", "Eerste Kamer der Staten-Generaal" if kamer == "ek"
                                    else "Tweede Kamer der Staten-Generaal"))
    return k.cql_and(*clauses)


def regel(record: k.Record) -> str:
    soort = record.get("documenttitel") or (record.descriptions[0] if record.descriptions else record.type)
    datum = record.date or record.available
    return (f"- **{k.kamerstuk_citation(record)}** ({datum}) — {soort[:160]}\n"
            f"  id: `{record.identifier}` · {record.preferred_url}")


# --------------------------------------------------------------------------- commands

def cmd_dossier(args) -> int:
    sgd = args.voor_1995
    area = SGD if sgd else OP
    res = k.search_all(k.cql_and(k.cql_clause("c.product-area", area),
                                 k.cql_clause("w.dossiernummer", args.nummer)), limit=args.max)
    if not res.records:
        print(f"Geen stukken gevonden voor dossier {args.nummer} in '{area}'."
              + ("" if sgd else " Voor stukken van vóór 1995: voeg --voor-1995 toe."))
        return 1
    titels = [r.get("dossiertitel") or r.title for r in res.records
              if r.type.lower() != "bijlage" and (r.get("dossiertitel") or r.title)]
    titel = max(set(titels), key=titels.count) if titels else ""
    print(f"# Dossier {args.nummer}: {titel}\n")
    print(f"{res.total} stukken in de SRU-index ({area}); hieronder "
          f"{'alle' if args.alles else 'de kernstukken'}.\n")
    groepen: dict = {}
    for r in res.records:
        groepen.setdefault(groep_van(r), []).append(r)
    volgorde = [g for g, _ in GROEPEN] + ["Overig", "Bijlagen"]
    for g in volgorde:
        items = groepen.get(g)
        if not items or (not args.alles and g not in KERNGROEPEN):
            continue
        print(f"## {g} ({len(items)})\n")
        for r in sorted(items, key=lambda r: (r.date or "", ondernummer_sleutel(r))):
            print(regel(r))
        print()
    if not args.alles:
        rest = sum(len(v) for g, v in groepen.items() if g not in KERNGROEPEN)
        if rest:
            print(f"_({rest} overige stukken — moties, brieven, bijlagen — weggelaten; gebruik --alles.)_\n")
    if not sgd:
        hq = k.cql_and(k.cql_clause("c.product-area", OP),
                       k.cql_clause("w.behandeldDossier", f"{args.nummer}*", "="))
        hres = k.search_all(hq, limit=300)
        soorten = [("Handelingen", "h-"), ("Staatsblad", "stb-")]
        if args.alles:
            soorten += [("Agenda's en Staatscourant", "")]
        gezien: set = set()
        for kop, prefix in soorten:
            items = [r for r in hres.records if r.identifier.startswith(prefix)
                     and r.identifier not in gezien]
            if not items:
                continue
            gezien.update(r.identifier for r in items)
            print(f"## {kop} ({len(items)})\n")
            for r in sorted(items, key=lambda r: (r.date, r.identifier)):
                cite = k.kamerstuk_citation(r) if prefix == "h-" else re.sub(
                    r"^stb-(\d{4})-(\d+)$", r"Stb. \1, \2", r.identifier)
                print(f"- **{cite}** ({r.date}) — {r.title[:140]}\n"
                      f"  id: `{r.identifier}` · {r.preferred_url}")
            print()
    if res.total > len(res.records):
        print(f"Let op: {res.total - len(res.records)} stukken niet opgehaald (verhoog --max).")
    return 0


def cmd_wet(args) -> int:
    q = k.cql_and(k.cql_clause("c.product-area", OP), k.cql_clause("dt.type", "Kamerstuk"),
                  k.cql_clause("w.dossiertitel", args.naam, "="))
    res = k.search_all(q, limit=args.max)
    dossiers: dict = {}
    for r in res.records:
        nr = r.get("dossiernummer")
        if not nr:
            continue
        d = dossiers.setdefault(nr, {"titel": r.get("dossiertitel") or r.title, "n": 0, "eerste": r.date,
                                     "laatste": r.date})
        d["n"] += 1
        d["eerste"] = min(d["eerste"] or r.date, r.date or d["eerste"])
        d["laatste"] = max(d["laatste"] or r.date, r.date or d["laatste"])
    if not dossiers:
        print(f"Geen dossier gevonden met '{args.naam}' in de dossiertitel. Probeer de citeertitel "
              "zonder afkorting (bijv. 'Wet werk en zekerheid' i.p.v. 'WWZ'), of `zoek` met trefwoorden.")
        return 1
    print(f"# Dossiers met '{args.naam}' in de titel ({res.total} stukken bekeken)\n")
    for nr, d in sorted(dossiers.items(), key=lambda x: -x[1]["n"]):
        print(f"- **{nr}** — {d['titel'][:220]} ({d['n']} stukken, {d['eerste']} – {d['laatste']})")
    return 0


def cmd_zoek(args) -> int:
    sgd = args.voor_1995
    if not (args.termen or args.artikel or args.dossier or args.wet):
        print("Geef minstens een zoekterm, --artikel, --dossier of --wet.", file=sys.stderr)
        return 2
    q = bouw_zoekvraag(args.termen, args.soort, args.dossier, args.wet, args.artikel,
                       args.van, args.tot, sgd, args.kamer)
    if args.sorteer == "datum":
        q = k.with_sort(q, "dt.date")
    res = k.search(q, max_records=args.n)
    if args.json:
        print(json.dumps({"query": q, "total": res.total,
                          "records": [r.as_dict() for r in res.records]}, ensure_ascii=False, indent=1))
        return 0
    print(f"Zoekvraag (CQL): `{q}`\n{res.total} resultaten; eerste {len(res.records)}:\n")
    for r in res.records:
        print(regel(r))
    if sgd:
        print("\nLet op: stukken van vóór 1995 zijn OCR van scans; controleer citaten tegen de pdf.")
    if res.total == 0:
        print("Geen resultaten. Tips: minder termen, geen afkortingen, andere --soort, of --voor-1995.")
    return 0


def gedrukte_paginas(paginas: list) -> dict:
    """Map scan page index -> printed page number for OCR pages.

    The printed number is a bare 1-4 digit line at the top or bottom of some pages. The most
    common offset (printed - index) is applied to all pages; without evidence the scan index
    is kept. Returns {index: printed}."""
    from collections import Counter
    offsets = Counter()
    for idx, tekst in paginas:
        regels = [r.strip() for r in tekst.splitlines() if r.strip()]
        for r in regels[:2] + regels[-2:]:
            if re.fullmatch(r"\d{1,4}", r):
                offsets[int(r) - idx] += 1
                break
    if not offsets:
        return {idx: idx for idx, _ in paginas}
    offset, n = offsets.most_common(1)[0]
    if n < 2 and len(paginas) > 3:
        return {idx: idx for idx, _ in paginas}
    return {idx: idx + offset for idx, _ in paginas}


def _bereik(tekst: str | None) -> tuple:
    if not tekst:
        return None, None
    m = re.fullmatch(r"\s*(\d+)?\s*-\s*(\d+)?\s*|\s*(\d+)\s*", tekst)
    if not m:
        raise SystemExit("--paginas verwacht bijv. 120-180, 120- of 45.")
    if m.group(3):
        return int(m.group(3)), int(m.group(3))
    return (int(m.group(1)) if m.group(1) else None, int(m.group(2)) if m.group(2) else None)


def _markdown_kop(record: k.Record) -> str:
    soort = record.get("documenttitel") or (record.descriptions[0] if record.descriptions else "")
    return (f"# {k.kamerstuk_citation(record)} — {soort}\n\n"
            f"- Dossier: {record.get('dossiertitel') or record.title}\n"
            f"- Datum: {record.date}\n- Bron: {record.preferred_url}\n")


def cmd_haal(args) -> int:
    record = k.get_record(args.id)
    if record is None:
        print(f"Geen document gevonden met id '{args.id}'. Gebruik een id uit `dossier` of `zoek` "
              "(bijv. kst-33818-3, h-tk-20132014-55-18 of 0000115981).", file=sys.stderr)
        return 1
    artikel = parse_artikel(args.artikel) if args.artikel else None
    trefwoorden = args.trefwoord or []
    is_sgd = record.product_area == SGD

    if is_sgd:
        van_p, tot_p = _bereik(args.paginas)
        n_ocr = len(record.manifestations.get("ocr") or [])
        if n_ocr > 20:
            print(f"(OCR: {min(n_ocr, args.max_paginas)} van {n_ocr} pagina's ophalen, ±1 per seconde; "
                  "eerder opgehaalde pagina's komen uit de cache.)", file=sys.stderr)
        paginas = k.sgd_ocr_pages(record, max_pages=args.max_paginas, first_page=van_p, last_page=tot_p)
        gedrukt = gedrukte_paginas(paginas)
        blocks = []
        for p, tekst in paginas:
            for par in tekst.split("\n"):
                if par.strip():
                    blocks.append(k.Block("al", par.strip(), (f"pagina {gedrukt[p]}",)))
        pagina_van = {id(b): int(b.headings[0].split()[-1]) for b in blocks}
        waarschuwing = ("Let op: OCR-tekst van een scan (Staten-Generaal Digitaal). Controleer elk "
                        f"citaat tegen de pdf: {record.url('pdf')}")
        if paginas and len(paginas) < n_ocr:
            waarschuwing += (f"\nAlleen pagina {paginas[0][0]}–{paginas[-1][0]} van {n_ocr} gelezen "
                             "(gebruik --paginas VAN-TOT of --max-paginas).")
    else:
        blocks = k.officiele_publicatie_blocks(k.fetch_xml(record))
        pagina_van = {}
        waarschuwing = ""

    if args.volledig or not (artikel or trefwoorden):
        md = _markdown_kop(record) + "\n" + (waarschuwing + "\n\n" if waarschuwing else "")
        md += k.blocks_to_markdown(blocks)
        if args.uitvoer:
            with open(args.uitvoer, "w", encoding="utf-8") as fh:
                fh.write(md)
            print(f"Geschreven: {args.uitvoer} ({len(md)} tekens, {len(blocks)} blokken).")
        else:
            print(md)
        return 0

    passages = vind_passages(blocks, artikel, trefwoorden, max_passages=args.max_passages)
    paginas_pdf = []
    if passages and not is_sgd and not args.geen_paginas and record.url("pdf"):
        try:
            pdf = nl_http.get(record.url("pdf"), accept="application/pdf").body
            paginas_pdf = k.pdf_pages(pdf, record.get("ondernummer") or None)
        except nl_http.FetchError as exc:
            print(f"(Paginanummers niet beschikbaar: {exc})", file=sys.stderr)
    print(_markdown_kop(record))
    if waarschuwing:
        print(waarschuwing + "\n")
    zoek = ", ".join(([f"artikel {artikel['label']}" + (f" lid {artikel['lid']}" if artikel.get("lid") else "")]
                      if artikel else []) + [f"'{w}'" for w in trefwoorden])
    if not passages:
        print(f"Geen passages gevonden voor {zoek}. Probeer een ander trefwoord of lees het stuk "
              "met --volledig.")
        return 1
    print(f"{len(passages)} passage(s) voor {zoek} (meest relevant eerst):\n")
    for p in passages:
        blk = blocks[p["index"]]
        pagina = pagina_van.get(id(blk)) if is_sgd else pagina_voor(p["kern"], paginas_pdf)
        cite = k.kamerstuk_citation(record, pagina)
        print(f"### {cite}")
        if p["kop"] and not is_sgd:
            print(f"_Paragraaf: {p['kop'][:300]}_\n")
        tekst = p["tekst"] if len(p["tekst"]) < 3000 else p["tekst"][:3000] + " […]"
        print("> " + tekst.replace("\n\n", "\n>\n> ") + "\n")
    if not is_sgd and not paginas_pdf and not args.geen_paginas:
        print("(Paginanummer niet te bepalen uit de pdf; citeer met paragraaf of controleer in de pdf: "
              f"{record.url('pdf')})")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Parlementaire geschiedenis via de KOOP SRU-dienst.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dossier", help="kernstukken (en Handelingen) van een Kamerstukdossier")
    d.add_argument("nummer")
    d.add_argument("--alles", action="store_true", help="ook moties, brieven, bijlagen")
    d.add_argument("--voor-1995", action="store_true", help="zoek in Staten-Generaal Digitaal (1814-1995)")
    d.add_argument("--max", type=int, default=400)
    d.set_defaults(func=cmd_dossier)

    w = sub.add_parser("wet", help="dossiernummer(s) bij een wetsnaam")
    w.add_argument("naam")
    w.add_argument("--max", type=int, default=300)
    w.set_defaults(func=cmd_wet)

    z = sub.add_parser("zoek", help="vrij zoeken in Kamerstukken")
    z.add_argument("termen", nargs="*", help="zoektermen; elke term/zinsnede apart (alle moeten voorkomen)")
    z.add_argument("--soort", help="mvt, nnavv, nvw, mva, verslag, wetsvoorstel, raad-van-state, "
                                   "amendement, toelichting (= mvt+nnavv+nvw+mva), alle")
    z.add_argument("--dossier")
    z.add_argument("--wet", help="woorden uit de dossiertitel, bijv. 'Wet werk en zekerheid'")
    z.add_argument("--artikel", help="bijv. '7:673 BW' (zoekt de tekst '7:673')")
    z.add_argument("--van", help="datum JJJJ-MM-DD (niet voor --voor-1995)")
    z.add_argument("--tot", help="datum JJJJ-MM-DD (niet voor --voor-1995)")
    z.add_argument("--kamer", choices=["tk", "ek"])
    z.add_argument("--voor-1995", action="store_true")
    z.add_argument("--sorteer", choices=["relevantie", "datum"], default="relevantie")
    z.add_argument("-n", type=int, default=15)
    z.add_argument("--json", action="store_true")
    z.set_defaults(func=cmd_zoek)

    h = sub.add_parser("haal", help="document ophalen en passages vinden")
    h.add_argument("id", help="kst-33818-3, h-tk-20132014-55-18, of SGD-id als 0000115981")
    h.add_argument("--artikel", help="bijv. '7:673 lid 7' of '6.3.1.1' (NBW-ontwerpnummering)")
    h.add_argument("--trefwoord", action="append", help="herhaalbaar")
    h.add_argument("--volledig", action="store_true", help="hele tekst als markdown")
    h.add_argument("-o", "--uitvoer")
    h.add_argument("--max-passages", type=int, default=8)
    h.add_argument("--max-paginas", type=int, default=300, help="SGD: max. aantal OCR-pagina's")
    h.add_argument("--paginas", help="SGD: bereik van scanpagina's (volgorde in de scan), bijv. 120-180")
    h.add_argument("--geen-paginas", action="store_true", help="pdf niet ophalen voor paginanummers")
    h.set_defaults(func=cmd_haal)

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except (k.SruError, nl_http.FetchError) as exc:
        print(f"FOUT: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
