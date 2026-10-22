"""Offline tests for scripts/wettelijke_rente.py.

Rates: data/rentetabel.json (source per row). Expected amounts are hand computations; the steps are in
each docstring (rente = grondslag x percentage x dagen / 365, per segment afgerond op centen).
Run: python3 -m unittest discover -s skills/wettelijke-rente/tests
"""
import datetime as dt
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import wettelijke_rente as wr  # noqa: E402

D = dt.date
E = Decimal


class TestTabel(unittest.TestCase):
    def setUp(self):
        self.t = wr.load_tabel()

    def test_niet_handel_percentages(self):
        """Stb. per rij (zie bronnen.md): 2002 7%, 8-2003 5%, 2-2004 4%, 2007 6%, 7-2009 4%, 2010 3%, 7-2011 4%,
        7-2012 3%, 2015 2%, 2023 4%, 7-2023 6%, 2024 7%, 2025 6%, 2026 4%."""
        verwacht = {D(2002, 6, 1): 7, D(2003, 8, 1): 5, D(2005, 1, 1): 4, D(2008, 1, 1): 6, D(2009, 7, 1): 4,
                    D(2010, 1, 1): 3, D(2011, 7, 1): 4, D(2013, 1, 1): 3, D(2022, 12, 31): 2, D(2023, 1, 1): 4,
                    D(2023, 7, 1): 6, D(2024, 6, 1): 7, D(2025, 6, 1): 6, D(2026, 9, 23): 4}
        for d, p in verwacht.items():
            self.assertEqual(wr.tarief(self.t["niet-handel"], d)[1], E(p), d)

    def test_handelsrente_actueel(self):
        """rijksoverheid.nl (gelezen 23-9-2026): handelsrente sinds 1 juli 2026 10,4%."""
        self.assertEqual(wr.tarief(self.t["handel"], D(2026, 9, 23))[1], E("10.4"))

    def test_handelsrente_formule(self):
        """Art. 6:120 lid 2 BW: ECB-MRO + 8. Elke rij: pct == ecb_mro + 8."""
        with open(wr.DATA_FILE, encoding="utf-8") as fh:
            for r in json.load(fh)["handel"]:
                self.assertEqual(E(r["pct"]), E(r["ecb_mro"]) + 8, r["vanaf"])


