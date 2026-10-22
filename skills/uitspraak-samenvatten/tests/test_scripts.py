import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import controleer_citaten as cc  # noqa: E402
import haal_uitspraak as hu  # noqa: E402
import rechtspraak_client as rc  # noqa: E402

# Invented ruling in the open-data XML shape (not a real case).
XML = """<?xml version="1.0" encoding="utf-8"?>
<open-rechtspraak>
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dcterms="http://purl.org/dc/terms/"
   xmlns:psi="http://psi.rechtspraak.nl/">
  <rdf:Description>
   <dcterms:identifier>ECLI:NL:HR:2099:1</dcterms:identifier>
   <dcterms:creator>Hoge Raad</dcterms:creator>
   <dcterms:date>2099-01-01</dcterms:date>
   <psi:zaaknummer>99/00001</psi:zaaknummer>
  </rdf:Description>
 </rdf:RDF>
 <inhoudsindicatie><para>Verzonnen testzaak over uitleg.</para></inhoudsindicatie>
 <uitspraak>
  <section><title>3 Beoordeling</title>
   <paragroup><nr>3.1</nr><para>Het hof heeft in rov. 4.2 geoordeeld dat de tekst duidelijk is.</para></paragroup>
   <paragroup><nr>3.2</nr><para>Dat oordeel geeft blijk van een onjuiste rechtsopvatting.</para></paragroup>
  </section>
 </uitspraak>
</open-rechtspraak>
""".encode("utf-8")


class HaalUitspraakTest(unittest.TestCase):
    def setUp(self):
        self._orig = rc.fetch_ecli_xml
        rc.fetch_ecli_xml = lambda ecli, meta_only=False: XML

    def tearDown(self):
        rc.fetch_ecli_xml = self._orig

    def test_markdown_keeps_ro_numbers(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = hu.main(["ECLI:NL:HR:2099:1"])
        out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("**3.2** Dat oordeel geeft blijk", out)
        self.assertIn("Hoge Raad", out)
        self.assertIn("Verzonnen testzaak", out)

    def test_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "u.md")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(hu.main(["ECLI:NL:HR:2099:1", "-o", path]), 0)
            with open(path, encoding="utf-8") as fh:
                self.assertIn("**3.1**", fh.read())

    def test_invalid_ecli(self):
        rc.fetch_ecli_xml = self._orig  # real validation, no network for invalid input
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(hu.main(["geen-ecli"]), 1)
        self.assertIn("Geen geldige ECLI", err.getvalue())


class ControleerCitatenTest(unittest.TestCase):
    SRC = "**3.2** Dat oordeel geeft blijk van een  onjuiste\nrechtsopvatting. Het hof heeft ’s middags beslist."

    def test_found_with_whitespace_and_bold(self):
        res = cc.check('r.o. 3.2: "Dat oordeel geeft blijk van een onjuiste rechtsopvatting."', self.SRC)
        self.assertEqual(res, [("Dat oordeel geeft blijk van een onjuiste rechtsopvatting.", True)])

    def test_curly_quotes_and_apostrophe(self):
        res = cc.check("“Het hof heeft 's middags beslist”", self.SRC)
        self.assertTrue(res[0][1])

    def test_not_found_when_altered(self):
        res = cc.check('"Dat oordeel geeft blijk van een juiste rechtsopvatting"', self.SRC)
        self.assertFalse(res[0][1])

    def test_dutch_low_high_quotes(self):
        # „...” is the usual Dutch quotation style; it must be checked, not skipped.
        ok = cc.check("„Dat oordeel geeft blijk van een onjuiste rechtsopvatting”", self.SRC)
        self.assertEqual(ok, [("Dat oordeel geeft blijk van een onjuiste rechtsopvatting", True)])
        bad = cc.check('„Dat oordeel geeft blijk van een juiste rechtsopvatting"', self.SRC)
        self.assertFalse(bad[0][1])

    def test_footnote_marker_in_source_ignored(self):
        src = "**3.1** Volgens vaste rechtspraak geldt die maatstaf.[^2] Deze maatstaf geldt niet."
        res = cc.check('"Volgens vaste rechtspraak geldt die maatstaf. Deze maatstaf"', src)
        self.assertTrue(res[0][1])

    def test_short_quotes_ignored(self):
        self.assertEqual(cc.check('"drie korte woorden"', self.SRC), [])

    def test_main_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            s, u = os.path.join(d, "s.md"), os.path.join(d, "u.md")
            with open(u, "w", encoding="utf-8") as fh:
                fh.write(self.SRC)
            with open(s, "w", encoding="utf-8") as fh:
                fh.write('"Dat oordeel geeft blijk van een onjuiste rechtsopvatting"')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cc.main([s, u]), 0)
            with open(s, "w", encoding="utf-8") as fh:
                fh.write('"Dit staat nergens in de uitspraak"')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cc.main([s, u]), 1)


if __name__ == "__main__":
    unittest.main()
