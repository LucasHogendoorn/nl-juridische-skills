"""Client for the official KOOP SRU 2.0 search service (stdlib only).

Endpoint: https://repository.overheid.nl/sru  (Handleiding SRU 2.0, Logius/KOOP).
KOOP applies a "fair use" policy and prefers this API over scraping. We identify
honestly (nl_http: ``User-Agent: nl-juridische-skills/<versie>``), throttle to about
one request per second per host and retry transient errors.

Collections used (``c.product-area``):
    officielepublicaties  Kamerstukken, Handelingen, Staatsblad, Staatscourant (±1995 onward)
    sgd                   Staten-Generaal Digitaal, 1814-1995 (scans + OCR text per page)
    tuchtrecht            disciplinary decisions (advocaten, gezondheidszorg, notarissen, ...)

Pages on wetten.overheid.nl and the old zoek.officielebekendmakingen.nl/sru are
never used.

Public interface (stable for the skills that bundle this file):
    SRU_URL
    cql_quote(value) -> str
    cql_clause(index, value, relation="==") -> str
    cql_and(*clauses) -> str                        (skips empty clauses)
    with_sort(query, index, descending=True) -> str
    search(query, max_records=20, start=1) -> SearchResult
    search_all(query, limit=200, page_size=100) -> SearchResult   (follows paging)
    parse_response(xml_bytes) -> SearchResult
    get_record(identifier, product_area=None) -> Record | None
    fetch_xml(record) -> bytes
    officiele_publicatie_blocks(xml_bytes) -> list[Block]
    blocks_to_markdown(blocks) -> str
    uitspraak_to_markdown(xml_bytes) -> str          (tuchtrecht <uitspraak>)
    sgd_ocr_pages(record, max_pages=80, first_page=None, last_page=None) -> list[(pagina, tekst)]
    pdf_pages(pdf_bytes, ondernummer=None) -> list[(pagina | None, tekst)]
    kamerstuk_citation(record, pagina=None) -> str   (Kamerstukken II 2013/14, 33818, nr. 3, p. 12)
    normalize(text) -> str                           (for matching: lower, de-hyphenate, 1 space)
Errors: SruError (bad query / unexpected answer), nl_http.FetchError (network).
"""
from __future__ import annotations

import re
import urllib.parse
import zlib
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

import nl_http

SRU_URL = "https://repository.overheid.nl/sru"
MAX_PAGE = 1000  # maximumRecords upper bound per the SRU manual

NS = {
    "sru": "http://docs.oasis-open.org/ns/search-ws/sruResponse",
    "gzd": "http://standaarden.overheid.nl/sru",
    "diag": "http://docs.oasis-open.org/ns/search-ws/diagnostic",
}


class SruError(Exception):
    """Query rejected or answer not understood (Dutch message)."""


# --------------------------------------------------------------------------- CQL

def cql_quote(value: str) -> str:
    """Quote a CQL term. Always quotes; escapes backslash and double quote."""
    value = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def cql_clause(index: str, value: str, relation: str = "==") -> str:
    """``index relation "value"``; relation e.g. '==', '=', '>=', '<=', 'any', 'all'."""
    if value is None or str(value).strip() == "":
        return ""
    sep = f" {relation} " if relation.isalpha() else relation
    return f"{index}{sep}{cql_quote(str(value).strip())}"


def cql_and(*clauses: str) -> str:
    parts = [c.strip() for c in clauses if c and c.strip()]
    return " AND ".join(parts)


def with_sort(query: str, index: str, descending: bool = True) -> str:
    """Append a CQL ``sortBy`` clause (supported by the KOOP SRU)."""
    order = "sort.descending" if descending else "sort.ascending"
    return f"{query} sortBy {index}/{order}"


# --------------------------------------------------------------------------- records

