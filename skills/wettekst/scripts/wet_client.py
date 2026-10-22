"""Client for Dutch statute text from the official BWB repository (stdlib only).

Source: the official "Basiswettenbestand" XML repository behind wetten.overheid.nl:
    https://repository.officiele-overheidspublicaties.nl/bwb/<BWB-id>/manifest.xml
    https://repository.officiele-overheidspublicaties.nl/bwb/<BWB-id>/<label>/xml/<BWB-id>_<label>.xml

The manifest lists every consolidated version ("toestand") with its
datum_inwerkingtreding and einddatum, so the version valid on a given date
(geldigheidsdatum) can be selected. The repository holds versions from roughly
2002 onward (earlier dates are refused with a clear message).
The per-law WTI file (``<BWB-id>/<BWB-id>.WTI``) gives the change history per
article since 1992 (datum, nieuw/wijziging/vervallen, dossiernummer, Stb/Stcrt).
Pages on wetten.overheid.nl are never fetched (its robots.txt disallows AI agents);
only links to it are produced, for humans to click.
Downloaded versions are cached (reused while the manifest entry is unchanged) in
``$NLJS_CACHE_DIR/bwb`` or ``~/.cache/nl-juridische-skills/bwb``.

Public interface (stable for other skills):
    parse_citation(text) -> Citation
    list_versies(bwb_id) -> list[Versie]            (oldest first)
    kies_versie(versies, datum=None) -> Versie      (datum 'JJJJ-MM-DD'; None = vandaag)
    load_toestand(bwb_id, datum=None) -> (xml_bytes, Versie)
    find_artikel(root, artikel_nr) -> Element | None
    parse_artikel(element) -> dict
    fetch_artikel(citation_or_text, datum=None, lid=None) -> dict
    render_artikel(result) -> str                   (markdown)
    wetten_url(bwb_id, artikel_nr, datum=None) -> str   (link for humans only)
    load_wti(bwb_id) -> bytes                       (wetstechnische informatie, cached)
    parse_wti_artikel(wti_bytes, artikel_nr) -> list[dict]
    wijzigingen_artikel(citation_or_text) -> dict   (change history per article)
    WETTEN, BW_BOEKEN                               (abbreviation tables)
Errors: WetError (bad input / not found), nl_http.FetchError (network).
"""
from __future__ import annotations

import datetime as _dt
import os
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

import nl_http

REPO = "https://repository.officiele-overheidspublicaties.nl/bwb"

# BW books: book -> (BWB-id, name). Verified against zoekservice.overheid.nl SRU on 2026-09-23.
BW_BOEKEN = {
    "1": ("BWBR0002656", "Burgerlijk Wetboek Boek 1"),
    "2": ("BWBR0003045", "Burgerlijk Wetboek Boek 2"),
    "3": ("BWBR0005291", "Burgerlijk Wetboek Boek 3"),
    "4": ("BWBR0002761", "Burgerlijk Wetboek Boek 4"),
    "5": ("BWBR0005288", "Burgerlijk Wetboek Boek 5"),
    "6": ("BWBR0005289", "Burgerlijk Wetboek Boek 6"),
    "7": ("BWBR0005290", "Burgerlijk Wetboek Boek 7"),
    "7A": ("BWBR0006000", "Burgerlijk Wetboek Boek 7A"),
    "8": ("BWBR0005034", "Burgerlijk Wetboek Boek 8"),
    "10": ("BWBR0030068", "Burgerlijk Wetboek Boek 10"),
}

