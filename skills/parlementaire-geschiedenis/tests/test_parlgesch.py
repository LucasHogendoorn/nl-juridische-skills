"""Offline tests for parlementaire-geschiedenis (recorded KOOP SRU fixtures, no network).

Run from the repository root:
    python3 -m unittest discover -s skills/parlementaire-geschiedenis/tests
"""
import os
import sys
import unittest
import zlib
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import koop_sru_client as k  # noqa: E402
import parlgesch as pg  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def fixture(name):
    with open(os.path.join(FIX, name), "rb") as fh:
        return fh.read()


class TestCql(unittest.TestCase):
    def test_quote_escapes(self):
        self.assertEqual(k.cql_quote('a "b"'), '"a \\"b\\""')

    def test_clause_and_skip_empty(self):
        q = k.cql_and(k.cql_clause("w.dossiernummer", "33818"), "", k.cql_clause("x", "", "="))
        self.assertEqual(q, 'w.dossiernummer=="33818"')

    def test_word_relation(self):
        self.assertEqual(k.cql_clause("w.documenttitel", "nota", "any"), 'w.documenttitel any "nota"')

    def test_sort(self):
        self.assertTrue(k.with_sort("q", "dt.date").endswith("sortBy dt.date/sort.descending"))

    def test_bouw_zoekvraag_mvt_artikel(self):
        q = pg.bouw_zoekvraag(["transitievergoeding"], soort="mvt", artikel="art. 7:673 BW")
        self.assertIn('c.product-area=="officielepublicaties"', q)
        self.assertIn('w.documenttitel="Memorie van toelichting"', q)
        self.assertIn('cql.textAndIndexes="7:673"', q)
        self.assertIn('cql.textAndIndexes="transitievergoeding"', q)

    def test_bouw_zoekvraag_toelichting_or(self):
        q = pg.bouw_zoekvraag([], soort="toelichting", dossier="35074")
        self.assertIn(" OR ", q)
        self.assertIn('w.documenttitel="Nota naar aanleiding van het verslag"', q)

    def test_bouw_zoekvraag_sgd(self):
        q = pg.bouw_zoekvraag(["onrechtmatige daad"], soort="mva", dossier="7729", sgd=True,
                              van="1970-01-01")
        self.assertIn('c.product-area=="sgd"', q)
        self.assertIn('dt.description="memorie van antwoord"', q)
        self.assertNotIn("dt.date", q)  # no date filter on sgd


class TestParseRecords(unittest.TestCase):
    def test_kamerstuk(self):
        res = k.parse_response(fixture("sru_kst.xml"))
        self.assertEqual(res.total, 1)
        r = res.records[0]
        self.assertEqual(r.identifier, "kst-33818-3")
        self.assertEqual(r.get("documenttitel"), "Memorie van toelichting")
        self.assertEqual(r.get("dossiernummer"), "33818")
        self.assertEqual(r.date, "2013-11-29")
        self.assertTrue(r.url("xml").endswith("kst-33818-3.xml"))
        self.assertTrue(r.url("pdf").endswith("kst-33818-3.pdf"))
        self.assertEqual(k.kamerstuk_citation(r, 12), "Kamerstukken II 2013/14, 33818, nr. 3, p. 12")
        self.assertEqual(pg.groep_van(r), "Memorie van toelichting")

    def test_handeling(self):
        res = k.parse_response(fixture("sru_handelingen.xml"))
        r = res.records[0]
        self.assertEqual(k.kamerstuk_citation(r), "Handelingen II 2013/14, nr. 55, item 18")
        self.assertIn("33818;14", r.getall("behandeldDossier"))

    def test_sgd(self):
        res = k.parse_response(fixture("sru_sgd.xml"))
        r = res.records[0]
        self.assertEqual(r.product_area, "sgd")
        self.assertEqual(r.date, "1986-01-27")
        self.assertEqual(r.descriptions[0], "NOTA NAAR AANLEIDING VAN HET EINDVERSLAG")
        self.assertEqual(k.kamerstuk_citation(r, 3), "Kamerstukken II 1985/86, 17541, nr. 11, p. 3")
        self.assertEqual(len(r.manifestations["ocr"]), 17)
        self.assertEqual(pg.groep_van(r), "Nota's n.a.v. verslag / memories van antwoord")

    def test_diagnostic_raises(self):
        body = (b'<searchRetrieveResponse xmlns="http://docs.oasis-open.org/ns/search-ws/sruResponse" '
                b'xmlns:ns3="http://docs.oasis-open.org/ns/search-ws/diagnostic"><diagnostics><ns3:diagnostic>'
                b"<ns3:message>line 1:35 mismatched input</ns3:message></ns3:diagnostic></diagnostics>"
                b"</searchRetrieveResponse>")
        with self.assertRaises(k.SruError) as cm:
            k.parse_response(body)
        self.assertIn("mismatched input", str(cm.exception))

    def test_invalid_xml(self):
        with self.assertRaises(k.SruError):
            k.parse_response(b"<html>kapot")

    def test_citation_eerste_kamer_and_herdruk(self):
        r = k.Record(identifier="kst-33818-D-n1", creator="Eerste Kamer der Staten-Generaal",
                     meta={"vergaderjaar": ["2013-2014"], "dossiernummer": ["33818"], "ondernummer": ["D"]})
        self.assertEqual(k.kamerstuk_citation(r), "Kamerstukken I 2013/14, 33818, nr. D (herdruk)")