class TestBerekening(unittest.TestCase):
    def test_schrikkeljaar_dagbasis(self):
        """hand: 10.000 x 7% x 366/365 (2024) = 701,9178 -> 701,92; met dagbasis 'jaar' 700,00."""
        r = wr.bereken("niet-handel", E(10000), D(2024, 1, 1), D(2024, 12, 31))
        self.assertEqual(r["totaal_rente_berekend"], "701.92")
        r = wr.bereken("niet-handel", E(10000), D(2024, 1, 1), D(2024, 12, 31), dagbasis="jaar")
        self.assertEqual(r["totaal_rente_berekend"], "700.00")

    def test_kapitalisatie(self):
        """hand: 10.000 vanaf 1-1-2025. Jaar 1 (2025, 6%): 600,00; grondslag 10.600.
        Jaar 2 (2026, 4%): 10.600 x 4% = 424,00. Totaal 1.024,00 (art. 6:119 lid 2 BW)."""
        r = wr.bereken("niet-handel", E(10000), D(2025, 1, 1), D(2026, 12, 31))
        self.assertEqual(r["totaal_rente_berekend"], "1024.00")

    def test_zonder_kapitalisatie_binnen_jaar(self):
        """hand: 1.000 van 1-7-2025 t/m 30-6-2026: 184 d x 6% = 30,2466 -> 30,25 (1-7 t/m 31-12-2025);
        181 d x 4% = 19,8356 -> 19,84 (1-1 t/m 30-6-2026). Totaal 50,09."""
        r = wr.bereken("niet-handel", E(1000), D(2025, 7, 1), D(2026, 6, 30))
        self.assertEqual(r["totaal_rente_berekend"], "50.09")

    def test_handelsrente_halfjaar(self):
        """hand: 10.000 x 12,25% x 184/365 (1-7 t/m 31-12-2024) = 617,5342 -> 617,53."""
        r = wr.bereken("handel", E(10000), D(2024, 7, 1), D(2024, 12, 31), overeenkomst=D(2024, 1, 15))
        self.assertEqual(r["totaal_rente_berekend"], "617.53")

    def test_handelsrente_2013(self):
        """hand: 10.000 van 16-3-2013 t/m 30-6-2013: 107 d x 8,75% = 256,5068 -> 256,51;
        1-7 t/m 31-12-2013: 184 d x 8,5% = 428,4932 -> 428,49. Totaal 685,00."""
        r = wr.bereken("handel", E(10000), D(2013, 3, 16), D(2013, 12, 31), overeenkomst=D(2013, 3, 16))
        self.assertEqual(r["totaal_rente_berekend"], "685.00")

    def test_deelbetaling_met_kosten(self):
        """hand: 10.000, kosten 500, 1-1 t/m 31-12-2026 (4%). Tot 30-6: 181 d -> 198,3562 -> 198,36.
        Betaling 2.000 op 30-6: kosten 500, rente 198,36, hoofdsom 1.301,64 -> hoofdsom 8.698,36.
        1-7 t/m 31-12: 184 d x 8.698,36 x 4% / 365 = 175,3971 -> 175,40. Open: 8.698,36 + 175,40 = 8.873,76."""
        r = wr.bereken("niet-handel", E(10000), D(2026, 1, 1), D(2026, 12, 31), kosten=E(500),
                       betalingen=[(D(2026, 6, 30), E(2000))])
        self.assertEqual(r["open_hoofdsom"], "8698.36")
        self.assertEqual(r["open_rente"], "175.40")
        self.assertEqual(r["open_kosten"], "0.00")
        self.assertEqual(r["totaal_open"], "8873.76")

    def test_incasso_2019_2026(self):
        """hand (volledige stappen in test-reports/wettelijke-rente.md): 12.500 vanaf 1-3-2019 t/m 1-3-2026,
        kosten 875, betaling 5.000 op 15-6-2022. Rente totaal 2.798,78; open hoofdsom 9.218,58,
        open rente 1.955,20, totaal 11.173,78."""
        r = wr.bereken("niet-handel", E(12500), D(2019, 3, 1), D(2026, 3, 1), kosten=E(875),
                       betalingen=[(D(2022, 6, 15), E(5000))])
        self.assertEqual(r["totaal_rente_berekend"], "2798.78")
        self.assertEqual(r["open_hoofdsom"], "9218.58")
        self.assertEqual(r["open_rente"], "1955.20")
        self.assertEqual(r["totaal_open"], "11173.78")