# Other codes/laws: abbreviation (lowercase) -> (BWB-id, name). Same verification.
_WETTEN = [
    (("rv", "wetboek van burgerlijke rechtsvordering"), "BWBR0001827", "Wetboek van Burgerlijke Rechtsvordering"),
    (("sr", "wetboek van strafrecht"), "BWBR0001854", "Wetboek van Strafrecht"),
    (("sv", "wetboek van strafvordering"), "BWBR0001903", "Wetboek van Strafvordering"),
    (("awb", "algemene wet bestuursrecht"), "BWBR0005537", "Algemene wet bestuursrecht"),
    (("gw", "grondwet"), "BWBR0001840", "Grondwet"),
    (("uavg", "uitvoeringswet avg", "uitvoeringswet algemene verordening gegevensbescherming"),
     "BWBR0040940", "Uitvoeringswet Algemene verordening gegevensbescherming"),
    (("fw", "faillissementswet"), "BWBR0001860", "Faillissementswet"),
    (("k", "wvk", "wetboek van koophandel"), "BWBR0001838", "Wetboek van Koophandel"),
    (("ro", "wet ro", "wet op de rechterlijke organisatie"), "BWBR0001830", "Wet op de rechterlijke organisatie"),
    (("wor", "wet op de ondernemingsraden"), "BWBR0002747", "Wet op de ondernemingsraden"),
    (("wft", "wet op het financieel toezicht"), "BWBR0020368", "Wet op het financieel toezicht"),
    (("ow", "omgevingswet"), "BWBR0037885", "Omgevingswet"),
    (("wvw", "wvw 1994", "wegenverkeerswet", "wegenverkeerswet 1994"), "BWBR0006622", "Wegenverkeerswet 1994"),
    (("opiumwet",), "BWBR0001941", "Opiumwet"),
    (("vw", "vw 2000", "vreemdelingenwet", "vreemdelingenwet 2000"), "BWBR0011823", "Vreemdelingenwet 2000"),
    (("uhw", "uitvoeringswet huurprijzen woonruimte"), "BWBR0014315", "Uitvoeringswet huurprijzen woonruimte"),
    (("advocatenwet",), "BWBR0002093", "Advocatenwet"),
    (("wna", "wet op het notarisambt"), "BWBR0010388", "Wet op het notarisambt"),
    (("awr", "algemene wet inzake rijksbelastingen"), "BWBR0002320", "Algemene wet inzake rijksbelastingen"),
    (("wet ob", "wet ob 1968", "wet op de omzetbelasting 1968"), "BWBR0002629", "Wet op de omzetbelasting 1968"),
]
WETTEN = {alias: (bwb, naam) for aliases, bwb, naam in _WETTEN for alias in aliases}

BW_IDS = {bwb for bwb, _ in BW_BOEKEN.values()}

