"""Client for the official Open Data API of de Rechtspraak (data.rechtspraak.nl).

Only the documented open-data endpoints are used:
    GET https://data.rechtspraak.nl/uitspraken/content?id=<ECLI>[&return=META]
    GET https://data.rechtspraak.nl/uitspraken/zoeken?<filters>

The search endpoint filters on metadata only (instantie, datum, rechtsgebied,
type, wijzigingsdatum, LJN). It has no free-text parameter; unknown parameters
are silently ignored by the server. ``zoek(..., trefwoorden=[...])`` therefore
filters *locally* on the title and summary (a shortened inhoudsindicatie) of
the entries the server returned. See test-reports/api-capabilities.md.

Public interface (stable for other skills):
    normalize_ecli(text) -> str
    fetch_ecli_xml(ecli, meta_only=False) -> bytes
    parse_uitspraak(xml_bytes) -> dict
    render_uitspraak(parsed, meta_only=False) -> str          (markdown)
    fetch_ecli(ecli, meta_only=False) -> dict                  (parsed)
    fetch_ecli_markdown(ecli, meta_only=False) -> str
    build_search_url(**filters) -> str
    parse_search(xml_bytes) -> dict
    zoek(**filters, trefwoorden=None) -> dict
    render_search(result) -> str                               (markdown)
    INSTANTIES, RECHTSGEBIEDEN                                 (code -> URI)
Errors: RechtspraakError (bad input / not found / parse), nl_http.FetchError (network).
"""
from __future__ import annotations

import datetime as _dt
import re
import urllib.parse
from xml.etree import ElementTree as ET

import nl_http

BASE = "https://data.rechtspraak.nl/uitspraken"
CONTENT_URL = f"{BASE}/content"
SEARCH_URL = f"{BASE}/zoeken"
DEEPLINK = "https://uitspraken.rechtspraak.nl/details?id="

ECLI_RE = re.compile(r"^ECLI:[A-Z]{2}:[A-Z0-9]{1,7}:\d{4}:[A-Z0-9.]{1,25}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?$")

_OWMS = "http://standaarden.overheid.nl/owms/terms/"
# Current courts (from data.rechtspraak.nl/Waardelijst/Instanties, checked 2026-09-23).
INSTANTIES = {
    "HR": _OWMS + "Hoge_Raad_der_Nederlanden",
    "PHR": _OWMS + "Parket_bij_de_Hoge_Raad",
    "RVS": _OWMS + "Raad_van_State",
    "CRVB": _OWMS + "Centrale_Raad_van_Beroep",
    "CBB": _OWMS + "College_van_Beroep_voor_het_bedrijfsleven",
    "GHAMS": _OWMS + "Gerechtshof_Amsterdam",
    "GHARL": _OWMS + "Gerechtshof_Arnhem-Leeuwarden",
    "GHDHA": _OWMS + "Gerechtshof_Den_Haag",
    "GHSHE": _OWMS + "Gerechtshof_'s-Hertogenbosch",
    "RBAMS": _OWMS + "Rechtbank_Amsterdam",
    "RBDHA": _OWMS + "Rechtbank_Den_Haag",
    "RBGEL": _OWMS + "Rechtbank_Gelderland",
    "RBLIM": _OWMS + "Rechtbank_Limburg",
    "RBMNE": _OWMS + "Rechtbank_Midden-Nederland",
    "RBNHO": _OWMS + "Rechtbank_Noord-Holland",
    "RBNNE": _OWMS + "Rechtbank_Noord-Nederland",
    "RBOBR": _OWMS + "Rechtbank_Oost-Brabant",
    "RBOVE": _OWMS + "Rechtbank_Overijssel",
    "RBROT": _OWMS + "Rechtbank_Rotterdam",
    "RBZWB": _OWMS + "Rechtbank_Zeeland-West-Brabant",
}

