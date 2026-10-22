"""Offline tests for the rechtspraak skill (no network).

Fixtures in tests/fixtures/ were recorded on 2026-09-23 from the official
open-data endpoints (public rulings; see fixtures/BRONNEN.md).
Run: python3 -m unittest discover -s skills/rechtspraak/tests
"""
from __future__ import annotations

import io
import os
import sys
import unittest
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import celex_client as cc  # noqa: E402
import fetch_celex  # noqa: E402
import fetch_ecli  # noqa: E402
import nl_http  # noqa: E402
import rechtspraak_client as rc  # noqa: E402
import zoek_uitspraken  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def fixture(name: str) -> bytes:
    with open(os.path.join(FIX, name), "rb") as fh:
        return fh.read()


def fake_get(routes: dict):
    """Return a replacement for nl_http.get that serves fixtures by URL substring."""
    calls = []

    def _get(url, accept="*/*", headers=None, allow_status=()):
        calls.append(url)
        for key, name in routes.items():
            if key in url:
                if name == 404:
                    raise nl_http.FetchError("Niet gevonden (HTTP 404)", 404, "niet_gevonden", url)
                return nl_http.Response(200, fixture(name), url, {})
        raise AssertionError(f"onverwachte URL in test: {url}")

    _get.calls = calls
    return _get