_ART = r"\d+[a-z]{0,4}(?:[:.]\d+[a-z]{0,4})*"
_LID_RE = re.compile(r"(?:,\s*)?\blid\s+(\d+[a-z]?)\b\s*,?", re.IGNORECASE)
_SUB_RE = re.compile(r"(?:,\s*)?\b(?:sub|onder|onderdeel)\s+([a-z0-9]{1,4})\b\.?\s*,?", re.IGNORECASE)
_CIT_RE = re.compile(rf"^(?:art(?:ikel|\.)?\s*)?(?P<art>{_ART})\s*,?\s*(?P<wet>.+?)\s*\.?$", re.IGNORECASE)
_CIT_WET_FIRST_RE = re.compile(rf"^(?P<wet>BW|[A-Za-z][\w ]*?)\s+(?:art(?:ikel|\.)?\s*)?(?P<art>{_ART})$", re.IGNORECASE)
_BWB_RE = re.compile(r"^BWB[RV]\d{7}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class WetError(Exception):
    """Invalid citation, unknown law/article, or unavailable version (Dutch message)."""


@dataclass
class Citation:
    bwb_id: str
    wet: str            # human name, e.g. "Burgerlijk Wetboek Boek 6"
    artikel: str        # as cited, e.g. "6:162", "8:1", "350"
    artikel_nr: str     # as numbered inside the BWB document, e.g. "162", "8:1", "350"
    lid: str | None = None
    onderdeel: str | None = None
    citaat: str = ""


@dataclass
class Versie:
    label: str          # e.g. "2026-07-16_0"
    geldig_van: str     # datum_inwerkingtreding
    geldig_tot: str     # einddatum ("9999-12-31" = open)
    item: str           # relative item path in the repository
    sha512: str = ""

    @property
    def url(self) -> str:
        return f"{REPO}/{self.item}"


# --------------------------------------------------------------------------- citations

def _norm_wet(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().strip(".,").lower())


def parse_citation(text: str) -> Citation:
    """Parse '6:162 BW', 'art. 7:673 lid 2 BW', 'art. 8:1 Awb', 'art. 350 Sr', 'art. 843a Rv'.

    Raises WetError with a Dutch message when the law is unknown or the form is not recognised.
    """
    raw = (text or "").strip()
    work = raw
    lid = onderdeel = None
    m = _LID_RE.search(work)
    if m:
        lid = m.group(1).lower()
        work = (work[:m.start()] + " " + work[m.end():]).strip()
    m = _SUB_RE.search(work)
    if m:
        onderdeel = m.group(1).lower()
        work = (work[:m.start()] + " " + work[m.end():]).strip()
    work = re.sub(r"\s+", " ", work).strip()
    m = _CIT_RE.match(work)
    if m and not re.fullmatch(_ART, m.group("wet"), re.IGNORECASE):
        artikel, wet = m.group("art"), m.group("wet")
    else:
        m2 = _CIT_WET_FIRST_RE.match(work)
        if not m2:
            raise WetError(
                f"Kan {raw!r} niet lezen als wetsartikel. Voorbeelden: '6:162 BW', 'art. 7:673 lid 2 BW', "
                "'art. 8:1 Awb', 'art. 350 Sr'.")
        artikel, wet = m2.group("art"), m2.group("wet")
    artikel = artikel.lower()
    wet_key = _norm_wet(wet)
    if wet_key in ("bw", "burgerlijk wetboek"):
        if ":" not in artikel:
            raise WetError(f"Geef bij het BW het boek aan, bijvoorbeeld '6:162 BW' (niet '{artikel} BW').")
        boek, nr = artikel.split(":", 1)
        boek_key = boek.upper()
        if boek_key not in BW_BOEKEN:
            raise WetError(f"Onbekend BW-boek {boek!r}. Beschikbaar: {', '.join(BW_BOEKEN)}.")
        bwb, naam = BW_BOEKEN[boek_key]
        return Citation(bwb, naam, f"{boek_key}:{nr}", nr, lid, onderdeel, raw)
    if wet_key in ("avg", "gdpr"):
        raise WetError("De AVG is een EU-verordening (CELEX 32016R0679) en staat niet in het BWB. "
                       "Voor de Nederlandse uitvoeringswet: gebruik 'UAVG'.")
    if wet_key not in WETTEN:
        raise WetError(
            f"Onbekende wet {wet!r}. Bekende afkortingen: BW (boek 1-8, 10), "
            f"{', '.join(sorted({a[0] for a, _, _ in _WETTEN}))}. "
            "Voor andere regelingen: geef het BWB-id op (te vinden in de URL op wetten.overheid.nl).")
    bwb, naam = WETTEN[wet_key]
    return Citation(bwb, naam, artikel, artikel, lid, onderdeel, raw)


def citation_from_bwb(bwb_id: str, artikel: str, lid: str | None = None) -> Citation:
    bwb_id = bwb_id.strip().upper()
    if not _BWB_RE.match(bwb_id):
        raise WetError(f"Geen geldig BWB-id: {bwb_id!r} (verwacht bijvoorbeeld BWBR0005289).")
    art = re.sub(r"^(?:art(?:ikel|\.)?\s*)", "", artikel.strip(), flags=re.IGNORECASE).lower()
    nr = art.split(":", 1)[1] if bwb_id in BW_IDS and ":" in art else art
    naam = next((n for b, n in list(BW_BOEKEN.values()) + list(WETTEN.values()) if b == bwb_id), bwb_id)
    return Citation(bwb_id, naam, art, nr, lid, None, f"{bwb_id} {artikel}")


# --------------------------------------------------------------------------- versions + cache

def _cache_dir() -> Path:
    base = os.environ.get("NLJS_CACHE_DIR")
    root = Path(base) if base else Path.home() / ".cache" / "nl-juridische-skills"
    return root / "bwb"


def _check_bwb(bwb_id: str) -> str:
    bwb_id = (bwb_id or "").strip().upper()
    if not _BWB_RE.match(bwb_id):
        raise WetError(f"Geen geldig BWB-id: {bwb_id!r}.")
    return bwb_id


def parse_manifest(xml_bytes: bytes, bwb_id: str) -> list[Versie]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise WetError(f"Manifest van {bwb_id} is geen geldige XML ({exc}).") from None
    versies = []
    for expr in root.findall("expression"):
        label = expr.get("label", "")
        meta = expr.find("metadata")
        van = meta.findtext("datum_inwerkingtreding", "") if meta is not None else ""
        tot = meta.findtext("einddatum", "") if meta is not None else ""
        for man in expr.findall("manifestation"):
            if man.get("label") != "xml":
                continue
            item = man.find("item")
            if item is None or item.get("_deleted") == "true":
                continue
            sha = man.findtext("metadata/hashcode", "") or ""
            versies.append(Versie(label, van, tot or "9999-12-31",
                                  f"{bwb_id}/{label}/xml/{item.get('label')}", sha.lower()))
    versies.sort(key=lambda v: (v.geldig_van, v.label))
    return versies


_MANIFESTS: dict[str, bytes] = {}


def load_manifest(bwb_id: str) -> bytes:
    """Raw manifest.xml of a regeling (fetched once per process)."""
    bwb_id = _check_bwb(bwb_id)
    if bwb_id not in _MANIFESTS:
        try:
            _MANIFESTS[bwb_id] = nl_http.get(f"{REPO}/{bwb_id}/manifest.xml", accept="application/xml").body
        except nl_http.FetchError as exc:
            if exc.kind == "niet_gevonden":
                raise WetError(f"Regeling {bwb_id} niet gevonden in de officiële BWB-repository.") from None
            raise
    return _MANIFESTS[bwb_id]


def list_versies(bwb_id: str) -> list[Versie]:
    bwb_id = _check_bwb(bwb_id)
    versies = parse_manifest(load_manifest(bwb_id), bwb_id)
    if not versies:
        raise WetError(f"Geen XML-versies gevonden in het manifest van {bwb_id}.")
    return versies


def kies_versie(versies: list[Versie], datum: str | None = None) -> Versie:
    """Pick the version valid on ``datum`` (inclusive). Latest label wins on ties."""
    if datum is None:
        datum = _dt.date.today().isoformat()
    if not DATE_RE.match(datum):
        raise WetError(f"Datum {datum!r} heeft niet het formaat JJJJ-MM-DD.")
    try:
        _dt.date.fromisoformat(datum)
    except ValueError:
        raise WetError(f"Datum {datum!r} bestaat niet.") from None
    matches = [v for v in versies if v.geldig_van <= datum <= v.geldig_tot]
    if matches:
        return matches[-1]
    earliest = versies[0].geldig_van if versies else "?"
    if versies and datum < earliest:
        raise WetError(f"Geen versie beschikbaar voor {datum}: de officiële repository heeft voor deze "
                       f"regeling versies vanaf {earliest}.")
    raise WetError(f"Geen versie gevonden die geldig was op {datum} (mogelijk was de regeling toen niet "
                   "in werking of is ze vervallen).")


def load_toestand(bwb_id: str, datum: str | None = None) -> tuple[bytes, Versie]:
    """Return (xml_bytes, versie) for the version valid on ``datum``.

    Cache: ``<cache>/<BWB>/<label>.xml`` plus a ``.hash`` sidecar holding the manifest
    hash at download time; the cached file is reused while the manifest hash is unchanged.
    Note: for some older versions the manifest hash does not match the served file
    (observed 2026-09-23 for BWBR0002448 2010-10-10_0), so a mismatch is not an error.
    """
    bwb_id = _check_bwb(bwb_id)
    versie = kies_versie(list_versies(bwb_id), datum)
    cache = _cache_dir() / bwb_id / f"{versie.label}.xml"
    sidecar = cache.with_suffix(".hash")
    if cache.is_file() and sidecar.is_file() and sidecar.read_text(encoding="utf-8").strip() == versie.sha512:
        return cache.read_bytes(), versie
    data = nl_http.get(versie.url, accept="application/xml").body
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(cache)
        sidecar.write_text(versie.sha512, encoding="utf-8")
    except OSError:
        pass  # cache is optional
    return data, versie


# --------------------------------------------------------------------------- article parsing

_DROP = {"meta-data", "brondata", "jcis", "jci", "noot"}


def _clean(text: str) -> str:
    return re.sub(r"[ \t\r\n ]+", " ", text or "").strip()


def _norm_nr(nr: str) -> str:
    return re.sub(r"\s+", "", (nr or "")).rstrip(".").lower()


def find_artikel(root, artikel_nr: str):
    """Find <artikel> whose <kop><nr> equals ``artikel_nr``; prefer non-bijlage, non-vervallen."""
    target = _norm_nr(artikel_nr)
    found = []
    for el in root.iter("artikel"):
        nr = el.find("kop/nr")
        if nr is not None and _norm_nr("".join(nr.itertext())) == target:
            found.append(el)
    if not found:
        return None
    found.sort(key=lambda e: ("/Bijlage" in (e.get("bwb-ng-variabel-deel") or ""),
                              e.get("status") == "vervallen"))
    return found[0]


def _text(el) -> str:
    parts = [el.text or ""]
    for c in el:
        if c.tag in _DROP:
            parts.append(c.tail or "")
            continue
        if c.tag == "lijst":
            parts.append("\n" + _lijst(c) + "\n")
        elif c.tag in ("al", "lid"):
            parts.append("\n" + _text(c) + "\n")
        elif c.tag == "table":
            parts.append("\n" + _table(c) + "\n")
        else:
            parts.append(_text(c))
        parts.append(c.tail or "")
    return "".join(parts)


def _lines(text: str) -> str:
    return "\n".join(ln for ln in (_clean(x) for x in text.split("\n")) if ln)


def _lijst(el, depth: int = 0) -> str:
    out = []
    indent = "  " * depth
    for li in el.findall("li"):
        marker = _clean("".join(li.findtext("li.nr", "") or ""))
        body = []
        for c in li:
            if c.tag in ("li.nr",) or c.tag in _DROP:
                continue
            if c.tag == "lijst":
                body.append("\n" + _lijst(c, depth + 1))
            else:
                body.append(_text(c))
        text = _lines("".join(body))
        first, _, rest = text.partition("\n")
        out.append(f"{indent}{marker} {first}".rstrip() + (("\n" + rest) if rest else ""))
    return "\n".join(out)


def _table(el) -> str:
    rows = []
    for row in el.iter("row"):
        cells = [_clean(_text(e)).replace("|", "\\|") for e in row.findall("entry")]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows[1:]])