class TestDocument(unittest.TestCase):
    def setUp(self):
        self.blocks = k.officiele_publicatie_blocks(fixture("kst_fragment.xml"))

    def test_tussenkop_becomes_heading(self):
        koppen = [b.text for b in self.blocks if b.kind == "kop"]
        self.assertIn("Onderdeel V (artikel 7:673 BW)", koppen)
        zevende = [b for b in self.blocks if b.text.startswith("Het zevende lid")][0]
        self.assertEqual(zevende.headings[-1], "Onderdeel V (artikel 7:673 BW)")

    def test_markdown(self):
        md = k.blocks_to_markdown(self.blocks)
        self.assertIn("Onderdeel V (artikel 7:673 BW)", md)
        self.assertIn("Het zevende lid voorziet", md)

    def test_parse_artikel(self):
        self.assertEqual(pg.parse_artikel("art. 7:673 lid 7 BW"),
                         {"boek": "7", "nr": "673", "lid": "7", "label": "7:673"})
        self.assertEqual(pg.parse_artikel("artikel 6.3.1.1")["label"], "6.3.1.1")
        self.assertEqual(pg.parse_artikel("7:673, zevende lid")["lid"], None)  # word form not parsed
        self.assertEqual(pg.parse_artikel("7:673 7e lid")["lid"], "7")

    def test_artikel_patterns(self):
        art_re, lid_re = pg.artikel_patronen(pg.parse_artikel("7:673 lid 7"))
        self.assertTrue(art_re.search("op grond van artikel 7:673 BW"))
        self.assertTrue(art_re.search("Onderdeel V (artikel 673)"))
        self.assertFalse(art_re.search("artikel 7:673a BW"))
        self.assertTrue(lid_re.search("Het zevende lid voorziet"))
        self.assertTrue(lid_re.search("in lid 7 van"))

    def test_vind_passages_lid(self):
        passages = pg.vind_passages(self.blocks, pg.parse_artikel("7:673 lid 7"), ["transitievergoeding"])
        self.assertTrue(passages)
        self.assertIn("Het zevende lid voorziet", passages[0]["tekst"])
        self.assertIn("Onderdeel V (artikel 7:673 BW)", passages[0]["kop"])

    def test_context_stops_at_673a(self):
        art_re, _ = pg.artikel_patronen(pg.parse_artikel("7:673"))
        ctx = pg.artikel_context(self.blocks, art_re)
        zevende = [i for i, b in enumerate(self.blocks) if b.text.startswith("Het zevende lid")][0]
        derde_673a = [i for i, b in enumerate(self.blocks) if b.text.startswith("Het derde lid maakt")][0]
        self.assertTrue(ctx[zevende])
        self.assertFalse(ctx[derde_673a])  # under "Onderdeel W (artikelen 7:673a, ...)"

    def test_article_heading_outranks_incidental_mentions(self):
        # Invented MvT: many early paragraphs mention "artikel 22" in passing; the
        # artikelsgewijze toelichting sits under a heading "Artikel 22" with lid sub-headings.
        B = k.Block
        blocks = [B("kop", "1. Algemeen", ("1. Algemeen",))]
        for n in range(10):
            blocks.append(B("al", f"Terloops: artikel 22 van de verordening, punt {n}.", ("1. Algemeen",)))
        blocks += [B("kop", "Artikel 21", ("Artikel 21",)),
                   B("al", "Dit artikel regelt de accreditatie.", ("Artikel 21",)),
                   B("kop", "Artikel 22", ("Artikel 22",)),
                   B("al", "Dit artikel geeft de hoofdregel weer.", ("Artikel 22",)),
                   B("kop", "Eerste lid: verwerkingsverbod", ("Eerste lid: verwerkingsverbod",)),
                   B("al", "Het eerste lid bevat het verbod.", ("Eerste lid: verwerkingsverbod",)),
                   B("kop", "Artikel 23", ("Artikel 23",)),
                   B("al", "Dit artikel bevat uitzonderingen.", ("Artikel 23",))]
        passages = pg.vind_passages(blocks, pg.parse_artikel("22"), [], context=0)
        kernen = [p["kern"] for p in passages]
        self.assertEqual(kernen[:2], ["Dit artikel geeft de hoofdregel weer.", "Het eerste lid bevat het verbod."])
        self.assertNotIn("Dit artikel bevat uitzonderingen.", kernen)

    def test_keyword_only(self):
        passages = pg.vind_passages(self.blocks, None, ["dienstverband"])
        self.assertTrue(any("twee jaar" in p["tekst"] for p in passages))


