"""Offline tests for scripts/termijnen.py.

Source of each expected value is given per test:
- "HR" = the date is stated in the ruling itself (fetched via data.rechtspraak.nl, see references/bronnen.md).
- "Stcrt" = follows from the text of a gelijkstellingsbesluit.
- "hand" = hand computation, steps written in the test docstring.
Run: python3 -m unittest discover -s skills/termijnen/tests
"""
import datetime as dt
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import termijnen as t  # noqa: E402

D = dt.date


class TestHogeRaadRegels(unittest.TestCase):
    def test_hr_2017_2225_voorbeelden(self):
        """HR 1-9-2017, ECLI:NL:HR:2017:2225 r.o. 3.4.3: uitspraak 28 feb (gewoon jaar) -> 28 mei,
        29 feb (schrikkeljaar) -> 29 mei, 30 april -> 30 juli, 30 september -> 30 december."""
        self.assertEqual(t.plus_maanden(D(2017, 2, 28), 3)[0], D(2017, 5, 28))
        self.assertEqual(t.plus_maanden(D(2016, 2, 29), 3)[0], D(2016, 5, 29))
        self.assertEqual(t.plus_maanden(D(2026, 4, 30), 3)[0], D(2026, 7, 30))
        self.assertEqual(t.plus_maanden(D(2026, 9, 30), 3)[0], D(2026, 12, 30))

    def test_hr_2004_ao1315(self):
        """HR 12-3-2004, ECLI:NL:HR:2004:AO1315: vonnis 29-11-2002, cassatietermijn eindigde 28-02-2003."""
        self.assertEqual(t.plus_maanden(D(2002, 11, 29), 3), (D(2003, 2, 28), True))

    def test_hr_2017_2225_atw_zondag(self):
        """HR 2017:2225 r.o. 3.1 (hof, in cassatie niet bestreden): 29-5-2016 was een zondag, termijn verlengd
        tot maandag 30-5-2016. Test-only data for 2016 (no Stcrt days needed: 30-5-2016 is a plain Monday)."""
        data = {"jaren": (2016, 2016), "extra": {}, "peildatum": "test"}
        stappen = []
        self.assertEqual(t.pas_atw_toe(D(2016, 3, 1), D(2016, 5, 29), data, stappen), D(2016, 5, 30))


class TestFeestdagen(unittest.TestCase):
    def setUp(self):
        self.data = t.load_data()

    def test_hemelvaart_volgt_uit_stcrt(self):
        """Stcrt: elk besluit stelt de vrijdag na Hemelvaart gelijk (2020-2028). Pasen + 39 dagen + 1 moet
        die vrijdag zijn; dat controleert de paasberekening voor alle gedekte jaren."""
        vrijdagen = {2020: D(2020, 5, 22), 2021: D(2021, 5, 14), 2022: D(2022, 5, 27), 2023: D(2023, 5, 19),
                     2024: D(2024, 5, 10), 2025: D(2025, 5, 30), 2026: D(2026, 5, 15), 2027: D(2027, 5, 7),
                     2028: D(2028, 5, 26)}
        for jaar, vr in vrijdagen.items():
            self.assertEqual(t.pasen(jaar) + dt.timedelta(days=40), vr, jaar)
            self.assertEqual(vr.weekday(), 4)
            self.assertIn(vr, self.data["extra"])

    def test_tabel_heeft_13_gelijkgestelde_dagen(self):
        """Stcrt 2019/53179 (3) + 2022/7812 (5) + 2025/24713 (5) = 13 dagen."""
        self.assertEqual(len(self.data["extra"]), 13)

    def test_jaar_buiten_tabel_weigert(self):
        with self.assertRaises(t.Weigering):
            t.feestdagen(2029, self.data)
        with self.assertRaises(t.Weigering):
            t.hoger_beroep_civiel(D(2019, 12, 20), False, self.data)
        with self.assertRaises(t.Weigering):
            t.bezwaar_beroep_awb(D(2028, 12, 1), self.data)