def parse_artikel(el) -> dict:
    kop = el.find("kop")
    label = _clean(kop.findtext("label", "") if kop is not None else "") or "Artikel"
    nr = _clean("".join(kop.find("nr").itertext())) if kop is not None and kop.find("nr") is not None else ""
    titel = _clean("".join(kop.find("titel").itertext())) if kop is not None and kop.find("titel") is not None else ""
    leden, loose = [], []
    for c in el:
        if c.tag in ("kop",) or c.tag in _DROP:
            continue
        if c.tag == "lid":
            lidnr = _clean("".join(c.find("lidnr").itertext())) if c.find("lidnr") is not None else ""
            body = "".join("\n" + (_lijst(s) if s.tag == "lijst" else _text(s)) + "\n"
                           for s in c if s.tag not in ("lidnr",) and s.tag not in _DROP)
            leden.append({"lid": lidnr.rstrip("."), "tekst": _lines(body)})
        elif c.tag == "lijst":
            loose.append(_lijst(c))
        else:
            loose.append(_text(c))
    tekst = _lines("\n".join(loose))
    joined = " ".join([tekst] + [l["tekst"] for l in leden]).strip().lower()
    return {
        "kop": f"{label} {nr}".strip(),
        "nummer": nr,
        "titel": titel,
        "leden": leden,
        "tekst": tekst,
        "vervallen": el.get("status") == "vervallen" or joined.startswith("[vervallen") or joined.startswith("vervallen"),
        "inwerking": el.get("inwerking", ""),
        "pad": el.get("bwb-ng-variabel-deel", ""),
    }