@dataclass
class Record:
    identifier: str = ""
    title: str = ""
    type: str = ""
    creator: str = ""
    date: str = ""            # dcterms:date / issued / uitspraakdatum / temporal
    available: str = ""
    product_area: str = ""
    descriptions: list = field(default_factory=list)
    subjects: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)          # tpmeta local-name -> [values]
    xml_url: str = ""          # gzd:url (main manifestation)
    preferred_url: str = ""
    manifestations: dict = field(default_factory=dict)  # name -> [urls]

    def get(self, name: str, default: str = "") -> str:
        vals = self.meta.get(name)
        return vals[0].strip() if vals else default

    def getall(self, name: str) -> list:
        return [v.strip() for v in self.meta.get(name, [])]

    def url(self, manifestation: str) -> str:
        urls = self.manifestations.get(manifestation) or []
        return urls[0] if urls else ""

    def as_dict(self) -> dict:
        return {
            "identifier": self.identifier, "title": self.title, "type": self.type,
            "creator": self.creator, "date": self.date, "product_area": self.product_area,
            "descriptions": self.descriptions, "subjects": self.subjects, "meta": self.meta,
            "xml_url": self.xml_url, "preferred_url": self.preferred_url,
            "manifestations": self.manifestations,
        }


@dataclass
class SearchResult:
    total: int
    records: list
    next_start: int | None = None
    query: str = ""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _text(el) -> str:
    return "".join(el.itertext()).strip() if el is not None else ""


def _parse_record(gzd) -> Record:
    rec = Record()
    original = gzd.find("gzd:originalData", NS)
    if original is not None:
        for el in original.iter():
            name = _local(el.tag)
            value = _text(el) if len(el) == 0 else ""
            if not value:
                continue
            if el.tag.startswith("{http://purl.org/dc/terms/}"):
                if name == "identifier" and not rec.identifier:
                    rec.identifier = value
                elif name == "title" and not rec.title:
                    rec.title = value
                elif name == "type" and not rec.type:
                    rec.type = value
                elif name == "creator" and not rec.creator:
                    rec.creator = value
                elif name in ("date", "issued") and not rec.date:
                    rec.date = value
                elif name == "temporal" and not rec.date:
                    rec.date = value
                elif name == "available":
                    rec.available = value
                elif name == "description":
                    rec.descriptions.append(" ".join(value.split()))
                elif name == "subject":
                    rec.subjects.append(value)
                continue
            if name == "product-area":
                rec.product_area = value
                continue
            if value:
                rec.meta.setdefault(name, []).append(value)
    enriched = gzd.find("gzd:enrichedData", NS)
    if enriched is not None:
        rec.xml_url = _text(enriched.find("gzd:url", NS))
        rec.preferred_url = _text(enriched.find("gzd:preferredUrl", NS))
        for item in enriched.findall("gzd:itemUrl", NS):
            rec.manifestations.setdefault(item.get("manifestation", "?"), []).append(_text(item))
    uitspraakdatum = rec.get("uitspraakdatum")
    if uitspraakdatum:
        rec.date = uitspraakdatum
    elif not rec.date:
        # For sgd records dcterms:available is the digitisation date, not the document date.
        rec.date = rec.get("datumVergadering") or ("" if rec.product_area == "sgd" else rec.available)
    return rec


def parse_response(xml_bytes: bytes) -> SearchResult:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise SruError(f"Het SRU-antwoord is geen geldige XML ({exc}).") from None
    diags = [_text(d) for d in root.iter("{%s}message" % NS["diag"])]
    total_el = root.find("sru:numberOfRecords", NS)
    if total_el is None:
        detail = "; ".join(d for d in diags if d) or "geen numberOfRecords in antwoord"
        raise SruError(f"De zoekvraag werd niet geaccepteerd door de SRU-dienst: {detail}")
    try:
        total = int(_text(total_el))
    except ValueError:
        total = 0
    records = [_parse_record(g) for g in root.iter("{%s}gzd" % NS["gzd"])]
    nxt = root.find("sru:nextRecordPosition", NS)
    next_start = int(_text(nxt)) if nxt is not None and _text(nxt).isdigit() else None
    if total == 0 and diags:
        raise SruError("De SRU-dienst meldt een probleem met de zoekvraag: " + "; ".join(diags))
    return SearchResult(total=total, records=records, next_start=next_start)


