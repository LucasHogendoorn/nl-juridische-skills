"""Client for EU documents via the EU Publications Office (stdlib only).

Endpoints (official, content-negotiated):
    GET https://publications.europa.eu/resource/celex/<CELEX>
    GET https://publications.europa.eu/resource/ecli/<ECLI:EU:...>
with ``Accept: text/html, application/xhtml+xml`` and ``Accept-Language: <nld|eng|fra|deu>``.
The server redirects to the Cellar manifestation (XHTML) of the requested language.

Public interface (stable for other skills):
    normalize_id(text) -> (kind, value)        kind = "celex" | "ecli"
    zaak_naar_celex(zaaknummer, soort="arrest") -> str   e.g. "C-131/12" -> "62012CJ0131"
    fetch_html(identifier, taal="nld") -> dict {html, taal, url, bron_url}
    html_to_markdown(html) -> str
    fetch_markdown(identifier, taal="nld", meta_only=False) -> str
Errors: CelexError (bad input / not found), nl_http.FetchError (network).
"""
from __future__ import annotations

import datetime as _dt
import re
import urllib.parse
from html.parser import HTMLParser

import nl_http

BASE = "https://publications.europa.eu/resource"
TALEN = ("nld", "eng", "fra", "deu")

CELEX_RE = re.compile(r"^(?:[0-9CE][0-9]{4}[A-Z]{1,2}[0-9]{1,4}(?:\([0-9]{1,2}\))?(?:-[0-9]{8})?|[0-9]{5}[A-Z]{1,2}/TXT)$")
ECLI_EU_RE = re.compile(r"^ECLI:EU:[CTF]:\d{4}:\d+$")
ZAAK_RE = re.compile(r"^(?P<court>[CTF])\s*[-‑–]\s*(?P<nr>\d{1,4})\s*/\s*(?P<yy>\d{2}|\d{4})(?:\s*P)?$", re.IGNORECASE)

_SOORT_CODES = {"arrest": "J", "conclusie": "C", "beschikking": "O"}
_COURT_CODES = {"C": "C", "T": "T", "F": "F"}


class CelexError(Exception):
    """Invalid identifier or document not available (Dutch message)."""


def normalize_id(text: str) -> tuple[str, str]:
    value = re.sub(r"\s+", "", text or "")
    if value.upper().startswith("ECLI:"):
        value = value.upper()
        if not ECLI_EU_RE.match(value):
            if value.startswith("ECLI:NL:"):
                raise CelexError(f"{value} is een Nederlandse ECLI; gebruik fetch_ecli.py.")
            raise CelexError(f"Geen geldige Europese ECLI: {text!r} (verwacht bv. ECLI:EU:C:2014:317).")
        return "ecli", value
    value = value.upper()
    if CELEX_RE.match(value):
        return "celex", value
    if ZAAK_RE.match(value):
        return "celex", zaak_naar_celex(value)
    raise CelexError(
        f"Geen geldig CELEX-nummer, ECLI:EU of zaaknummer: {text!r}. Voorbeelden: 32016R0679 (AVG), "
        "62012CJ0131 (HvJ C-131/12), ECLI:EU:C:2014:317, C-131/12.")


def zaak_naar_celex(zaaknummer: str, soort: str = "arrest") -> str:
    """Map a case number (C-131/12, T-201/04) to a CELEX number.

    Sector 6 + year + court/document code + 4-digit number. ``soort``: arrest (J),
    conclusie (C, alleen HvJ), beschikking (O). The mapping is mechanical: always
    check the fetched title, because not every case has every document type.
    """
    m = ZAAK_RE.match((zaaknummer or "").strip())
    if not m:
        raise CelexError(f"Geen zaaknummer in de vorm C-131/12 of T-201/04: {zaaknummer!r}.")
    if soort not in _SOORT_CODES:
        raise CelexError("Soort moet 'arrest', 'conclusie' of 'beschikking' zijn.")
    yy = m.group("yy")
    if len(yy) == 2:
        year = int(yy)
        year += 1900 if year >= 50 else 2000
    else:
        year = int(yy)
    court = m.group("court").upper()
    return f"6{year}{court}{_SOORT_CODES[soort]}{int(m.group('nr')):04d}"