def _pdf_with_pages(pages):
    """Tiny synthetic PDF: one Flate content stream per page with a Kamerstuk footer."""
    parts = [b"%PDF-1.4\n"]
    for i, (body, footer) in enumerate(pages, 1):
        content = (f"BT /F1 9 Tf 50 700 Td ({body}) Tj T* [(Tweede Kamer, vergaderjaar 2013)-300(\\226"
                   f"2014, 33 818, nr. 3 {footer})] TJ ET").encode("latin-1")
        data = zlib.compress(content)
        parts.append(f"{i} 0 obj<</Length {len(data)}/Filter/FlateDecode>>stream\n".encode() + data
                     + b"\nendstream\nendobj\n")
    return b"".join(parts)


class TestPdfPages(unittest.TestCase):
    def test_footer_page_numbers(self):
        pdf = _pdf_with_pages([("Eerste bladzijde over de transitie-", 1),
                               ("Het zevende lid voorziet in uitzonderingen", 112)])
        pages = k.pdf_pages(pdf, "3")
        self.assertEqual([p for p, _ in pages], [1, 112])
        self.assertIn("vergaderjaar 2013 –2014", pages[1][1])
        self.assertEqual(pg.pagina_voor("Het zevende lid voorziet in uitzonderingen op grond waarvan",
                                        [(112, "Het zevende lid voorziet in uitzonderingen op grond waarvan")]),
                         112)

    def test_unreadable_pdf(self):
        self.assertEqual(k.pdf_pages(b"%PDF-1.4 nothing"), [])


class TestSgdOcr(unittest.TestCase):
    def test_ocr_pages_use_startpagina_and_cache(self):
        rec = k.parse_response(fixture("sru_sgd.xml")).records[0]
        body = fixture("sgd_ocr_pagina.xml")
        calls = []

        def fake_get(url, accept="*/*", headers=None, allow_status=()):
            calls.append(url)
            return mock.Mock(body=body)

        import tempfile
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"NLJS_CACHE_DIR": tmp}), \
                mock.patch.object(k.nl_http, "get", side_effect=fake_get):
            pages = k.sgd_ocr_pages(rec, first_page=2, last_page=3)
            self.assertEqual([p for p, _ in pages], [2, 3])
            self.assertIn("Artikel 5.6.9a", pages[0][1])
            k.sgd_ocr_pages(rec, first_page=2, last_page=3)  # second time from cache
        self.assertEqual(len(calls), 2)


class TestBereik(unittest.TestCase):
    def test_bereik(self):
        self.assertEqual(pg._bereik("120-180"), (120, 180))
        self.assertEqual(pg._bereik("45"), (45, 45))
        self.assertEqual(pg._bereik("120-"), (120, None))
        with self.assertRaises(SystemExit):
            pg._bereik("abc")


if __name__ == "__main__":
    unittest.main()