def _search_url(query: str, max_records: int, start: int) -> str:
    params = {
        "operation": "searchRetrieve", "version": "2.0", "query": query,
        "maximumRecords": str(max(1, min(int(max_records), MAX_PAGE))),
        "startRecord": str(max(1, int(start))),
    }
    return SRU_URL + "?" + urllib.parse.urlencode(params)


def search(query: str, max_records: int = 20, start: int = 1) -> SearchResult:
    """One SRU searchRetrieve call."""
    if not query or not query.strip():
        raise SruError("Lege zoekvraag.")
    resp = nl_http.get(_search_url(query, max_records, start), accept="application/xml")
    result = parse_response(resp.body)
    result.query = query
    if result.next_start is None and start + len(result.records) <= result.total and result.records:
        result.next_start = start + len(result.records)
    return result


def search_all(query: str, limit: int = 200, page_size: int = 100) -> SearchResult:
    """Follow paging until ``limit`` records or the end of the result set."""
    records: list = []
    start = 1
    total = 0
    while len(records) < limit:
        chunk = search(query, max_records=min(page_size, limit - len(records)), start=start)
        total = chunk.total
        records.extend(chunk.records)
        if not chunk.records or chunk.next_start is None or chunk.next_start > total:
            break
        start = chunk.next_start
    return SearchResult(total=total, records=records[:limit], query=query)


def get_record(identifier: str, product_area: str | None = None) -> Record | None:
    """Look up one record by its identifier (kst-33818-3, ECLI:NL:TGZRAMS:2024:1, 0000115981)."""
    ident = identifier.strip()
    q = cql_and(cql_clause("c.product-area", product_area) if product_area else "",
                cql_clause("dt.identifier", ident))
    res = search(q, max_records=5)
    for rec in res.records:
        if rec.identifier.lower() == ident.lower():
            return rec
    return None


def fetch_xml(record: Record) -> bytes:
    url = record.url("xml") or (record.xml_url if record.xml_url.endswith(".xml") else "")
    if not url:
        raise SruError(f"Voor {record.identifier} is geen XML-versie beschikbaar "
                       f"(alleen: {', '.join(sorted(record.manifestations)) or 'onbekend'}).")
    return nl_http.get(url, accept="application/xml").body


# --------------------------------------------------------------------------- text

def normalize(text: str) -> str:
    """Lowercase, undo end-of-line hyphenation, collapse whitespace (for matching only)."""
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = text.replace("­", "")
    return " ".join(text.lower().split())


@dataclass
class Block:
    kind: str          # "kop" | "al" | "li" | "rij" | "noot"
    text: str
    headings: tuple    # heading path at this point
    level: int = 0


_SKIP_TAGS = {"metadata", "meta", "colspec", "plaatje", "illustratie"}
_HEADING_TAGS = {"kop"}
_PARA_TAGS = {"al", "tekstregel", "noot.al", "bijschrift", "stuknr", "dossiernr"}


def _clean(s: str) -> str:
    return " ".join(s.split())


def _has_own_text(el) -> bool:
    if el.text and el.text.strip():
        return True
    return any(c.tail and c.tail.strip() for c in el)