def _url(kind: str, value: str) -> str:
    return f"{BASE}/{kind}/{urllib.parse.quote(value, safe='')}"


def fetch_html(identifier: str, taal: str = "nld") -> dict:
    """Fetch the XHTML of a CELEX / ECLI:EU document in ``taal`` (falls back to other languages)."""
    kind, value = normalize_id(identifier)
    if taal not in TALEN:
        raise CelexError(f"Taal moet een van {', '.join(TALEN)} zijn.")
    url = _url(kind, value)
    order = [taal] + [t for t in TALEN if t != taal]
    problems = []
    for lang in order:
        try:
            resp = nl_http.get(url, accept="text/html, application/xhtml+xml;q=0.9",
                               headers={"Accept-Language": lang}, allow_status=(300, 406))
        except nl_http.FetchError as exc:
            if exc.kind == "niet_gevonden":
                problems.append(f"{lang}: niet gevonden")
                continue
            raise
        if resp.status == 300:
            sub = re.search(r'href="(https?://[^"]+)"', resp.text())
            if not sub:
                problems.append(f"{lang}: meerdere documenten, geen link gevonden")
                continue
            resp = nl_http.get(sub.group(1), accept="text/html, application/xhtml+xml;q=0.9",
                               headers={"Accept-Language": lang})
        if resp.status == 406:
            problems.append(f"{lang}: niet beschikbaar in deze taal")
            continue
        return {"html": resp.text(), "taal": lang, "url": url, "bron_url": resp.url,
                "id": value, "soort_id": kind}
    raise CelexError(f"{value} kon niet worden opgehaald bij publications.europa.eu ({'; '.join(problems)}). "
                     "Controleer het nummer; oudere documenten bestaan soms niet als HTML.")


# --------------------------------------------------------------------------- HTML -> markdown

_SKIP = {"script", "style", "noscript", "svg", "form", "nav", "header", "footer", "aside",
         "button", "iframe", "head", "title", "select", "option"}
_BLOCK = {"p", "div", "section", "article", "li", "blockquote", "dd", "dt"}
_HEAD = {"h1", "h2", "h3", "h4", "h5", "h6"}