def wetten_url(bwb_id: str, artikel_nr: str, datum: str | None = None) -> str:
    q = f"jci1.3:c:{bwb_id}&artikel={artikel_nr}"
    if datum:
        q += f"&g={datum}"
    return "https://wetten.overheid.nl/" + urllib.parse.quote(q, safe=":&=")


def fetch_artikel(citation, datum: str | None = None, lid: str | None = None) -> dict:
    """Fetch one article. ``citation`` is a Citation or a string like '7:673 lid 2 BW'.

    Returns dict: citaat, wet, bwb_id, artikel, lid (requested), kop, titel, leden (filtered
    to the requested lid when given), tekst, vervallen, versie {label, geldig_van, geldig_tot,
    bron_xml}, peildatum, url.
    """
    cit = parse_citation(citation) if isinstance(citation, str) else citation
    want_lid = (lid or cit.lid)
    data, versie = load_toestand(cit.bwb_id, datum)
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise WetError(f"Wettekst-XML van {cit.bwb_id} is niet leesbaar ({exc}).") from None
    el = find_artikel(root, cit.artikel_nr)
    if el is None:
        tot = "heden" if versie.geldig_tot.startswith("9999") else versie.geldig_tot
        raise WetError(f"Artikel {cit.artikel} niet gevonden in {cit.wet} ({cit.bwb_id}), versie "
                       f"geldig {versie.geldig_van} t/m {tot}. Controleer het artikelnummer.")
    art = parse_artikel(el)
    leden = art["leden"]
    if want_lid:
        leden = [l for l in leden if l["lid"].lower() == str(want_lid).lower()]
        if not leden:
            beschikbaar = ", ".join(l["lid"] for l in art["leden"]) or "geen (artikel heeft geen leden)"
            raise WetError(f"Lid {want_lid} bestaat niet in artikel {cit.artikel} {cit.wet} "
                           f"(beschikbare leden: {beschikbaar}).")
    return {
        "citaat": cit.citaat or cit.artikel,
        "wet": cit.wet,
        "bwb_id": cit.bwb_id,
        "artikel": cit.artikel,
        "lid": want_lid,
        "onderdeel": cit.onderdeel,
        "kop": art["kop"],
        "titel": art["titel"],
        "leden": leden,
        "alle_leden": [l["lid"] for l in art["leden"]],
        "tekst": art["tekst"] if not want_lid else "",
        "vervallen": art["vervallen"],
        "versie": {"label": versie.label, "geldig_van": versie.geldig_van,
                   "geldig_tot": versie.geldig_tot, "bron_xml": versie.url},
        "peildatum": datum or _dt.date.today().isoformat(),
        "url": wetten_url(cit.bwb_id, cit.artikel_nr, datum),
    }