def officiele_publicatie_blocks(xml_bytes: bytes) -> list:
    """Linear blocks (headings + paragraphs) from an officiele-publicatie XML
    (Kamerstuk, Handeling, Stb, Stcrt). Keeps the heading path for each block.
    ``<kop>`` opens a (nested) heading; ``<tussenkop>`` is a sub-heading such as
    "Onderdeel V (artikel 7:673 BW)" in an artikelsgewijze toelichting and holds
    until the next tussenkop or kop."""
    try:
        root = ET.fromstring(xml_bytes.lstrip(b"\xef\xbb\xbf"))
    except ET.ParseError as exc:
        raise SruError(f"Het document is geen geldige XML ({exc}).") from None
    blocks: list = []
    path: list = []  # [(depth, title)]
    sub = [""]       # current tussenkop

    def heads() -> tuple:
        return tuple(t for _, t in path) + ((sub[0],) if sub[0] else ())

    def walk(el, depth: int) -> None:
        tag = _local(el.tag)
        if tag in _SKIP_TAGS:
            return
        if tag in _HEADING_TAGS:
            title = _clean("".join(el.itertext()))
            if title:
                while path and path[-1][0] >= depth:
                    path.pop()
                path.append((depth, title))
                sub[0] = ""
                blocks.append(Block("kop", title, heads(), len(path)))
            return
        if tag == "tussenkop":
            title = _clean("".join(el.itertext()))
            if title:
                sub[0] = title
                blocks.append(Block("kop", title, heads(), len(path) + 1))
            return
        if tag == "noot":
            nr = _clean(_text(el.find("noot.nr"))) if el.find("noot.nr") is not None else ""
            body = _clean(" ".join(_clean("".join(a.itertext())) for a in el.iter()
                                   if _local(a.tag) == "noot.al"))
            if body:
                blocks.append(Block("noot", (f"[{nr}] " if nr else "") + body, heads()))
            return
        if tag == "li":
            txt = _clean(" ".join(_clean("".join(c.itertext())) for c in el))
            if txt:
                blocks.append(Block("li", txt, heads()))
            return
        if tag == "row":
            cells = [_clean("".join(e.itertext())) for e in el if _local(e.tag) == "entry"]
            cells = [c for c in cells if c]
            if cells:
                blocks.append(Block("rij", " | ".join(cells), heads()))
            return
        if tag in _PARA_TAGS or _has_own_text(el):
            txt = _clean("".join(el.itertext()))
            if txt:
                blocks.append(Block("al", txt, heads()))
            return
        for child in el:
            walk(child, depth + 1)

    walk(root, 0)
    return blocks


def blocks_to_markdown(blocks: list) -> str:
    out: list = []
    notes: list = []
    for b in blocks:
        if b.kind == "kop":
            out.append("\n" + "#" * min(2 + b.level, 6) + " " + b.text + "\n")
        elif b.kind == "li":
            out.append("- " + b.text)
        elif b.kind == "noot":
            notes.append(b.text)
        else:
            out.append(b.text + "\n")
    if notes:
        out.append("\n## Voetnoten\n")
        out.extend(notes)
    return "\n".join(out).strip() + "\n"