class TestEcliInput(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(rc.normalize_ecli(" ecli:nl:hr:2025:667 "), "ECLI:NL:HR:2025:667")
        self.assertEqual(rc.normalize_ecli("ECLI:NL:HR:1981:AG4158"), "ECLI:NL:HR:1981:AG4158")

    def test_invalid(self):
        for bad in ("", "HR 2025:667", "ECLI:NL:HR:25:667", "ECLI NL HR 2025 667"):
            with self.assertRaises(rc.RechtspraakError):
                rc.normalize_ecli(bad)

    def test_eu_ecli_refused_by_nl_client(self):
        with self.assertRaises(rc.RechtspraakError) as ctx:
            rc.fetch_ecli_xml("ECLI:EU:C:2014:317")
        self.assertIn("Europese ECLI", str(ctx.exception))


class TestParseUitspraak(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = rc.parse_uitspraak(fixture("content_ECLI_NL_HR_2025_667.xml"))
        cls.md = rc.render_uitspraak(cls.p)

    def test_metadata(self):
        p = self.p
        self.assertEqual(p["ecli"], "ECLI:NL:HR:2025:667")
        self.assertEqual(p["instantie"], "Hoge Raad")
        self.assertEqual(p["datum"], "2025-04-25")
        self.assertEqual(p["zaaknummers"], ["24/00086"])
        self.assertIn("Cassatie", p["procedure"])
        self.assertIn("Burgerlijk procesrecht", "; ".join(p["rechtsgebieden"]))
        self.assertTrue(p["titel"].startswith("ECLI:NL:HR:2025:667 Hoge Raad"))
        self.assertEqual(p["tekst_type"], "uitspraak")

    def test_relations(self):
        eclis = {r["ecli"] for r in self.p["relaties"]}
        self.assertEqual(eclis, {"ECLI:NL:GHARL:2023:8464", "ECLI:NL:PHR:2024:1131"})

    def test_inhoudsindicatie(self):
        self.assertEqual(self.p["inhoudsindicatie"],
                         "Art. 236 Rv. Gezag van gewijsde. Nieuwe feitelijke grondslag? Letselschadezaak.")

    def test_ro_numbers_preserved(self):
        self.assertIn("**2.1** In cassatie kan van het volgende worden uitgegaan.", self.md)
        self.assertIn("**3.4** De overige klachten van het middel kunnen evenmin tot cassatie leiden.", self.md)
        self.assertIn("### 1 Procesverloop", self.md)
        self.assertIn("### 4 Beslissing", self.md)

    def test_footnotes(self):
        self.assertEqual(len(self.p["voetnoten"]), 6)
        self.assertEqual(self.p["voetnoten"][0][0], "1")
        self.assertIn("ECLI:NL:RBGEL:2019:6276", self.p["voetnoten"][0][1])
        self.assertIn("overgenomen", self.md)
        self.assertIn("[^1]", self.md)
        self.assertIn("[^1]: Rechtbank Gelderland 13 november 2019, ECLI:NL:RBGEL:2019:6276.", self.md)

    def test_meta_only_fixture(self):
        p = rc.parse_uitspraak(fixture("meta_ECLI_NL_HR_1981_AG4158.xml"))
        self.assertEqual(p["ecli"], "ECLI:NL:HR:1981:AG4158")
        self.assertEqual(p["datum"], "1981-03-13")
        self.assertIn("AG4158", p["vervangt"])
        self.assertTrue(any(v.startswith("NJ 1981/635") for v in p["vindplaatsen"]))
        self.assertIn("maatschappelijke kringen", p["inhoudsindicatie"])
        self.assertEqual(p["tekst"], "")
        md = rc.render_uitspraak(p, meta_only=True)
        self.assertNotIn("## Uitspraak", md)

    def test_missing_body_is_stated(self):
        p = rc.parse_uitspraak(fixture("meta_ECLI_NL_HR_1981_AG4158.xml"))
        self.assertIn("niet gepubliceerd in de open data", rc.render_uitspraak(p))

    def test_bad_xml(self):
        with self.assertRaises(rc.RechtspraakError):
            rc.parse_uitspraak(b"<html>geen xml")


class TestSearch(unittest.TestCase):
    def test_build_url(self):
        url = rc.build_search_url(instanties=["RBAMS"], datum_van="2026-08-01", datum_tot="2026-08-31",
                                  rechtsgebieden=["arbeidsrecht"], soort="uitspraak",
                                  alleen_met_tekst=True, max_resultaten=3)
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertEqual(q["creator"], ["http://standaarden.overheid.nl/owms/terms/Rechtbank_Amsterdam"])
        self.assertEqual(q["date"], ["2026-08-01", "2026-08-31"])
        self.assertEqual(q["subject"], ["http://psi.rechtspraak.nl/rechtsgebied#civielRecht_arbeidsrecht"])
        self.assertEqual(q["type"], ["Uitspraak"])
        self.assertEqual(q["return"], ["DOC"])
        self.assertEqual(q["max"], ["3"])

    def test_single_bound_dates_become_range(self):
        url = rc.build_search_url(datum_van="2026-01-01", max_resultaten=1)
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertEqual(len(q["date"]), 2)
        self.assertEqual(q["date"][0], "2026-01-01")

    def test_validation(self):
        with self.assertRaises(rc.RechtspraakError):
            rc.build_search_url(datum_van="01-08-2026")
        with self.assertRaises(rc.RechtspraakError):
            rc.build_search_url(datum_van="2026-09-01", datum_tot="2026-08-01")
        with self.assertRaises(rc.RechtspraakError):
            rc.build_search_url(instanties=["XYZ"])
        with self.assertRaises(rc.RechtspraakError):
            rc.build_search_url(rechtsgebieden=["huurrecht"])
        with self.assertRaises(rc.RechtspraakError):
            rc.build_search_url(max_resultaten=5000)

    def test_aliases(self):
        self.assertEqual(rc.resolve_rechtsgebied("civiel"), rc.RECHTSGEBIEDEN["civiel"])
        self.assertEqual(rc.resolve_rechtsgebied("Personen en familierecht"),
                         rc.RECHTSGEBIEDEN["personen-en-familierecht"])
        self.assertEqual(rc.resolve_instantie("hr"), rc.INSTANTIES["HR"])

    def test_parse_search(self):
        r = rc.parse_search(fixture("zoeken_rbams_arbeidsrecht_2026-08.xml"))
        self.assertEqual(r["totaal"], 14)
        self.assertEqual(len(r["resultaten"]), 3)
        first = r["resultaten"][0]
        self.assertTrue(first["ecli"].startswith("ECLI:NL:RBAMS:2026:"))
        self.assertEqual(first["instantie"], "Rechtbank Amsterdam")
        self.assertRegex(first["datum"], r"^2026-08-\d\d$")
        self.assertTrue(first["samenvatting"])

    def test_parse_empty(self):
        r = rc.parse_search(fixture("zoeken_leeg.xml"))
        self.assertEqual(r["totaal"], 0)
        self.assertEqual(r["resultaten"], [])
        self.assertIn("Geen resultaten", rc.render_search({"url": "x", **r}))

    def test_local_keyword_filter(self):
        r = rc.parse_search(fixture("zoeken_rbams_arbeidsrecht_2026-08.xml"))
        hits = rc.filter_trefwoorden(r["resultaten"], ["concurrent"])
        self.assertEqual(len(hits), 2)
        self.assertEqual([h["ecli"] for h in rc.filter_trefwoorden(r["resultaten"], ["Concurrent", "wervingsverbod"])],
                         ["ECLI:NL:RBAMS:2026:8592"])
        self.assertEqual(rc.filter_trefwoorden(r["resultaten"], ["bestaatniet"]), [])

    def test_zoek_with_keywords_is_marked_local(self):
        with mock.patch.object(nl_http, "get", fake_get({"/uitspraken/zoeken": "zoeken_rbams_arbeidsrecht_2026-08.xml"})) as g:
            res = rc.zoek(trefwoorden=["concurrent"], instanties=["RBAMS"], datum_van="2026-08-01",
                          datum_tot="2026-08-31", max_resultaten=1)
        self.assertTrue(res["lokaal_gefilterd"])
        self.assertEqual(res["treffers_lokaal"], 2)
        self.assertEqual(len(res["resultaten"]), 1)
        self.assertIn("max=1000", g.calls[0])
        self.assertIn("sort=DESC", g.calls[0])
        self.assertIn("geen full-text", rc.render_search(res))


class TestCelex(unittest.TestCase):
    def test_zaak_naar_celex(self):
        self.assertEqual(cc.zaak_naar_celex("C-131/12"), "62012CJ0131")
        self.assertEqual(cc.zaak_naar_celex("C-131/12", "conclusie"), "62012CC0131")
        self.assertEqual(cc.zaak_naar_celex("T-201/04"), "62004TJ0201")
        self.assertEqual(cc.zaak_naar_celex("C-6/64"), "61964CJ0006")
        self.assertEqual(cc.zaak_naar_celex("C-311/18"), "62018CJ0311")

    def test_normalize_id(self):
        self.assertEqual(cc.normalize_id("32016r0679"), ("celex", "32016R0679"))
        self.assertEqual(cc.normalize_id("ecli:eu:c:2014:317"), ("ecli", "ECLI:EU:C:2014:317"))
        self.assertEqual(cc.normalize_id("C-131/12"), ("celex", "62012CJ0131"))
        with self.assertRaises(cc.CelexError):
            cc.normalize_id("ECLI:NL:HR:2025:667")
        with self.assertRaises(cc.CelexError):
            cc.normalize_id("AVG")

    def test_html_to_markdown_points(self):
        md = cc.html_to_markdown(fixture("celex_62012CJ0131_nld_ingekort.html").decode("utf-8"))
        self.assertIn("ARREST VAN HET HOF (Grote kamer)", md)
        self.assertIn("In zaak C‑131/12,", md)
        self.assertIn("**1** Het verzoek om een prejudiciële beslissing betreft", md)
        self.assertIn("**2** Dit verzoek is ingediend", md)
        self.assertNotIn("| --- |", md)          # numbered points are not rendered as tables
        self.assertIn("— Google Spain SL en Google Inc.", md)

    def test_fetch_markdown_offline(self):
        routes = {"publications.europa.eu/resource/ecli/": "celex_62012CJ0131_nld_ingekort.html"}
        with mock.patch.object(nl_http, "get", fake_get(routes)):
            md = cc.fetch_markdown("ECLI:EU:C:2014:317")
        self.assertTrue(md.startswith("# ECLI:EU:C:2014:317"))
        self.assertIn("**Taal:** nld", md)
        self.assertIn("uri=ecli:ECLI:EU:C:2014:317", md)


class TestCli(unittest.TestCase):
    def run_main(self, fn, argv, routes):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(nl_http, "get", fake_get(routes)), redirect_stdout(out), redirect_stderr(err):
            code = fn(argv)
        return code, out.getvalue(), err.getvalue()

    def test_fetch_ecli_cli(self):
        code, out, _ = self.run_main(fetch_ecli.main, ["ECLI:NL:HR:2025:667"],
                                     {"content?id=ECLI%3ANL%3AHR%3A2025%3A667": "content_ECLI_NL_HR_2025_667.xml"})
        self.assertEqual(code, 0)
        self.assertIn("**2.1**", out)

    def test_fetch_ecli_not_found(self):
        code, _, err = self.run_main(fetch_ecli.main, ["ECLI:NL:HR:2099:1"], {"content?id=": 404})
        self.assertEqual(code, 1)
        self.assertIn("niet gevonden", err)

    def test_fetch_ecli_invalid(self):
        code, _, err = self.run_main(fetch_ecli.main, ["HR 2025/667"], {})
        self.assertEqual(code, 1)
        self.assertIn("Geen geldige ECLI", err)

    def test_zoek_cli_requires_filter(self):
        code, _, err = self.run_main(zoek_uitspraken.main, [], {})
        self.assertEqual(code, 1)
        self.assertIn("minstens één filter", err)

    def test_zoek_cli(self):
        code, out, _ = self.run_main(
            zoek_uitspraken.main,
            ["--instantie", "RBAMS", "--rechtsgebied", "arbeidsrecht", "--van", "2026-08-01", "--tot", "2026-08-31"],
            {"/uitspraken/zoeken": "zoeken_rbams_arbeidsrecht_2026-08.xml"})
        self.assertEqual(code, 0)
        self.assertIn("| ECLI:NL:RBAMS:2026:", out)

    def test_fetch_celex_cli_zaaknummer(self):
        code, out, err = self.run_main(fetch_celex.main, ["C-131/12"],
                                       {"resource/celex/62012CJ0131": "celex_62012CJ0131_nld_ingekort.html"})
        self.assertEqual(code, 0)
        self.assertIn("62012CJ0131", err)
        self.assertIn("**1** Het verzoek", out)


class TestHttp(unittest.TestCase):
    def test_user_agent_is_honest(self):
        self.assertTrue(nl_http.USER_AGENT.startswith("nl-juridische-skills/"))


if __name__ == "__main__":
    unittest.main()