def render_artikel(r: dict) -> str:
    lid = f" lid {r['lid']}" if r.get("lid") else ""
    geldig_tot = r["versie"]["geldig_tot"]
    tot = "heden" if geldig_tot.startswith("9999") else geldig_tot
    lines = [
        f"# Art. {r['artikel']}{lid} {r['wet']}",
        "",
        f"- **Regeling:** {r['wet']} ({r['bwb_id']})",
        f"- **Peildatum:** {r['peildatum']}",
        f"- **Versie:** geldig van {r['versie']['geldig_van']} t/m {tot} ({r['versie']['label']})",
        f"- **Bron:** {r['url']}",
        "",
        f"## {r['kop']}" + (f" — {r['titel']}" if r.get("titel") else ""),
        "",
    ]
    if r.get("vervallen"):
        lines += ["_Let op: dit artikel is in deze versie vervallen._", ""]
    if r.get("tekst"):
        lines += [r["tekst"], ""]
    for l in r["leden"]:
        lines += [f"**{l['lid']}.** {l['tekst']}", ""]
    if r.get("onderdeel"):
        lines += [f"_Gevraagd onderdeel: {r['onderdeel']} (hierboven staat het volledige lid)._", ""]
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------- change history (WTI)

def load_wti(bwb_id: str) -> bytes:
    """Return the WTI XML for ``bwb_id``; cached until the manifest reports a newer WTI."""
    bwb_id = _check_bwb(bwb_id)
    try:
        mroot = ET.fromstring(load_manifest(bwb_id))
    except ET.ParseError as exc:
        raise WetError(f"Manifest van {bwb_id} is geen geldige XML ({exc}).") from None
    stamp = mroot.findtext("metadata/tijdstip_laatste_wijziging_wti", "") or ""
    loc = mroot.findtext("metadata/wti_locatie", "") or f"{bwb_id}.WTI"
    cache = _cache_dir() / bwb_id / "wti.xml"
    marker = _cache_dir() / bwb_id / "wti.stamp"
    if stamp and cache.is_file() and marker.is_file() and marker.read_text(encoding="utf-8").strip() == stamp:
        return cache.read_bytes()
    data = nl_http.get(f"{REPO}/{bwb_id}/{loc}", accept="application/xml").body
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(data)
        marker.write_text(stamp, encoding="utf-8")
    except OSError:
        pass
    return data