class _Md(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0
        self.tables: list[list[list[str]]] = []   # stack of tables: rows of cells
        self.cell: list[str] | None = None
        self.cell_stack: list[list[str] | None] = []
        self.lists: list[list] = []

    # output helpers
    def _target(self) -> list[str]:
        return self.cell if self.cell is not None else self.out

    def _emit(self, s: str) -> None:
        self._target().append(s)

    def _block(self) -> None:
        t = self._target()
        if t and not "".join(t[-2:]).endswith("\n\n"):
            t.append("\n\n")

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "br":
            self._emit("\n")
        elif tag in _HEAD:
            self._block()
            self._emit("#" * int(tag[1]) + " ")
        elif tag in ("b", "strong"):
            self._emit("**")
        elif tag in ("i", "em"):
            self._emit("*")
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
            self._block()
        elif tag == "li":
            self._block()
            if self.lists:
                self.lists[-1][1] += 1
                kind, n = self.lists[-1]
                self._emit("  " * (len(self.lists) - 1) + (f"{n}. " if kind == "ol" else "- "))
        elif tag == "table":
            self.tables.append([])
            self.cell_stack.append(self.cell)
            self.cell = None
        elif tag == "tr" and self.tables:
            self.tables[-1].append([])
        elif tag in ("td", "th") and self.tables:
            self.cell = []
        elif tag in _BLOCK:
            self._block()

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in _HEAD:
            self._emit("\n\n")
        elif tag in ("b", "strong"):
            self._emit("**")
        elif tag in ("i", "em"):
            self._emit("*")
        elif tag in ("ul", "ol") and self.lists:
            self.lists.pop()
            self._block()
        elif tag in ("td", "th") and self.tables and self.cell is not None:
            text = re.sub(r"[ \t]+", " ", "".join(self.cell))
            text = re.sub(r"\s*\n\s*\n\s*", "\n\n", text).strip()
            if self.tables[-1]:
                self.tables[-1][-1].append(text)
            self.cell = None
        elif tag == "table" and self.tables:
            rows = self.tables.pop()
            self.cell = self.cell_stack.pop() if self.cell_stack else None
            self._flush_table(rows)
        elif tag in _BLOCK:
            self._block()

    def handle_data(self, data):
        if self.skip:
            return
        text = re.sub(r"[ \t\r\n ]+", " ", data)
        t = self._target()
        if not text.strip() and (not t or t[-1].endswith("\n")):
            return
        self._emit(text)

    def _flush_table(self, rows: list[list[str]]) -> None:
        rows = [r for r in rows if any(c.strip() for c in r)]
        if not rows:
            return
        self._block()
        # EUR-Lex lays out numbered points / list items as 1-row, 2-column tables.
        if len(rows) == 1 and len(rows[0]) == 2 and len(rows[0][0]) <= 12 and "\n" not in rows[0][0]:
            marker, text = rows[0][0].strip("*").strip(), rows[0][1]
            if marker in ("—", "–", "-", "•"):
                self._emit(f"{marker} {text}")
            elif marker:
                self._emit(f"**{marker}** {text}")
            else:
                self._emit(text)
            self._block()
            return
        if all(sum(1 for c in r if c) <= 1 for r in rows):
            for r in rows:
                self._emit(" ".join(c for c in r if c))
                self._block()
            return
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        def cell(c: str) -> str:
            return re.sub(r"\s+", " ", c).replace("|", "\\|")
        lines = ["| " + " | ".join(cell(c) for c in rows[0]) + " |", "|" + "---|" * width]
        lines += ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows[1:]]
        self._emit("\n".join(lines))
        self._block()

    def markdown(self) -> str:
        text = "".join(self.out)
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\*\*\s*\*\*", "", text)
        return text.strip() + "\n"


def html_to_markdown(html: str) -> str:
    parser = _Md()
    parser.feed(html)
    parser.close()
    return parser.markdown()


def extract_title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def fetch_markdown(identifier: str, taal: str = "nld", meta_only: bool = False) -> str:
    doc = fetch_html(identifier, taal)
    body = "" if meta_only else html_to_markdown(doc["html"])
    if not meta_only and not body.strip():
        raise CelexError(f"Geen tekst gevonden in het document {doc['id']} (HTML-structuur onbekend).")
    title = extract_title(doc["html"])
    if not title or title.upper() == doc["id"] or title.lower().endswith((".xml", ".html")):
        # <title> often holds only the CELEX number or a file name; use the first text line instead
        title = next((ln.strip("# *") for ln in html_to_markdown(doc["html"]).splitlines()
                      if len(ln.strip("# *")) > 3 and not ln.startswith("|")), "")
    head = [
        f"# {doc['id']}",
        "",
        f"- **Titel/kop:** {title or '-'}",
        f"- **Taal:** {doc['taal']}" + ("" if doc["taal"] == taal else f" (gevraagd: {taal}, niet beschikbaar)"),
        f"- **Bron:** {doc['url']}",
        f"- **EUR-Lex:** https://eur-lex.europa.eu/legal-content/NL/TXT/?uri="
        + (f"CELEX:{doc['id']}" if doc["soort_id"] == "celex" else f"ecli:{doc['id']}"),
        f"- **Opgehaald:** {_dt.date.today().isoformat()}",
        "",
        "---",
        "",
    ]
    return "\n".join(head) + (body if not meta_only else "_(alleen metadata; tekst niet opgehaald)_\n")