_RG = "http://psi.rechtspraak.nl/rechtsgebied#"
# From data.rechtspraak.nl/Waardelijst/Rechtsgebieden (checked 2026-09-23).
RECHTSGEBIEDEN = {
    "bestuursrecht": _RG + "bestuursrecht",
    "ambtenarenrecht": _RG + "bestuursrecht_ambtenarenrecht",
    "belastingrecht": _RG + "bestuursrecht_belastingrecht",
    "bestuursprocesrecht": _RG + "bestuursrecht_bestuursprocesrecht",
    "bestuursstrafrecht": _RG + "bestuursrecht_bestuursstrafrecht",
    "europees-bestuursrecht": _RG + "bestuursrecht_europeesBestuursrecht",
    "mededingingsrecht-bestuur": _RG + "bestuursrecht_mededingingsrecht",
    "omgevingsrecht": _RG + "bestuursrecht_omgevingsrecht",
    "socialezekerheidsrecht": _RG + "bestuursrecht_socialezekerheidsrecht",
    "vreemdelingenrecht": _RG + "bestuursrecht_vreemdelingenrecht",
    "civiel": _RG + "civielRecht",
    "aanbestedingsrecht": _RG + "civielRecht_aanbestedingsrecht",
    "arbeidsrecht": _RG + "civielRecht_arbeidsrecht",
    "burgerlijk-procesrecht": _RG + "civielRecht_burgerlijkProcesrecht",
    "europees-civiel-recht": _RG + "civielRecht_europeesCivielRecht",
    "goederenrecht": _RG + "civielRecht_goederenrecht",
    "insolventierecht": _RG + "civielRecht_insolventierecht",
    "intellectueel-eigendomsrecht": _RG + "civielRecht_intellectueeleigendomsrecht",
    "ipr": _RG + "civielRecht_internationaalPrivaatrecht",
    "mededingingsrecht": _RG + "civielRecht_mededingingsrecht",
    "ondernemingsrecht": _RG + "civielRecht_ondernemingsrecht",
    "personen-en-familierecht": _RG + "civielRecht_personenEnFamilierecht",
    "verbintenissenrecht": _RG + "civielRecht_verbintenissenrecht",
    "strafrecht": _RG + "strafrecht",
    "europees-strafrecht": _RG + "strafrecht_europeesStrafrecht",
    "internationaal-strafrecht": _RG + "strafrecht_internationaalStrafrecht",
    "materieel-strafrecht": _RG + "strafrecht_materieelStrafrecht",
    "penitentiair-strafrecht": _RG + "strafrecht_penitentiairStrafrecht",
    "strafprocesrecht": _RG + "strafrecht_strafprocesrecht",
    "internationaal-publiekrecht": _RG + "internationaalPubliekrecht",
    "mensenrechten": _RG + "internationaalPubliekrecht_mensenrechten",
    "volkenrecht": _RG + "internationaalPubliekrecht_volkenrecht",
}
_RG_ALIASES = {"civiel-recht": "civiel", "civielrecht": "civiel", "straf": "strafrecht",
               "bestuur": "bestuursrecht", "belasting": "belastingrecht", "ie": "intellectueel-eigendomsrecht",
               "familierecht": "personen-en-familierecht", "procesrecht": "burgerlijk-procesrecht"}

NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#"
NS_ECLI = "https://e-justice.europa.eu/ecli"
NS_PSI = "http://psi.rechtspraak.nl/"


class RechtspraakError(Exception):
    """Invalid input, unknown ECLI or unparseable response (Dutch message)."""


# --------------------------------------------------------------------------- input

def normalize_ecli(text: str) -> str:
    """Uppercase/trim an ECLI and validate its shape. Raises RechtspraakError."""
    ecli = re.sub(r"\s+", "", (text or "")).upper()
    if not ECLI_RE.match(ecli):
        raise RechtspraakError(
            f"Geen geldige ECLI: {text!r}. Verwacht bijvoorbeeld ECLI:NL:HR:2025:667.")
    return ecli


def resolve_instantie(value: str) -> str:
    if value.startswith("http://") or value.startswith("https://"):
        return value
    key = value.strip().upper()
    if key not in INSTANTIES:
        raise RechtspraakError(
            f"Onbekende instantie {value!r}. Gebruik een ECLI-code ({', '.join(sorted(INSTANTIES))}) "
            "of de volledige URI uit data.rechtspraak.nl/Waardelijst/Instanties.")
    return INSTANTIES[key]


