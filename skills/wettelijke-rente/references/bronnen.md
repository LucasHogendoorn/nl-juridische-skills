# Bronnen wettelijke rente (gecontroleerd 23 september 2026)

Wetteksten komen uit de officiële BWB-repository van KOOP (toestand-XML), niet van wetten.overheid.nl.
Staatsbladen: `https://repository.overheid.nl/frbr/officielepublicaties/stb/<jaar>/<id>/1/xml/<id>.xml`.

## Wetgeving (BW Boek 6, BWBR0005289, toestand 2026-07-16_0)

- Art. 6:44 lid 1 BW: "Betaling van een op een bepaalde verbintenis toe te rekenen geldsom strekt in de eerste plaats in mindering van de kosten, vervolgens in mindering van de verschenen rente en ten slotte in mindering van de hoofdsom en de lopende rente."
- Art. 6:119 lid 1 BW: rente "over de tijd dat de schuldenaar met de voldoening daarvan in verzuim is geweest". Lid 2: "Telkens na afloop van een jaar wordt het bedrag waarover de wettelijke rente wordt berekend, vermeerderd met de over dat jaar verschuldigde rente."
- Art. 6:119a lid 1 BW: bij een handelsovereenkomst rente "met ingang van de dag volgend op de dag die is overeengekomen als de uiterste dag van betaling tot en met de dag waarop de schuldenaar de geldsom heeft voldaan". Lid 3: zelfde jaarlijkse kapitalisatie als 6:119 lid 2.
- Art. 6:120 lid 1 BW: percentage niet-handel bij AMvB; lopende rente gaat mee met een nieuw percentage.
- Art. 6:120 lid 2 BW: handelsrente = "herfinancieringsrente die door de Europese Centrale Bank is vastgesteld voor haar meest recente basisherfinancieringstransactie die heeft plaatsgevonden voor de eerste kalenderdag van het betreffende halfjaar, vermeerderd met acht procentpunten". Tot 16-3-2013: "zeven procentpunten" (gewijzigd bij Stb. 2012, 647, art. I onderdeel D; inwerkingtreding 16-3-2013, Stb. 2013, 9).

## Percentages niet-handelstransacties (art. 6:119 BW)

Elke rij gelezen in de tekst van het besluit; tot 2022 ook in de BWB-toestanden van het Besluit wettelijke
rente (BWBR0002744; manifest: laatste toestand 2015-01-01_0 geldig tot en met 2022-12-31, "twee procent").

| Vanaf | % | Bron |
|---|---|---|
| 1-1-2002 | 7 | Stb. 2001, 630 |
| 1-8-2003 | 5 | Stb. 2003, 280 |
| 1-2-2004 | 4 | Stb. 2004, 13 |
| 1-1-2007 | 6 | Stb. 2006, 700 |
| 1-7-2009 | 4 | Stb. 2009, 262 |
| 1-1-2010 | 3 | Stb. 2009, 618 |
| 1-7-2011 | 4 | Stb. 2011, 317 |
| 1-7-2012 | 3 | Stb. 2012, 285 |
| 1-1-2015 | 2 | Stb. 2014, 491 |
| 1-1-2023 | 4 | Stb. 2022, 520 |
| 1-7-2023 | 6 | Stb. 2023, 235 |
| 1-1-2024 | 7 | Stb. 2023, 484 |
| 1-1-2025 | 6 | Stb. 2024, 395 |
| 1-1-2026 | 4 | Stb. 2025, 438; bevestigd door rijksoverheid.nl ("sinds 1 januari 2026 4%") |

Nieuwe besluiten vinden: KOOP SRU `https://repository.overheid.nl/sru`, zoekvraag
`c.product-area==officielepublicaties AND w.publicatienaam==Staatsblad AND dt.title any "vaststelling wettelijke rente"`
(laatste treffer op 23-9-2026: stb-2025-438).

## Percentages handelstransacties (art. 6:119a BW)

Nederland publiceert geen officiële tabel. De percentages zijn afgeleid met de formule van art. 6:120 lid 2 BW
uit de officiële ECB-reeks "Main refinancing operations - fixed rate" (`FM.B.U2.EUR.4F.KR.MRR_FR.LEV`,
https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.MRR_FR.LEV?format=csvdata): de laatste waarde
die gold voor 1 januari of 1 juli, plus 8. Alleen het percentage vanaf 1-7-2026 (10,4%) is door een
Nederlandse overheidsbron bevestigd (rijksoverheid.nl, "Hoogte wettelijke rente", gelezen 23-9-2026).
Per rij staan ECB-percentage en ingangsdatum van dat ECB-percentage in `data/rentetabel.json`.

