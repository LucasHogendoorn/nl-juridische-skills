import csv
import io
import os
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import docx_naar_tekst as dx  # noqa: E402
import naar_csv as nc  # noqa: E402

GOOD = """# Chronologie

## Stukken
| Code | Datum stuk | Soort |
|---|---|---|
| D1 | 2024-01-15 | brief |

## Chronologie
| # | Datum | Gebeurtenis | Bron | Status | Juridische relevantie |
|---|-------|-------------|------|--------|-----------------------|
| 1 | 2024-01 | Opdracht \\| offerte getekend. | D1, punt 1 | vaststaand | |
| 2 | ± 2024-02-01 (afgeleid: "volgende week" in D2 van 2024-01-25) | Levering. | D2, alinea 3 | stelling Jansen — betwist (D3, alinea 2) | Verzuim? |
| 3 | 2024-02-10 09:15 | Klacht per e-mail. | D3, e-mail 10-02-2024 | stelling Jansen — onbetwist | art. 6:89 BW |
| 4 | 2024-03-01 – 2024-03-31 | Werkzaamheden. | D4, p. 2 | vaststaand | |
| 5 | onbekend | Mondelinge toezegging. | D5, r. 4 | stelling Jansen | |
"""


class NaarCsvTest(unittest.TestCase):
    def test_finds_chronology_table_not_stukkenlijst(self):
        header, rows = nc.find_table(GOOD)
        self.assertEqual(header[1], "Datum")
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0][2], "Opdracht | offerte getekend.")  # escaped pipe kept as text

    def test_good_table_passes(self):
        errors, warnings = nc.check(*nc.find_table(GOOD))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_source_is_error(self):
        bad = GOOD.replace("| D1, punt 1 |", "|  |")
        errors, _ = nc.check(*nc.find_table(bad))
        self.assertTrue(any("geen bron" in e for e in errors))

    def test_dutch_date_format_is_error(self):
        bad = GOOD.replace("| 2024-02-10 09:15 |", "| 10 februari 2024 |")
        errors, _ = nc.check(*nc.find_table(bad))
        self.assertTrue(any("datum '10 februari 2024'" in e for e in errors))

    def test_estimated_date_without_afgeleid_is_error(self):
        bad = GOOD.replace('(afgeleid: "volgende week" in D2 van 2024-01-25)', "")
        errors, _ = nc.check(*nc.find_table(bad))
        self.assertTrue(any("Rij 2" in e and "afgeleid" in e for e in errors))

    def test_unknown_status_is_error(self):
        bad = GOOD.replace("| vaststaand | |\n| 2", "| waarschijnlijk | |\n| 2")
        errors, _ = nc.check(*nc.find_table(bad))
        self.assertTrue(any("status 'waarschijnlijk'" in e for e in errors))

    def test_betwist_without_source_warns(self):
        bad = GOOD.replace("betwist (D3, alinea 2)", "betwist")
        errors, warnings = nc.check(*nc.find_table(bad))
        self.assertEqual(errors, [])
        self.assertTrue(any("betwist" in w for w in warnings))

    def test_bare_document_code_warns(self):
        bad = GOOD.replace("| D1, punt 1 |", "| D1 |")
        errors, warnings = nc.check(*nc.find_table(bad))
        self.assertEqual(errors, [])
        self.assertTrue(any("alleen het stuk" in w for w in warnings))

    def test_unsorted_warns(self):
        bad = GOOD.replace("| 2024-02-10 09:15 |", "| 2023-12-01 |")
        _, warnings = nc.check(*nc.find_table(bad))
        self.assertTrue(any("Rij 3" in w and "gesorteerd" in w for w in warnings))

    def test_no_table(self):
        errors, _ = nc.check(*nc.find_table("geen tabel"))
        self.assertTrue(errors)

    def test_csv_output_for_dutch_excel(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = os.path.join(d, "c.md"), os.path.join(d, "c.csv")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(GOOD)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(nc.main([src, "-o", out]), 0)
            raw = open(out, "rb").read()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))  # BOM for Excel
            rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
            self.assertEqual(rows[0][:4], ["#", "Datum", "Gebeurtenis", "Bron"])
            self.assertEqual(len(rows), 6)

    def test_controleer_exit_code(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "c.md")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(GOOD.replace("| D1, punt 1 |", "|  |"))
            with redirect_stdout(io.StringIO()):
                self.assertEqual(nc.main([src, "--controleer"]), 1)


DOC_XML = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:r><w:t>Zutphen, 3 juni 2024</w:t></w:r></w:p>
<w:p></w:p>
<w:p><w:r><w:t xml:space="preserve">Wij stellen u </w:t></w:r><w:r><w:t>in gebreke.</w:t></w:r><w:del><w:r><w:delText>weg</w:delText></w:r></w:del></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Factuur</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>EUR 100</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
</w:body></w:document>"""


class DocxTest(unittest.TestCase):
    def test_paragraphs_numbered_and_tables_flattened(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.docx")
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("word/document.xml", DOC_XML)
            self.assertEqual(dx.docx_paragraphs(path),
                             ["Zutphen, 3 juni 2024", "Wij stellen u in gebreke.", "Factuur | EUR 100"])
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(dx.main([path]), 0)
            self.assertIn("[2] Wij stellen u in gebreke.", buf.getvalue())

    def test_not_a_docx(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.docx")
            with open(path, "w") as fh:
                fh.write("geen zip")
            with self.assertRaises(ValueError):
                dx.docx_paragraphs(path)


class ExampleTest(unittest.TestCase):
    def test_worked_example_passes_controle(self):
        path = os.path.join(os.path.dirname(__file__), "..", "examples", "chronologie-voorbeeld.md")
        with open(path, encoding="utf-8") as fh:
            errors, warnings = nc.check(*nc.find_table(fh.read()))
        self.assertEqual((errors, warnings), ([], []))


if __name__ == "__main__":
    unittest.main()