def _bekendmaking(el) -> dict | None:
    if el is None:
        return None
    soort = el.get("soort", "")
    jaar = el.findtext("publicatiejaar", "") or ""
    nummer = el.findtext("publicatienummer", "") or ""
    ident = el.get("urlidentifier", "") or ""
    return {
        "soort": soort, "jaar": jaar, "nummer": nummer, "id": ident,
        "publicatiedatum": el.findtext("publicatiedatum", "") or "",
        "citaat": f"{soort}. {jaar}/{nummer}" if soort and jaar else "",
        "url": f"https://zoek.officielebekendmakingen.nl/{ident}" if ident else "",
    }


def parse_wti_artikel(wti_bytes: bytes, artikel_nr: str) -> list[dict]:
    """All WTI change entries for an article label ('Artikel <nr>'), oldest first."""
    try:
        root = ET.fromstring(wti_bytes)
    except ET.ParseError as exc:
        raise WetError(f"WTI-bestand is geen geldige XML ({exc}).") from None
    want = f"artikel {_norm_nr(artikel_nr)}"
    out = []
    for datum in root.iter("datum"):
        label = re.sub(r"\s+", " ", datum.get("label", "")).strip().lower().rstrip(".")
        if label != want:
            continue
        for det in datum.findall("details"):
            bron = det.find("ontstaansbron/bron")
            opm = [_clean("".join(a.itertext())) for a in det.findall("opmerkingen/opmerking")]
            out.append({
                "datum": datum.get("waarde", ""),
                "betreft": _clean(det.findtext("betreft", "") or ""),
                "dossier": _clean(bron.findtext("dossiernummer", "") or "") if bron is not None else "",
                "bron": _bekendmaking(bron.find("bekendmaking") if bron is not None else None),
                "inwerkingtreding": _bekendmaking(det.find("inwerkingtreding/bron/bekendmaking")),
                "terugwerkende_kracht": _clean(det.findtext(".//terugwerkende-kracht-datum", "") or ""),
                "opmerkingen": [o for o in opm if o],
            })
    out.sort(key=lambda e: (not e["datum"], e["datum"]))  # undated (never in force) last
    return out


def wijzigingen_artikel(citation) -> dict:
    """Change history of one article from the official WTI file."""
    cit = parse_citation(citation) if isinstance(citation, str) else citation
    entries = parse_wti_artikel(load_wti(cit.bwb_id), cit.artikel_nr)
    if not entries:
        raise WetError(f"Geen wijzigingshistorie gevonden voor artikel {cit.artikel} in {cit.wet} ({cit.bwb_id}).")
    return {"bwb_id": cit.bwb_id, "wet": cit.wet, "artikel": cit.artikel,
            "bron_wti": f"{REPO}/{cit.bwb_id}/{cit.bwb_id}.WTI", "wijzigingen": entries}


def render_wijzigingen(r: dict) -> str:
    lines = [f"# Wijzigingshistorie art. {r['artikel']} {r['wet']}", "",
             f"- **Bron:** {r['bron_wti']} (wetstechnische informatie, BWB)", "",
             "| Datum | Betreft | Dossier | Bron | Inwerkingtreding | Opmerking |", "|---|---|---|---|---|---|"]
    for e in r["wijzigingen"]:
        bron = (e["bron"] or {}).get("citaat", "")
        iwt = (e["inwerkingtreding"] or {}).get("citaat", "")
        opm = " ".join(e["opmerkingen"]).replace("|", "\\|")
        lines.append(f"| {e['datum'] or 'geen (niet in werking)'} | {e['betreft']} | {e['dossier']} | {bron} | {iwt} | {opm} |")
    return "\n".join(lines) + "\n"
