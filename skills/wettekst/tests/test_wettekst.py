"""Offline tests for the wettekst skill (no network).

Fixtures in tests/fixtures/ are trimmed copies of official BWB XML recorded on
2026-09-23 (see fixtures/BRONNEN.md).
Run: python3 -m unittest discover -s skills/wettekst/tests
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import fetch_wet  # noqa: E402
import nl_http  # noqa: E402
import wet_client as wc  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
BW7_XML = "BWBR0005290_2026-07-01_0_ingekort.xml"


def fixture(name: str) -> bytes:
    with open(os.path.join(FIX, name), "rb") as fh:
        return fh.read()


def fake_get(routes: dict):
    calls = []

    def _get(url, accept="*/*", headers=None, allow_status=()):
        calls.append(url)
        for key, name in routes.items():
            if key in url:
                return nl_http.Response(200, fixture(name), url, {})
        raise AssertionError(f"onverwachte URL in test: {url}")

    _get.calls = calls
    return _get


BW7_ROUTES = {
    "BWBR0005290/manifest.xml": "manifest_BWBR0005290_ingekort.xml",
    "BWBR0005290/2026-07-01_0/xml/": BW7_XML,
}


class TestCitations(unittest.TestCase):
    def check(self, text, bwb, artikel, nr, lid=None, onderdeel=None):
        c = wc.parse_citation(text)
        self.assertEqual((c.bwb_id, c.artikel, c.artikel_nr, c.lid, c.onderdeel),
                         (bwb, artikel, nr, lid, onderdeel), text)

    def test_bw_forms(self):
        self.check("6:162 BW", "BWBR0005289", "6:162", "162")
        self.check("art. 3:40 BW", "BWBR0005291", "3:40", "40")
        self.check("art. 7:673 lid 2 BW", "BWBR0005290", "7:673", "673", "2")
        self.check("artikel 7:673, lid 2, BW", "BWBR0005290", "7:673", "673", "2")
        self.check("Art. 6:106 lid 1 sub a BW", "BWBR0005289", "6:106", "106", "1", "a")
        self.check("BW 6:162", "BWBR0005289", "6:162", "162")
        self.check("art. 2:9 BW", "BWBR0003045", "2:9", "9")
        self.check("art. 8:1 BW", "BWBR0005034", "8:1", "1")
        self.check("art. 10:154 BW", "BWBR0030068", "10:154", "154")
        self.check("art. 1:1 BW", "BWBR0002656", "1:1", "1")

    def test_other_codes(self):
        self.check("art. 8:1 Awb", "BWBR0005537", "8:1", "8:1")
        self.check("art. 350 Sr", "BWBR0001854", "350", "350")
        self.check("art. 843a Rv", "BWBR0001827", "843a", "843a")
        self.check("art. 27 Sv", "BWBR0001903", "27", "27")
        self.check("art. 1 Grondwet", "BWBR0001840", "1", "1")
        self.check("art. 1 Gw", "BWBR0001840", "1", "1")
        self.check("art. 22 UAVG", "BWBR0040940", "22", "22")
        self.check("art. 42 Fw", "BWBR0001860", "42", "42")
        self.check("art. 5.1 Ow", "BWBR0037885", "5.1", "5.1")

    def test_errors(self):
        for bad, fragment in (("162 BW", "boek"), ("art. 6 AVG", "EU-verordening"),
                              ("art. 5 Foowet", "Onbekende wet"), ("onzin", "niet lezen"),
                              ("art. 9:1 BW", "Onbekend BW-boek")):
            with self.assertRaises(wc.WetError) as ctx:
                wc.parse_citation(bad)
            self.assertIn(fragment, str(ctx.exception), bad)

    def test_citation_from_bwb(self):
        c = wc.citation_from_bwb("bwbr0005290", "art. 7:673")
        self.assertEqual((c.bwb_id, c.artikel_nr), ("BWBR0005290", "673"))
        with self.assertRaises(wc.WetError):
            wc.citation_from_bwb("BW7", "673")


class TestVersions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.versies = wc.parse_manifest(fixture("manifest_BWBR0005290_ingekort.xml"), "BWBR0005290")

    def test_sorted(self):
        self.assertEqual([v.label for v in self.versies],
                         ["2015-07-01_0", "2016-01-01_1", "2016-04-01_0", "2026-07-01_0"])

    def test_pick_by_date(self):
        self.assertEqual(wc.kies_versie(self.versies, "2016-01-01").label, "2016-01-01_1")
        self.assertEqual(wc.kies_versie(self.versies, "2016-03-31").label, "2016-01-01_1")
        self.assertEqual(wc.kies_versie(self.versies, "2016-04-01").label, "2016-04-01_0")
        self.assertEqual(wc.kies_versie(self.versies, "2030-01-01").label, "2026-07-01_0")

    def test_pick_errors(self):
        with self.assertRaises(wc.WetError) as ctx:
            wc.kies_versie(self.versies, "2001-01-01")
        self.assertIn("versies vanaf 2015-07-01", str(ctx.exception))
        with self.assertRaises(wc.WetError):
            wc.kies_versie(self.versies, "2020-01-01")  # gap in this trimmed manifest
        with self.assertRaises(wc.WetError):
            wc.kies_versie(self.versies, "2016-02-30")
        with self.assertRaises(wc.WetError):
            wc.kies_versie(self.versies, "1-1-2016")


class TestArticleParsing(unittest.TestCase):
    def test_bw7_673_leden(self):
        root = ET.fromstring(fixture(BW7_XML))
        art = wc.parse_artikel(wc.find_artikel(root, "673"))
        self.assertEqual(art["kop"], "Artikel 673")
        self.assertEqual(art["leden"][0]["lid"], "1")
        lid2 = next(l for l in art["leden"] if l["lid"] == "2")
        self.assertTrue(lid2["tekst"].startswith("De transitievergoeding is voor elk jaar"))
        self.assertNotIn("Stb", lid2["tekst"])       # meta-data stripped
        self.assertFalse(art["vervallen"])

    def test_list_items(self):
        root = ET.fromstring(fixture(BW7_XML))
        art = wc.parse_artikel(wc.find_artikel(root, "669"))
        lid3 = next(l for l in art["leden"] if l["lid"] == "3")
        self.assertIn("\na. het vervallen van arbeidsplaatsen", lid3["tekst"])
        self.assertIn("\ne. verwijtbaar handelen of nalaten van de werknemer", lid3["tekst"])

    def test_awb_colon_numbers(self):
        root = ET.fromstring(fixture("BWBR0005537_2026-08-15_0_ingekort.xml"))
        art = wc.parse_artikel(wc.find_artikel(root, "8:1"))
        self.assertEqual(art["tekst"], "Een belanghebbende kan tegen een besluit beroep instellen bij de bestuursrechter.")
        self.assertIsNone(wc.find_artikel(root, "8:999"))

    def test_vervallen(self):
        root = ET.fromstring(fixture("BWBR0001827_2026-07-14_0_ingekort.xml"))
        art = wc.parse_artikel(wc.find_artikel(root, "843a"))
        self.assertTrue(art["vervallen"])


class TestFetchOffline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"NLJS_CACHE_DIR": self.tmp.name})
        self.env.start()
        wc._MANIFESTS.clear()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()
        wc._MANIFESTS.clear()

    def test_fetch_lid_and_cache(self):
        get = fake_get(BW7_ROUTES)
        with mock.patch.object(nl_http, "get", get):
            r = wc.fetch_artikel("art. 7:673 lid 2 BW", datum="2026-09-23")
            self.assertEqual([l["lid"] for l in r["leden"]], ["2"])
            self.assertEqual(r["versie"]["label"], "2026-07-01_0")
            self.assertIn("jci1.3:c:BWBR0005290&artikel=673&g=2026-09-23", r["url"])
            md = wc.render_artikel(r)
            self.assertIn("# Art. 7:673 lid 2 Burgerlijk Wetboek Boek 7", md)
            self.assertIn("**2.** De transitievergoeding", md)
            n_calls = len(get.calls)
            wc._MANIFESTS.clear()
            wc.fetch_artikel("art. 7:673 lid 1 BW", datum="2026-09-23")
        # second call: manifest again, toestand from the cache (manifest entry unchanged)
        self.assertEqual(len(get.calls), n_calls + 1)

    def test_missing_lid(self):
        with mock.patch.object(nl_http, "get", fake_get(BW7_ROUTES)):
            with self.assertRaises(wc.WetError) as ctx:
                wc.fetch_artikel("art. 7:673 lid 42 BW", datum="2026-09-23")
        self.assertIn("beschikbare leden", str(ctx.exception))

    def test_missing_article(self):
        with mock.patch.object(nl_http, "get", fake_get(BW7_ROUTES)):
            with self.assertRaises(wc.WetError) as ctx:
                wc.fetch_artikel("art. 7:9999 BW", datum="2026-09-23")
        self.assertIn("niet gevonden", str(ctx.exception))

    def test_cli(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(nl_http, "get", fake_get(BW7_ROUTES)), redirect_stdout(out), redirect_stderr(err):
            code = fetch_wet.main(["art. 7:669 lid 3 BW", "--datum", "2026-09-23"])
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("Onder een redelijke grond", out.getvalue())

    def test_cli_bad_citation(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = fetch_wet.main(["art. 6 AVG"])
        self.assertEqual(code, 1)
        self.assertIn("EU-verordening", err.getvalue())


class TestWti(unittest.TestCase):
    WTI = b"""<?xml version="1.0"?><wetstechnische-informatie><wijzigingen><regelingelementen>