class TestTermijnen(unittest.TestCase):
    def setUp(self):
        self.data = t.load_data()

    def laatste(self, r):
        return dt.date.fromisoformat(r["laatste_dag"])

    def test_appel_31_januari(self):
        """hand: vonnis za 31-1-2026; april heeft geen 31 -> do 30-4-2026 (HR 2017:2225 r.o. 3.4.4);
        30-4-2026 is een donderdag, geen feestdag -> 30-4-2026."""
        self.assertEqual(self.laatste(t.hoger_beroep_civiel(D(2026, 1, 31), False, self.data)), D(2026, 4, 30))

    def test_appel_koningsdag(self):
        """hand: vonnis 27-1-2026 -> 27-4-2026 = maandag Koningsdag (art. 3 lid 1 Atw) -> di 28-4-2026."""
        self.assertEqual(self.laatste(t.hoger_beroep_civiel(D(2026, 1, 27), False, self.data)), D(2026, 4, 28))

    def test_appel_hemelvaart_en_brugdag(self):
        """hand: vonnis 14-2-2026 -> 14-5-2026 = Hemelvaart (Pasen 5-4 + 39); 15-5 gelijkgesteld
        (Stcrt 2025/24713); 16-17 mei weekend -> ma 18-5-2026."""
        self.assertEqual(self.laatste(t.hoger_beroep_civiel(D(2026, 2, 14), False, self.data)), D(2026, 5, 18))

    def test_kort_geding_tweede_paasdag(self):
        """hand: vonnis ma 9-3-2026 + 28 dagen = ma 6-4-2026 = tweede Paasdag -> di 7-4-2026."""
        self.assertEqual(self.laatste(t.hoger_beroep_civiel(D(2026, 3, 9), True, self.data)), D(2026, 4, 7))

    def test_cassatie_2_januari(self):
        """hand: arrest 2-10-2025 -> 2-1-2026 = gelijkgestelde dag (Stcrt 2025/24713); 3-4 jan weekend
        -> ma 5-1-2026."""
        self.assertEqual(self.laatste(t.cassatie_civiel(D(2025, 10, 2), False, self.data)), D(2026, 1, 5))

    def test_cassatie_kort_geding_acht_weken(self):
        """hand: art. 402 lid 2 Rv, 2 x 4 weken = 56 dagen. Uitspraak di 3-2-2026 + 56 = di 31-3-2026."""
        self.assertEqual(self.laatste(t.cassatie_civiel(D(2026, 2, 3), True, self.data)), D(2026, 3, 31))

    def test_awb_vrijdag(self):
        """hand: bekendmaking vr 24-4-2026; dag 1 = za 25-4 (art. 6:8 lid 1 Awb); 42 dagen -> vr 5-6-2026."""
        self.assertEqual(self.laatste(t.bezwaar_beroep_awb(D(2026, 4, 24), self.data)), D(2026, 6, 5))

    def test_straf_kerst(self):
        """hand: vonnis vr 11-12-2026 + 14 = vr 25-12 (Kerst) -> za 26, zo 27 -> ma 28-12-2026."""
        self.assertEqual(self.laatste(t.hoger_beroep_straf(D(2026, 12, 11), self.data)), D(2026, 12, 28))

    def test_art_2_atw(self):
        """hand: 3 dagen na do 24-12-2026: dag 1 = vr 25 (Kerst), 26 za, 27 zo = einde -> art. 1: ma 28.
        Werkdagen in 25..28: alleen 28 = 1 < 2 -> art. 2 Atw: verlengen tot di 29-12-2026."""
        r = t.generiek(D(2026, 12, 24), 3, "dagen", True, self.data)
        self.assertEqual(self.laatste(r), D(2026, 12, 29))
        self.assertTrue(any("Art. 2 Atw" in s for s in r["stappen"]))

    def test_art_4_atw_geen_verlenging(self):
        """hand: 4 maanden na 6-2-2026 = za 6-6-2026; art. 4 onder a Atw (meer dan drie maanden): geen verlenging."""
        self.assertEqual(self.laatste(t.generiek(D(2026, 2, 6), 4, "maanden", True, self.data)), D(2026, 6, 6))

    def test_generiek_zonder_atw(self):
        """hand: 10 dagen na 1-5-2026 = 11-5-2026 (maandag); zonder --wettelijk geen Atw. En 7 dagen na
        vr 1-5-2026 = vr 8-5-2026."""
        self.assertEqual(self.laatste(t.generiek(D(2026, 5, 1), 10, "dagen", False, self.data)), D(2026, 5, 11))
        self.assertEqual(self.laatste(t.generiek(D(2026, 5, 1), 7, "dagen", False, self.data)), D(2026, 5, 8))