def resolve_rechtsgebied(value: str) -> str:
    if value.startswith("http://") or value.startswith("https://"):
        return value
    key = value.strip().lower().replace(" ", "-").replace("_", "-")
    key = _RG_ALIASES.get(key, key)
    if key not in RECHTSGEBIEDEN:
        raise RechtspraakError(
            f"Onbekend rechtsgebied {value!r}. Kies uit: {', '.join(sorted(RECHTSGEBIEDEN))} "
            "(of geef de volledige URI).")
    return RECHTSGEBIEDEN[key]


# --------------------------------------------------------------------------- fetch

def fetch_ecli_xml(ecli: str, meta_only: bool = False) -> bytes:
    ecli = normalize_ecli(ecli)
    if ecli.startswith("ECLI:EU:"):
        raise RechtspraakError(f"{ecli} is een Europese ECLI; gebruik celex_client / fetch_celex.py.")
    if not ecli.startswith("ECLI:NL:"):
        raise RechtspraakError(f"{ecli} is geen Nederlandse ECLI; data.rechtspraak.nl kent alleen ECLI:NL.")
    params = {"id": ecli}
    if meta_only:
        params["return"] = "META"
    url = f"{CONTENT_URL}?{urllib.parse.urlencode(params)}"
    try:
        return nl_http.get(url, accept="application/xml").body
    except nl_http.FetchError as exc:
        if exc.kind == "niet_gevonden":
            raise RechtspraakError(
                f"{ecli} niet gevonden bij data.rechtspraak.nl (HTTP 404). Controleer de ECLI; "
                "niet elke uitspraak is gepubliceerd.") from None
        raise


def fetch_ecli(ecli: str, meta_only: bool = False) -> dict:
    return parse_uitspraak(fetch_ecli_xml(ecli, meta_only=meta_only))


def fetch_ecli_markdown(ecli: str, meta_only: bool = False) -> str:
    return render_uitspraak(fetch_ecli(ecli, meta_only=meta_only), meta_only=meta_only)


# --------------------------------------------------------------------------- content parsing

def _local(tag) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _parse_xml(xml_bytes: bytes):
    try:
        return ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise RechtspraakError(f"Antwoord van data.rechtspraak.nl is geen geldige XML ({exc}).") from None


def _meta_value(el) -> str:
    return _clean("".join(el.itertext()))


def parse_uitspraak(xml_bytes: bytes) -> dict:
    root = _parse_xml(xml_bytes)
    if _local(root.tag) != "open-rechtspraak":
        raise RechtspraakError(f"Onverwacht antwoord: root-element <{_local(root.tag)}>.")
    meta = {
        "ecli": "", "titel": "", "instantie": "", "datum": "", "publicatiedatum": "",
        "gewijzigd": "", "type": "", "procedure": [], "zaaknummers": [], "rechtsgebieden": [],
        "vindplaatsen": [], "relaties": [], "wetsverwijzingen": [], "vervangt": [],
    }
    rdf = next((c for c in root if _local(c.tag) == "RDF"), None)
    descriptions = [d for d in rdf if _local(d.tag) == "Description"] if rdf is not None else []
    abstract = ""
    for index, desc in enumerate(descriptions):
        for el in desc:
            name = _local(el.tag)
            value = _meta_value(el)
            if index == 0:
                _collect_primary(meta, name, el, value)
            elif name == "title" and value and not meta["titel"]:
                meta["titel"] = value
            elif name == "abstract" and value:
                abstract = value  # with return=META the inhoudsindicatie is only here
    inhoud, body, body_type = "", "", None
    footnotes: list[tuple[str, str]] = []
    for child in root:
        name = _local(child.tag)
        if name == "inhoudsindicatie":
            inhoud = _Renderer().render_plain(child)
        elif name in ("uitspraak", "conclusie"):
            body_type = name
            renderer = _Renderer()
            body = renderer.render(child)
            footnotes = renderer.footnotes
    meta.update({
        "inhoudsindicatie": inhoud or abstract,
        "tekst": body,
        "tekst_type": body_type,
        "voetnoten": footnotes,
        "link": DEEPLINK + meta["ecli"] if meta["ecli"] else "",
    })
    return meta