class TestBlindVerificatie(unittest.TestCase):
    """Independent blind-test cases (test-reports/blind/wettelijke-rente.md). Rates verified by the tester in
    BWB-toestanden BWBR0047640 (2023-2026) and BWBR0002744 (2002-2022) and the ECB MRR_FR series; interest
    per day = pct/365, interest day range inclusive, annual capitalisation on the anniversary of vanaf.
    Hand values computed day by day; the skill rounds per segment, so a 1 cent difference is accepted."""

    def near(self, got, exp):
        self.assertLessEqual(abs(E(got) - E(exp)), E("0.01"), (got, exp))

    def test_blind_cases(self):
        nh, h = "niet-handel", "handel"
        cases = [
            (nh, 10000, D(2025, 3, 1), D(2025, 8, 31), None, (), "302.47"),     # 184 d x 6%
            (nh, 5000, D(2024, 10, 1), D(2025, 3, 31), None, (), "162.19"),     # 92 d 7% + 90 d 6%
            (nh, 20000, D(2023, 6, 1), D(2025, 5, 31), None, (), "2653.53"),    # 4/6/7/6%, kapitalisatie 1-6-2024
            (h, 8000, D(2025, 4, 1), D(2025, 9, 30), D(2025, 1, 15), (), "427.06"),   # 11,15% / 10,15%
            (nh, 1000, D(2025, 12, 15), D(2026, 3, 14), None, (), "10.79"),     # 6% -> 4%
            (h, 15000, D(2026, 5, 1), D(2026, 8, 31), D(2026, 1, 10), (), "519.43"),  # 10,15% -> 10,40% (MRO 2,40)
            (h, 50000, D(2023, 3, 15), D(2025, 9, 14), D(2022, 11, 1), (), "15993.24"),  # 2x kapitalisatie
        ]
        for soort, hs, van, tot, ovk, bet, verwacht in cases:
            r = wr.bereken(soort, E(hs), van, tot, betalingen=bet, overeenkomst=ovk)
            self.near(r["totaal_rente_berekend"], verwacht)

    def test_blind_deelbetaling(self):
        """10.000 vanaf 1-1-2025, betaling 3.000 op 1-7-2025, t/m 31-12-2025. Rente t/m de betaaldag
        (182 d, zoals art. 6:119a lid 1 'tot en met de dag waarop ... voldaan'): 299,18; hoofdsom 7.299,18;
        183 d x 6% = 219,58; open 7.518,76. (Tester's own first derivation stopped interest the day before
        payment: 7.518,26; convention difference, not an error.)"""
        r = wr.bereken("niet-handel", E(10000), D(2025, 1, 1), D(2025, 12, 31),
                       betalingen=[(D(2025, 7, 1), E(3000))])
        self.assertEqual(r["totaal_open"], "7518.76")

    def test_ecb_sinds_datum_klopt(self):
        """Blind test found wrong 'ecb_mro_sinds' labels (2015-12-09, 2019-09-18 are deposit-rate dates);
        the MRO was 0,05% from 2014-09-10 and 0% from 2016-03-16 (ECB MRR_FR)."""
        with open(wr.DATA_FILE, encoding="utf-8") as fh:
            rows = {r["vanaf"]: r for r in json.load(fh)["handel"]}
        self.assertEqual(rows["2016-01-01"]["ecb_mro_sinds"], "2014-09-10")
        for v in ("2020-01-01", "2020-07-01", "2021-01-01", "2021-07-01", "2022-01-01", "2022-07-01"):
            self.assertEqual(rows[v]["ecb_mro_sinds"], "2016-03-16", v)


class TestWeigeringen(unittest.TestCase):
    def test_handel_oude_overeenkomst(self):
        with self.assertRaises(wr.Weigering):
            wr.bereken("handel", E(1000), D(2014, 1, 1), D(2014, 6, 30), overeenkomst=D(2012, 5, 1))

    def test_handel_zonder_overeenkomstdatum(self):
        with self.assertRaises(wr.Weigering):
            wr.bereken("handel", E(1000), D(2024, 1, 1), D(2024, 6, 30))

    def test_te_vroeg_en_te_laat(self):
        with self.assertRaises(wr.Weigering):
            wr.bereken("niet-handel", E(1000), D(2001, 6, 1), D(2002, 6, 30))
        with self.assertRaises(wr.Weigering):
            wr.bereken("niet-handel", E(1000), D(2026, 1, 1), D(2027, 1, 1))

    def test_te_hoge_betaling(self):
        with self.assertRaises(wr.Weigering):
            wr.bereken("niet-handel", E(1000), D(2026, 1, 1), D(2026, 6, 30), betalingen=[(D(2026, 3, 1), E(5000))])

    def test_betaling_buiten_periode(self):
        with self.assertRaises(wr.Weigering):
            wr.bereken("niet-handel", E(1000), D(2026, 1, 1), D(2026, 6, 30), betalingen=[(D(2026, 7, 1), E(10))])


class TestCli(unittest.TestCase):
    def test_uitvoer(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = wr.main(["--soort", "niet-handel", "--hoofdsom", "10000", "--vanaf", "2025-01-01",
                            "--tot", "2026-12-31"])
        out = buf.getvalue()
        self.assertEqual(code, 0)
        for stuk in ["Uitkomst:", "Berekening:", "Juridische grondslag:", wr.DISCLAIMER, "1.024,00"]:
            self.assertIn(stuk, out)

    def test_json_weigering(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = wr.main(["--soort", "handel", "--hoofdsom", "100", "--vanaf", "2012-01-01", "--tot", "2012-12-31",
                            "--overeenkomst-datum", "2011-01-01", "--json"])
        self.assertEqual(code, 2)
        self.assertIn("fout", json.loads(buf.getvalue()))


if __name__ == "__main__":
    unittest.main()