class TestBlindVerificatie(unittest.TestCase):
    """Independent blind-test cases (test-reports/blind/termijnen.md). Expected values derived by hand
    from art. 339/402 Rv, art. 6:8 Awb, art. 408 Sv, art. 1-4 Atw (BWBR0002448), Stcrt. 2022/7812 and
    2025/24713, and HR 1-9-2017, ECLI:NL:HR:2017:2225 r.o. 3.4.3-3.4.4."""

    def setUp(self):
        self.data = t.load_data()

    def eind(self, r):
        return dt.date.fromisoformat(r["laatste_dag"])

    def test_blind_cases(self):
        cases = [
            (t.hoger_beroep_civiel(D(2024, 1, 31), False, self.data), D(2024, 4, 30)),  # geen 31 april
            (t.hoger_beroep_civiel(D(2024, 2, 29), False, self.data), D(2024, 5, 29)),  # HR 2017:2225: niet 31 mei
            (t.hoger_beroep_civiel(D(2023, 8, 30), False, self.data), D(2023, 11, 30)),
            (t.bezwaar_beroep_awb(D(2026, 4, 2), self.data), D(2026, 5, 18)),  # Hemelvaart + 15-5 gelijkgesteld
            (t.bezwaar_beroep_awb(D(2026, 3, 16), self.data), D(2026, 4, 28)),  # Koningsdag ma 27-4
            (t.hoger_beroep_civiel(D(2025, 11, 28), True, self.data), D(2025, 12, 29)),  # 2e Kerstdag vr
            (t.hoger_beroep_civiel(D(2025, 6, 13), False, self.data), D(2025, 9, 15)),  # zaterdag
            (t.hoger_beroep_civiel(D(2025, 12, 4), True, self.data), D(2026, 1, 5)),  # 1-1 + 2-1 gelijkgesteld
            (t.bezwaar_beroep_awb(D(2025, 3, 24), self.data), D(2025, 5, 6)),  # 5 mei (ook buiten lustrum)
        ]
        for r, verwacht in cases:
            self.assertEqual(self.eind(r), verwacht, r["stappen"])

    def test_weken_weekdag_tekst(self):
        """Blind test found the text 'zelfde weekdag als de startdatum' was wrong: 4 weeks after vr 28-11-2025
        ends on vr 26-12, which is the weekday of the uitspraak, not of dag 1 (za 29-11)."""
        r = t.hoger_beroep_civiel(D(2025, 11, 28), True, self.data)
        self.assertIn("zelfde weekdag als vrijdag 28 november 2025", r["stappen"][0])


class TestCli(unittest.TestCase):
    def run_cli(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = t.main(argv)
        return code, buf.getvalue()

    def test_tekst_uitvoer_bevat_verplichte_onderdelen(self):
        code, out = self.run_cli(["hoger-beroep-civiel", "--uitspraak", "2026-01-31"])
        self.assertEqual(code, 0)
        for stuk in ["Uitkomst:", "Berekening:", "Juridische grondslag:", t.DISCLAIMER, "2026-04-30"]:
            self.assertIn(stuk, out)

    def test_json(self):
        code, out = self.run_cli(["bezwaar-beroep-awb", "--bekendmaking", "2026-04-24", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["laatste_dag"], "2026-06-05")

    def test_weigering(self):
        code, out = self.run_cli(["hoger-beroep-civiel", "--uitspraak", "2030-01-10"])
        self.assertEqual(code, 2)
        self.assertIn("Geen berekening", out)
        self.assertIn(t.DISCLAIMER, out)
        code, out = self.run_cli(["hoger-beroep-civiel", "--uitspraak", "31-01-2026"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