def _collect_primary(meta: dict, name: str, el, value: str) -> None:
    if name == "identifier" and not meta["ecli"]:
        meta["ecli"] = value
    elif name == "creator" and value:
        meta["instantie"] = value
    elif name == "date":
        meta["datum"] = value
    elif name == "issued":
        meta["publicatiedatum"] = value
    elif name == "modified":
        meta["gewijzigd"] = value
    elif name == "type":
        meta["type"] = value
    elif name == "procedure" and value:
        meta["procedure"].append(value)
    elif name == "zaaknummer" and value:
        meta["zaaknummers"].append(value)
    elif name == "subject" and value:
        meta["rechtsgebieden"].append(value)
    elif name == "replaces" and value:
        meta["vervangt"].append(value)
    elif name == "hasVersion":
        meta["vindplaatsen"].extend(_clean("".join(li.itertext())) for li in el.iter()
                                    if _local(li.tag) == "li" and _clean("".join(li.itertext())))
    elif name == "relation":
        meta["relaties"].append({
            "ecli": el.get(f"{{{NS_ECLI}}}resourceIdentifier", ""),
            "type": (el.get(f"{{{NS_PSI}}}type") or el.get(f"{{{NS_PSI}}}typeRelatie") or "").rsplit("/", 1)[-1],
            "aanleg": (el.get(f"{{{NS_PSI}}}aanleg") or "").rsplit("/", 1)[-1],
            "gevolg": (el.get(f"{{{NS_PSI}}}gevolg") or "").rsplit("#", 1)[-1].rsplit("/", 1)[-1],
            "omschrijving": value,
        })
    elif name == "references":
        label = value or el.get(f"{{{NS_RDFS}}}label", "")
        if label:
            meta["wetsverwijzingen"].append(label)