<regelingelement label-id="1">
 <datum waarde="2015-07-01" label="Artikel 673"><details><betreft>nieuw</betreft>
  <ontstaansbron><bron><dossiernummer>33818</dossiernummer><bekendmaking soort="Stb" urlidentifier="stb-2014-216">
   <publicatiejaar>2014</publicatiejaar><publicatienummer>216</publicatienummer></bekendmaking></bron></ontstaansbron>
  <inwerkingtreding><bron><bekendmaking soort="Stb" urlidentifier="stb-2014-274"><publicatiejaar>2014</publicatiejaar>
   <publicatienummer>274</publicatienummer></bekendmaking></bron></inwerkingtreding>
  <opmerkingen><opmerking><al>Artikel XXII bevat overgangsrecht.</al></opmerking></opmerkingen></details></datum>
 <datum waarde="1997-04-01" label="Artikel 673"><details><betreft>nieuw</betreft></details></datum>
 <datum waarde="2015-07-01" label="Artikel 673a"><details><betreft>nieuw</betreft></details></datum>
</regelingelement></regelingelementen></wijzigingen></wetstechnische-informatie>"""

    def test_parse(self):
        entries = wc.parse_wti_artikel(self.WTI, "673")
        self.assertEqual([e["datum"] for e in entries], ["1997-04-01", "2015-07-01"])
        e = entries[1]
        self.assertEqual((e["betreft"], e["dossier"]), ("nieuw", "33818"))
        self.assertEqual(e["bron"]["citaat"], "Stb. 2014/216")
        self.assertEqual(e["inwerkingtreding"]["citaat"], "Stb. 2014/274")
        self.assertEqual(e["opmerkingen"], ["Artikel XXII bevat overgangsrecht."])
        self.assertEqual(e["bron"]["url"], "https://zoek.officielebekendmakingen.nl/stb-2014-216")


if __name__ == "__main__":
    unittest.main()