def uitspraak_to_markdown(xml_bytes: bytes) -> str:
    """Tuchtrecht <uitspraak> XML -> markdown (metadata header, inhoudsindicatie, tekst)."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise SruError(f"De uitspraak is geen geldige XML ({exc}).") from None

    def find_local(name: str):
        for el in root.iter():
            if _local(el.tag) == name:
                return el
        return None

    def paragraphs(el) -> list:
        if el is None:
            return []
        out = []
        for p in el.iter():
            if _local(p.tag) != "p":
                continue
            if any(_local(c.tag) == "p" for c in p):
                continue  # only innermost <p>
            t = _clean("".join(p.itertext()))
            if t:
                out.append(t)
        if not out:
            t = _clean("".join(el.itertext()))
            if t:
                out.append(t)
        return out

    ecli = _clean(_text(find_local("ecli"))) or _clean(_text(find_local("identifier")))
    inst = find_local("instantie")
    inst_txt = ", ".join(_clean(_text(c)) for c in inst) if inst is not None else ""
    lines = [f"# {ecli}", ""]
    for label, name in (("Instantie", None), ("Uitspraakdatum", "uitspraakdatum"),
                        ("Zaaknummer", "zaaknummer"), ("Onderwerp", "onderwerp"),
                        ("Beslissing", "beslissingen")):
        el = find_local(name) if name else None
        val = inst_txt if name is None else " — ".join(
            _clean(t) for t in (el.itertext() if el is not None else []) if _clean(t))
        if val:
            lines.append(f"- **{label}:** {val}")
    lines.append(f"- **Bron:** https://tuchtrecht.overheid.nl/{ecli}")
    ind = paragraphs(find_local("inhoudsindicatie"))
    if ind:
        lines += ["", "## Inhoudsindicatie", ""] + [p + "\n" for p in ind]
    body = paragraphs(find_local("uitspraaktekst"))
    if body:
        lines += ["", "## Uitspraak", ""] + [p + "\n" for p in body]
    return "\n".join(lines).strip() + "\n"


def _cache_dir():
    from pathlib import Path
    import os
    base = os.environ.get("NLJS_CACHE_DIR")
    root = Path(base) if base else Path.home() / ".cache" / "nl-juridische-skills"
    return root / "sgd"


def sgd_ocr_pages(record: Record, max_pages: int = 80, first_page: int | None = None,
                  last_page: int | None = None, progress=None) -> list:
    """Fetch the OCR text per page of a Staten-Generaal Digitaal record.

    Returns [(pagina, tekst)], pagina counted from the record's startpagina. One request
    per page (throttled), so ``first_page``/``last_page`` limit the range and pages are
    cached on disk (``$NLJS_CACHE_DIR/sgd`` or ``~/.cache/nl-juridische-skills/sgd``).
    OCR quality varies; check quotes against the scan (pdf/jpg) before relying on them.
    """
    urls = sorted(record.manifestations.get("ocr") or [])
    if not urls:
        raise SruError(f"Voor {record.identifier} is geen OCR-tekst beschikbaar.")
    try:
        start = int(record.get("startpagina", "1") or 1)
    except ValueError:
        start = 1
    numbered = [(start + i, u) for i, u in enumerate(urls)]
    if first_page is not None:
        numbered = [(p, u) for p, u in numbered if p >= first_page]
    if last_page is not None:
        numbered = [(p, u) for p, u in numbered if p <= last_page]
    numbered = numbered[:max_pages]
    cache = _cache_dir()
    pages = []
    for n, (pagina, url) in enumerate(numbered, 1):
        path = cache / re.sub(r"[^A-Za-z0-9_.-]", "_", url.split("/frbr/sgd/", 1)[-1])
        body = None
        try:
            if path.is_file():
                body = path.read_bytes()
        except OSError:
            body = None
        if body is None:
            if progress:
                progress(n, len(numbered))
            body = nl_http.get(url, accept="application/xml").body
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
            except OSError:
                pass
        pages.append((pagina, _ocr_text(body)))
    return pages


def _ocr_text(body: bytes) -> str:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return body.decode("utf-8", "replace")
    return "\n".join(_clean("".join(p.itertext())) for p in root.iter() if _local(p.tag) == "p")


# --------------------------------------------------------------------------- PDF (page numbers)

_PDF_TOKENS = re.compile(rb"\((?:\\.|[^\\)])*\)|\[|\]|-?\d*\.?\d+|T\*|TJ|Tj|TD|Td|'|\"|ET",
                         re.S)
_PDF_ESC = {ord("n"): b"\n", ord("r"): b"", ord("t"): b" ", ord("b"): b"", ord("f"): b""}


def _pdf_unescape(raw: bytes) -> str:
    out = bytearray()
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == 0x5C and i + 1 < len(raw):
            n = raw[i + 1]
            if 48 <= n <= 55:
                j = i + 1
                while j < len(raw) and j < i + 4 and 48 <= raw[j] <= 55:
                    j += 1
                out.append(int(raw[i + 1:j], 8) & 0xFF)
                i = j
                continue
            out += _PDF_ESC.get(n, bytes([n]))
            i += 2
            continue
        out.append(c)
        i += 1
    return out.decode("cp1252", "replace")


def _pdf_stream_text(stream: bytes) -> str:
    parts = []
    in_array = False
    for m in _PDF_TOKENS.finditer(stream):
        tok = m.group()
        if tok.startswith(b"("):
            parts.append(_pdf_unescape(tok[1:-1]))
        elif tok == b"[":
            in_array = True
        elif tok == b"]":
            in_array = False
        elif in_array and tok[:1] in b"-0123456789.":
            try:
                if float(tok) < -200:
                    parts.append(" ")
            except ValueError:
                pass
        elif tok in (b"T*", b"TD", b"Td", b"'", b'"', b"ET"):
            parts.append("\n")
    return "".join(parts)


_FOOTER = re.compile(r"nr\.\s*([0-9A-Z]+(?:-n\d+)?)\s+(\d{1,4})\s*$")


def pdf_pages(pdf_bytes: bytes, ondernummer: str | None = None) -> list:
    """Best-effort text per page of an officielebekendmakingen Kamerstuk PDF.

    Uses only zlib: decompresses content streams and reads (literal) text strings.
    The printed page number is taken from the footer line
    "Tweede Kamer, vergaderjaar 2013–2014, 33 818, nr. 3 12". Returns
    [(pagina or None, tekst)] in stream order. Returns [] when the PDF uses
    encodings this simple reader cannot decode (then cite without page).
    """
    pages = []
    for raw in re.findall(rb"stream\r?\n(.*?)\r?\nendstream", pdf_bytes, re.S):
        try:
            data = zlib.decompress(raw)
        except zlib.error:
            continue
        if b"Tj" not in data and b"TJ" not in data:
            continue
        text = _pdf_stream_text(data)
        if not text.strip():
            continue
        page = None
        tail = [ln.strip() for ln in text.splitlines() if ln.strip()][-3:]
        for ln in reversed(tail):
            m = _FOOTER.search(ln)
            if m and (ondernummer is None or m.group(1) == str(ondernummer)):
                page = int(m.group(2))
                break
        pages.append((page, text))
    return pages


# --------------------------------------------------------------------------- citations

def vergaderjaar_kort(vj: str) -> str:
    """'2013-2014' -> '2013/14'."""
    m = re.match(r"\s*(\d{4})\s*[-/–]\s*(\d{2,4})", vj or "")
    if not m:
        return vj or ""
    return f"{m.group(1)}/{m.group(2)[-2:]}"


def _kamer(record: Record) -> str:
    creator = (record.creator or "").lower()
    ident = record.identifier.lower()
    desc = " ".join(record.descriptions).lower()
    if "eerste kamer" in creator or "-ek-" in ident or "eerste kamer" in desc:
        return "I"
    if "tweede kamer" in creator or "-tk-" in ident or "tweede kamer" in desc:
        return "II"
    if "verenigde vergadering" in creator or "verenigde vergadering" in desc:
        return "VV"
    return "II"


def kamerstuk_citation(record: Record, pagina: int | str | None = None) -> str:
    """Dutch citation in Kamerstukken style.

    Kamerstuk:  Kamerstukken II 2013/14, 33818, nr. 3, p. 12
    Handeling:  Handelingen II 2013/14, nr. 55, item 18
    SGD stuk:   Kamerstukken II 1985/86, 17541, nr. 11, p. 3
    """
    p = f", p. {pagina}" if pagina not in (None, "") else ""
    vj = vergaderjaar_kort(record.get("vergaderjaar"))
    kamer = _kamer(record)
    typ = (record.type or "").lower()
    pubnaam = record.get("publicatienaam").lower()
    if pubnaam.startswith("handeling") or typ.startswith("handeling"):
        nr = record.get("publicatienummer")
        item = record.get("handelingenitemnummer")
        cite = f"Handelingen {kamer} {vj}".strip()
        if nr:
            cite += f", nr. {nr}"
        if item:
            cite += f", item {item}"
        return cite + p
    dossier = record.get("dossiernummer")
    onder = record.get("ondernummer")
    if not dossier:
        m = re.match(r"kst-(\d+)(?:-([A-Z]+|[IVX]+))?-(\w+(?:-n\d+)?)$", record.identifier)
        if m:
            dossier = m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")
            onder = onder or m.group(3)
    if dossier:
        cite = f"Kamerstukken {kamer} {vj}, {dossier}"
        if onder:
            cite += f", nr. {onder}"
            if re.search(r"-n\d+$", record.identifier):
                cite += " (herdruk)"
        return cite + p
    return f"{record.identifier}{p}"