| Vanaf | ECB MRO | Handelsrente |
|---|---|---|
| 16-3-2013 | 0,75 (sinds 11-7-2012) | 8,75 |
| 1-7-2013 | 0,50 | 8,50 |
| 1-1-2014 | 0,25 | 8,25 |
| 1-7-2014 | 0,15 | 8,15 |
| 1-1-2015 t/m 30-6-2016 | 0,05 | 8,05 |
| 1-7-2016 t/m 31-12-2022 | 0,00 | 8,00 |
| 1-1-2023 | 2,50 | 10,50 |
| 1-7-2023 | 4,00 | 12,00 |
| 1-1-2024 | 4,50 | 12,50 |
| 1-7-2024 | 4,25 | 12,25 |
| 1-1-2025 | 3,15 | 11,15 |
| 1-7-2025 | 2,15 | 10,15 |
| 1-1-2026 | 2,15 | 10,15 |
| 1-7-2026 | 2,40 | 10,40 |

## Overgangsrecht handelsrente 2013 (reden voor weigering)

- Stb. 2012, 647 art. III voegt art. 183a Overgangswet nieuw BW in: "De artikelen 96 lid 4, 119a leden 4 en 5 en 119b van Boek 6 zijn niet van toepassing op overeenkomsten die vóór het tijdstip van het in werking treden van deze bepalingen zijn gesloten." Art. 6:120 lid 2 (de verhoging naar 8 procentpunten) staat daar niet in.
- Memorie van toelichting, Kamerstukken II 2011/12, 33171, nr. 3, bij art. III: "wordt bepaald dat deze wet van toepassing is op die overeenkomsten die na de inwerkingtreding van deze wet worden gesloten (eerbiedigende werking)", en daarna dat de formulering op advies van de Raad van State is aangepast tot de genoemde artikelen.
- Tekst en toelichting wijzen dus niet eenduidig dezelfde kant op voor overeenkomsten van voor 16-3-2013, en
  voor lopende rente in het halfjaar 1-1 t/m 30-6-2013 zegt art. 6:120 lid 2 niets over een wijziging midden in
  een halfjaar. Het script berekent daarom alleen handelsrente voor overeenkomsten gesloten op of na 16-3-2013.

## Rekenconventies van het script

- Rente loopt over elke dag van `--vanaf` tot en met `--tot`. Een betaling wordt aan het einde van de
  betaaldag verwerkt (rente over de betaaldag loopt nog, vgl. "tot en met de dag waarop" in 6:119a lid 1).
- Rente per dag = grondslag x percentage / 365 (standaard) of / lengte van het rentejaar (`--dagbasis jaar`).
- Rentejaar = vanaf de begindatum tot de dag voor dezelfde datum een jaar later; aan het einde daarvan wordt
  de rente bij de grondslag gevoegd. Begindatum 29 februari: verjaardag 28 februari.
- Rente per deelperiode afgerond op centen (half naar boven); totalen zijn sommen van die afgeronde bedragen.
- Toerekening van een betaling: kosten, dan gekapitaliseerde rente, dan lopende (nog niet gekapitaliseerde)
  rente tot en met de betaaldag, dan hoofdsom.

## Niet uit een primaire bron geverifieerd (juridische review nodig)

1. Dagtelling (365 of werkelijke lengte van het jaar): wet en besluiten zeggen niets. Geen rechtspraak gelezen.
2. Begin van het "jaar" in art. 6:119 lid 2 / 6:119a lid 3: het script rekent vanaf de eerste rentedag per
   vordering. Tekstuele lezing; geen rechtspraak gelezen.
3. Toerekening (art. 6:44 lid 1 BW): het script behandelt alle tot en met de betaaldag opgelopen rente als
   "verschenen rente" en rekent gekapitaliseerde rente als rente, niet als hoofdsom. Beide keuzes zijn lezingen.
4. Of de rente over de eerste of de laatste dag loopt, hangt af van de juiste begindatum; het script neemt
   beide grensdagen mee.
5. Handelsrente-percentages zijn afgeleid uit ECB-data, niet uit een Nederlandse officiële tabel (behalve
   10,4% vanaf 1-7-2026). De interpretatie "meest recente transactie voor de eerste kalenderdag" = de
   ECB-waarde die gold op de dag voor 1 januari/1 juli is een lezing van art. 6:120 lid 2.
6. Afronding per deelperiode is een keuze; andere rekenprogramma's kunnen enkele centen afwijken.
