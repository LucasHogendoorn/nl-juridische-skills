"""Offline tests for tuchtrecht (recorded KOOP SRU fixtures, no network).

Run from the repository root:
    python3 -m unittest discover -s skills/tuchtrecht/tests
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import koop_sru_client as k  # noqa: E402
import tuchtrecht as tr  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def fixture(name):
    with open(os.path.join(FIX, name), "rb") as fh:
        return fh.read()


class TestQuery(unittest.TestCase):
    def test_advocaten_datum(self):
        q = tr.bouw_zoekvraag(["belangenverstrengeling"], domein="advocaat", van="2024-01-01",
                              tot="2024-12-31")
        self.assertIn('c.product-area=="tuchtrecht"', q)
        self.assertIn('w.instantieDomein=="Advocaten"', q)
        self.assertIn('cql.textAndIndexes="belangenverstrengeling"', q)
        self.assertIn("w.uitspraakdatum>=2024-01-01 AND w.uitspraakdatum<=2024-12-31", q)
        self.assertTrue(q.endswith("sortBy w.uitspraakdatum/sort.descending"))

    def test_huisarts_maps_to_arts_plus_word(self):
        q = tr.bouw_zoekvraag(["dossiervoering"], beroep="huisarts")
        self.assertIn('w.instantieDomein=="Gezondheidszorg"', q)
        self.assertIn('(dt.description="huisarts" OR (w.beroepsgroep=="Arts" AND '
                      'cql.textAndIndexes="huisarts"))', q)

    def test_beroep_field_or_word(self):
        # decisions after ±2021 have no w.beroepsgroep: the word must also be accepted
        q = tr.bouw_zoekvraag(["implantaat"], beroep="tandarts")
        self.assertIn('(dt.description="tandarts" OR w.beroepsgroep=="Tandarts")', q)
        q = tr.bouw_zoekvraag([], beroep="gz-psycholoog")
        self.assertIn('dt.description="psycholoog"', q)

    def test_strikt_and_onderwerp_and_uitkomst(self):
        q = tr.bouw_zoekvraag(["zorgplicht"], domein="notaris", strikt=True, onderwerp="Belangenconflict",
                              uitkomst="berisping", sorteer="relevantie")
        self.assertIn('dt.description="zorgplicht"', q)
        self.assertIn('(w.subonderwerp="Belangenconflict" OR dt.subject="Belangenconflict")', q)
        self.assertIn('(w.beslissing="berisping" OR dt.description="berisping")', q)
        self.assertNotIn("sortBy", q)

    def test_bad_values(self):
        with self.assertRaises(SystemExit):
            tr.bouw_zoekvraag([], domein="bakkers")
        with self.assertRaises(SystemExit):
            tr.bouw_zoekvraag([], beroep="kapper")
        with self.assertRaises(SystemExit):
            tr.bouw_zoekvraag(["x"], van="1-1-2024")


class TestParse(unittest.TestCase):
    def test_advocaten_record(self):
        res = k.parse_response(fixture("sru_tuchtrecht.xml"))
        self.assertGreater(res.total, 100)
        r = res.records[0]
        self.assertEqual(r.identifier, "ECLI:NL:TADRSHE:2011:YA2031")
        self.assertEqual(r.date, "2011-09-19")  # uitspraakdatum, not publication date
        self.assertEqual(r.get("instantieDomein"), "Advocaten")
        self.assertEqual(r.get("subonderwerp"), "Belangenconflict")
        self.assertIn("belangenverstrengeling", r.descriptions[0])
        self.assertEqual(r.preferred_url, "https://tuchtrecht.overheid.nl/ECLI:NL:TADRSHE:2011:YA2031")
        regel = tr.regel(r, 1)
        self.assertIn("**ECLI:NL:TADRSHE:2011:YA2031**", regel)
        self.assertIn("Belangenconflict", regel)

    def test_gezondheidszorg_record(self):
        r = k.parse_response(fixture("sru_gezondheidszorg.xml")).records[0]
        self.assertEqual(r.get("beroepsgroep"), "Arts")
        self.assertEqual(r.get("beslissing"), "Ongegrond/afwijzing")
        self.assertIn("beslissing: Ongegrond/afwijzing", tr.regel(r, 1))

    def test_diagnostic(self):
        with self.assertRaises(k.SruError):
            k.parse_response(fixture("sru_diagnostic.xml"))

    def test_uitspraak_markdown(self):
        md = k.uitspraak_to_markdown(fixture("uitspraak.xml"))
        self.assertTrue(md.startswith("# ECLI:NL:TADRSHE:2011:YA2031"))
        self.assertIn("**Uitspraakdatum:** 19-09-2011", md)
        self.assertIn("Wat een behoorlijk advocaat betaamt — Belangenconflict", md)
        self.assertIn("## Inhoudsindicatie", md)
        self.assertIn("## Uitspraak", md)
        self.assertIn("1. Verloop van de procedure", md)


class TestCli(unittest.TestCase):
    def test_zoek_offline(self):
        body = fixture("sru_tuchtrecht.xml")
        with mock.patch.object(k.nl_http, "get", return_value=mock.Mock(body=body)):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = tr.main(["zoek", "belangenverstrengeling", "--domein", "advocaten", "-n", "2"])
        self.assertEqual(rc, 0)
        self.assertIn("ECLI:NL:TADRSHE:2011:YA2031", buf.getvalue())

    def test_haal_rejects_non_ecli(self):
        buf = io.StringIO()
        with mock.patch("sys.stderr", buf):
            self.assertEqual(tr.main(["haal", "33818"]), 2)


if __name__ == "__main__":
    unittest.main()