class _Renderer:
    """Render the DocBook-like <uitspraak>/<conclusie> body as markdown.

    Paragraph numbers (<paragroup><nr>3.2</nr>...) and section numbers are kept,
    so r.o.-references stay findable ("**3.2** ...").
    """

    def __init__(self) -> None:
        self.blocks: list[str] = []
        self.pending_nr: str | None = None
        self.footnotes: list[tuple[str, str]] = []
        self.footnote_labels: dict[str, str] = {}

    # -- public
    def render(self, el) -> str:
        for fn in el.iter():
            if _local(fn.tag) == "footnote":
                self.footnote_labels[fn.get("id", "")] = fn.get("label") or str(len(self.footnote_labels) + 1)
        self._walk(el, 0)
        self._flush_nr()
        return "\n\n".join(b for b in self.blocks if b.strip())

    def render_plain(self, el) -> str:
        self._walk(el, 0)
        return "\n\n".join(b for b in self.blocks if b.strip())

    # -- helpers
    def _emit(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        if self.pending_nr:
            text = f"**{self.pending_nr}** {text}"
            self.pending_nr = None
        self.blocks.append(text)

    def _flush_nr(self) -> None:
        if self.pending_nr:
            self.blocks.append(f"**{self.pending_nr}**")
            self.pending_nr = None

    def _inline(self, el) -> str:
        parts = [el.text or ""]
        for c in el:
            name = _local(c.tag)
            if name == "footnote-ref":
                ref = c.get("linkend") or c.get("idref") or ""
                parts.append(f"[^{self.footnote_labels.get(ref, '?')}]")
            elif name == "emphasis":
                inner = _clean(self._inline(c))
                role = c.get("role", "")
                if inner and role == "bold":
                    parts.append(f"**{inner}**")
                elif inner and role == "italic":
                    parts.append(f"*{inner}*")
                else:
                    parts.append(inner)
            elif name == "footnote":
                pass
            elif name == "nr":
                parts.append(_clean(self._inline(c)) + " ")
            elif name == "br":
                parts.append(" ")
            else:
                parts.append(self._inline(c))
            parts.append(c.tail or "")
        return re.sub(r"[ \t\r\n ]+", " ", "".join(parts))

    def _walk(self, el, depth: int) -> None:
        name = _local(el.tag)
        if name == "footnote":
            label = self.footnote_labels.get(el.get("id", ""), el.get("label", "?"))
            self.footnotes.append((label, _clean(" ".join(self._inline(p) for p in el))))
            return
        if name == "section":
            self._flush_nr()
            for c in el:
                if _local(c.tag) == "title":
                    title = _clean(self._inline(c))
                    if title:
                        self.blocks.append(f"{'#' * min(depth + 3, 6)} {title}")
                else:
                    self._walk(c, depth + 1)
            return
        if name == "title":
            title = _clean(self._inline(el))
            if title:
                self._flush_nr()
                self.blocks.append(f"{'#' * min(depth + 3, 6)} {title}")
            return
        if name == "paragroup":
            self._flush_nr()
            for c in el:
                if _local(c.tag) == "nr" and self.pending_nr is None:
                    self.pending_nr = _clean(self._inline(c))
                else:
                    self._walk(c, depth)
            self._flush_nr()
            return
        if name in ("para", "bridgehead"):
            text = _clean(self._inline(el))
            if name == "bridgehead" and text:
                text = f"**{text}**"
            self._emit(text)
            return
        if name in ("listitem", "item"):
            text = _clean(" ".join(self._inline(c) for c in el) or self._inline(el))
            self._emit(f"- {text}")
            return
        if name in ("table", "informaltable"):
            self._emit(self._table(el))
            return
        if name in ("mediaobject", "imageobject", "inlinemediaobject"):
            self._emit("[afbeelding]")
            return
        if name == "nr":
            self.pending_nr = _clean(self._inline(el))
            return
        # Container: recurse; keep stray direct text.
        if el.text and el.text.strip() and name not in ("uitspraak", "conclusie", "inhoudsindicatie"):
            self._emit(_clean(el.text))
        for c in el:
            self._walk(c, depth)

    def _table(self, el) -> str:
        rows = []
        for row in el.iter():
            if _local(row.tag) == "row":
                cells = [_clean(self._inline(cell)).replace("|", "\\|") for cell in row
                         if _local(cell.tag) in ("entry", "cell")]
                if any(cells):
                    rows.append(cells)
        if not rows:
            return ""
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
        lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return "\n".join(lines)


def render_uitspraak(parsed: dict, meta_only: bool = False) -> str:
    p = parsed
    lines = [f"# {p.get('ecli') or '(onbekende ECLI)'}"]
    if p.get("titel"):
        lines.append(f"*{p['titel']}*")
    lines += ["", "## Metadata"]

    def add(label: str, value) -> None:
        if isinstance(value, list):
            value = "; ".join(v for v in value if v)
        if value:
            lines.append(f"- **{label}:** {value}")

    add("Instantie", p.get("instantie"))
    add("Datum uitspraak", p.get("datum"))
    add("Datum publicatie", p.get("publicatiedatum"))
    add("Type", p.get("type"))
    add("Zaaknummer", p.get("zaaknummers"))
    add("Procedure", p.get("procedure"))
    add("Rechtsgebied", p.get("rechtsgebieden"))
    add("Vindplaatsen", p.get("vindplaatsen"))
    add("Vervangt (LJN)", p.get("vervangt"))
    add("Bron", p.get("link"))
    if p.get("relaties"):
        lines += ["", "## Formele relaties"]
        for r in p["relaties"]:
            extra = ", ".join(x for x in (r.get("aanleg"), f"gevolg: {r['gevolg']}" if r.get("gevolg") else "") if x)
            label = r.get("omschrijving") or r.get("ecli") or ""
            lines.append(f"- {label}" + (f" ({extra})" if extra else ""))
    if p.get("wetsverwijzingen"):
        lines += ["", "## Wetsverwijzingen"]
        lines += [f"- {w}" for w in p["wetsverwijzingen"]]
    if p.get("inhoudsindicatie"):
        lines += ["", "## Inhoudsindicatie", p["inhoudsindicatie"]]
    if not meta_only:
        if p.get("tekst"):
            lines += ["", f"## {(p.get('tekst_type') or 'uitspraak').capitalize()}", "", p["tekst"]]
            if p.get("voetnoten"):
                lines += ["", "## Voetnoten"]
                lines += [f"[^{label}]: {text}" for label, text in p["voetnoten"]]
        else:
            lines += ["", "_De volledige tekst van deze uitspraak is niet gepubliceerd in de open data "
                          "(alleen metadata beschikbaar)._"]
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------- search

def _check_date(value: str, label: str, allow_time: bool = False) -> str:
    rx = DATETIME_RE if allow_time else DATE_RE
    if not rx.match(value or ""):
        fmt = "JJJJ-MM-DD of JJJJ-MM-DDTUU:MM:SS" if allow_time else "JJJJ-MM-DD"
        raise RechtspraakError(f"{label} {value!r} heeft niet het formaat {fmt}.")
    try:
        _dt.date.fromisoformat(value[:10])
    except ValueError:
        raise RechtspraakError(f"{label} {value!r} is geen bestaande datum.") from None
    return value


def build_search_url(instanties=None, datum_van: str | None = None, datum_tot: str | None = None,
                     rechtsgebieden=None, soort: str | None = None, alleen_met_tekst: bool = False,
                     max_resultaten: int = 50, offset: int | None = None, sorteer: str | None = None,
                     gewijzigd_van: str | None = None, gewijzigd_tot: str | None = None,
                     ljn: str | None = None) -> str:
    """Build a /uitspraken/zoeken URL. Same-kind filters are OR'ed, different kinds AND'ed."""
    qs: list[tuple[str, str]] = []
    for inst in instanties or []:
        qs.append(("creator", resolve_instantie(inst)))
    if soort:
        s = soort.strip().lower()
        if s not in ("uitspraak", "conclusie"):
            raise RechtspraakError("Soort moet 'uitspraak' of 'conclusie' zijn.")
        qs.append(("type", s.capitalize()))
    if datum_van or datum_tot:
        van = _check_date(datum_van, "Datum-van") if datum_van else "1900-01-01"
        tot = _check_date(datum_tot, "Datum-tot") if datum_tot else _dt.date.today().isoformat()
        if van > tot:
            raise RechtspraakError(f"Datum-van {van} ligt na datum-tot {tot}.")
        qs += [("date", van), ("date", tot)]
    for mod, label in ((gewijzigd_van, "Gewijzigd-van"), (gewijzigd_tot, "Gewijzigd-tot")):
        if mod:
            qs.append(("modified", _check_date(mod, label, allow_time=True)))
    for rg in rechtsgebieden or []:
        qs.append(("subject", resolve_rechtsgebied(rg)))
    if ljn:
        qs.append(("replaces", ljn.strip().upper()))
    if alleen_met_tekst:
        qs.append(("return", "DOC"))
    if not 1 <= int(max_resultaten) <= 1000:
        raise RechtspraakError("max_resultaten moet tussen 1 en 1000 liggen.")
    qs.append(("max", str(int(max_resultaten))))
    if offset:
        qs.append(("from", str(int(offset))))
    if sorteer:
        s = sorteer.strip().upper()
        if s not in ("ASC", "DESC"):
            raise RechtspraakError("Sorteer moet ASC of DESC zijn.")
        qs.append(("sort", s))
    return f"{SEARCH_URL}?{urllib.parse.urlencode(qs)}"


_TITLE_RE = re.compile(r"^(?P<ecli>ECLI:[^,]+),\s*(?P<inst>.*?),\s*(?P<d>\d{2})-(?P<m>\d{2})-(?P<y>\d{4})(?:,\s*(?P<zaak>.*))?$")


def parse_search(xml_bytes: bytes) -> dict:
    root = _parse_xml(xml_bytes)
    atom = "{http://www.w3.org/2005/Atom}"
    subtitle = root.findtext(f"{atom}subtitle", default="") or ""
    m = re.search(r"(\d+)", subtitle)
    total = int(m.group(1)) if m else 0
    entries = []
    for e in root.findall(f"{atom}entry"):
        title = _clean(e.findtext(f"{atom}title", default=""))
        summary = _clean(e.findtext(f"{atom}summary", default=""))
        link_el = e.find(f"{atom}link")
        item = {
            "ecli": _clean(e.findtext(f"{atom}id", default="")),
            "titel": title,
            "samenvatting": "" if summary == "-" else summary,
            "bijgewerkt": _clean(e.findtext(f"{atom}updated", default="")),
            "link": link_el.get("href", "") if link_el is not None else "",
            "verwijderd": e.get("deleted") or "",
            "instantie": "", "datum": "", "zaaknummer": "",
        }
        tm = _TITLE_RE.match(title)
        if tm:
            item.update(instantie=tm.group("inst"), datum=f"{tm.group('y')}-{tm.group('m')}-{tm.group('d')}",
                        zaaknummer=tm.group("zaak") or "")
        entries.append(item)
    return {"totaal": total, "resultaten": entries}


def filter_trefwoorden(resultaten: list[dict], trefwoorden: list[str]) -> list[dict]:
    """Keep entries whose title+summary contain *all* words (case-insensitive). Local filter."""
    words = [w.lower() for w in trefwoorden if w and w.strip()]
    out = []
    for r in resultaten:
        hay = f"{r.get('titel', '')} {r.get('samenvatting', '')}".lower()
        if all(w in hay for w in words):
            out.append(r)
    return out


def zoek(trefwoorden: list[str] | None = None, scan_max: int = 1000, **filters) -> dict:
    """Search the ECLI index. Returns {url, totaal, resultaten, lokaal_gefilterd, gescand}.

    ``totaal`` is the server's count for the metadata filters. With ``trefwoorden``
    the server is asked for up to ``scan_max`` entries, which are filtered locally;
    only the first ``max_resultaten`` matches are returned.
    """
    wanted = int(filters.get("max_resultaten", 50))
    if trefwoorden:
        filters["max_resultaten"] = scan_max
        if not filters.get("sorteer"):
            filters["sorteer"] = "DESC"  # scan most recently modified entries first
    url = build_search_url(**filters)
    parsed = parse_search(nl_http.get(url, accept="application/atom+xml").body)
    result = {"url": url, "totaal": parsed["totaal"], "resultaten": parsed["resultaten"],
              "lokaal_gefilterd": False, "gescand": len(parsed["resultaten"]), "trefwoorden": []}
    if trefwoorden:
        hits = filter_trefwoorden(parsed["resultaten"], trefwoorden)
        result.update(resultaten=hits[:wanted], lokaal_gefilterd=True, treffers_lokaal=len(hits),
                      trefwoorden=list(trefwoorden))
    return result


def render_search(result: dict) -> str:
    lines = [f"<!-- {result.get('url', '')} -->",
             "# Zoekresultaten Rechtspraak open data",
             "",
             f"- Aantal ECLI's dat aan de filters voldoet (server): {result.get('totaal', 0)}"]
    if result.get("lokaal_gefilterd"):
        lines.append(
            f"- Lokaal gefilterd op trefwoorden {', '.join(repr(w) for w in result['trefwoorden'])} "
            f"in titel + samenvatting van {result.get('gescand', 0)} opgehaalde items: "
            f"{result.get('treffers_lokaal', 0)} treffer(s). Dit is geen full-text zoekopdracht.")
        if result.get("gescand", 0) < result.get("totaal", 0):
            lines.append(f"- Let op: slechts {result.get('gescand', 0)} van {result.get('totaal', 0)} items doorzocht "
                         "(meest recent gewijzigde eerst). Verfijn de filters voor een volledige lokale filtering.")
    lines.append(f"- Getoond: {len(result.get('resultaten', []))}")
    lines.append("")
    if not result.get("resultaten"):
        lines.append("_Geen resultaten._")
        return "\n".join(lines) + "\n"
    lines += ["| ECLI | Datum | Instantie | Samenvatting |", "|---|---|---|---|"]
    for r in result["resultaten"]:
        summary = (r.get("samenvatting") or "").replace("|", "\\|")
        if len(summary) > 220:
            summary = summary[:217].rstrip() + "..."
        if r.get("verwijderd"):
            summary = f"(verwijderd: {r['verwijderd']}) {summary}"
        lines.append(f"| {r['ecli']} | {r.get('datum', '')} | {r.get('instantie', '')} | {summary} |")
    return "\n".join(lines) + "\n"
