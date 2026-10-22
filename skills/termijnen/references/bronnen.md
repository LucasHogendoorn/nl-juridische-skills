# Bronnen termijnen (gecontroleerd 23 september 2026)

Wetteksten komen uit de officiële BWB-repository van KOOP (toestand-XML), niet van wetten.overheid.nl.
URL-patroon: `https://repository.officiele-overheidspublicaties.nl/bwb/<BWB-id>/<toestand>/xml/<BWB-id>_<toestand>.xml`.

## Wetgeving

| Regel in het script | Bron | Toestand |
|---|---|---|
| Verlenging bij zaterdag, zondag, feestdag | Art. 1 lid 1 Algemene termijnenwet (BWBR0002448) | 2010-10-10_0 |
| Geen verlenging bij terugrekenen | Art. 1 lid 2 Atw | idem |
| Ten minste twee werkdagen in termijn van 3+ dagen | Art. 2 Atw | idem |
| Lijst feestdagen, Goede Vrijdag, gelijkstelling bij KB | Art. 3 lid 1-3 Atw | idem |
| Atw niet bij >90 dagen, >12 weken, >3 maanden, jaren, uren | Art. 4 onder a Atw | idem |
| Atw ook voor AMvB-termijnen | Art. 5 Atw | idem |
| Appel 3 maanden / kort geding 4 weken | Art. 339 lid 1 en 2 Rv (BWBR0001827) | 2026-07-14_0 |
| Cassatie 3 maanden; dubbele verkorte appeltermijn | Art. 402 lid 1 en 2 Rv | 2026-07-14_0 |
| Bezwaar/beroep 6 weken | Art. 6:7 Awb (BWBR0005537) | 2026-08-15_0 |
| Aanvang dag na bekendmaking | Art. 6:8 lid 1 Awb | idem |
| Strafappel 14 dagen na einduitspraak | Art. 408 lid 1 Sv (BWBR0001903) | 2026-07-01_0 |
| Sv verwijst voor 'dag' naar de Atw | Art. 136 lid 1 en 2 Sv | idem |

Kernteksten (letterlijk):
- Art. 1 lid 1 Atw: "Een in een wet gestelde termijn die op een zaterdag, zondag of algemeen erkende feestdag eindigt, wordt verlengd tot en met de eerstvolgende dag die niet een zaterdag, zondag of algemeen erkende feestdag is."
- Art. 2 Atw: "Een in een wet gestelde termijn van ten minste drie dagen wordt, zo nodig, zoveel verlengd, dat daarin ten minste twee dagen voorkomen die niet een zaterdag, zondag of algemeen erkende feestdag zijn."
- Art. 3 lid 1 Atw: "Algemeen erkende feestdagen in de zin van deze wet zijn: de Nieuwjaarsdag, de Christelijke tweede Paas- en Pinksterdag, de beide Kerstdagen, de Hemelvaartsdag, de dag waarop de verjaardag van de Koning wordt gevierd en de vijfde mei." Lid 2: Goede Vrijdag wordt gelijkgesteld.
- Art. 4 Atw: "Deze wet geldt niet voor termijnen: a. omschreven in uren, in meer dan 90 dagen, in meer dan twaalf weken, in meer dan drie maanden, of in een of meer jaren; b. betreffende de bekendmaking, inwerkingtreding of buitenwerkingtreding van wettelijke voorschriften; c. van vrijheidsbeneming."
- Art. 339 lid 1 Rv: "De termijn voor het instellen van hoger beroep is drie maanden, te rekenen van de dag van de uitspraak van het vonnis dan wel de dag van de mondelinge uitspraak als bedoeld in artikel 29a." Lid 2: "In afwijking van het eerste lid is de termijn van beroep van een vonnis in kort geding vier weken."
- Art. 402 lid 2 Rv: "In de gevallen, waarin de wet voor het hoger beroep een kortere termijn heeft voorgeschreven, wordt ook de termijn voor het beroep in cassatie verkort en gesteld op het dubbele van de termijn in die gevallen voor het hoger beroep bepaald."
- Art. 6:8 lid 1 Awb: "De termijn vangt aan met ingang van de dag na die waarop het besluit op de voorgeschreven wijze is bekendgemaakt."
- Art. 136 lid 1 Sv: "Onder maand wordt verstaan een tijd van dertig dagen, onder dag, behoudens voor de toepassing van de Algemene termijnenwet, een tijd van vierentwintig uren."

## Gelijkgestelde dagen (art. 3 lid 3 Atw)

Gevonden via de KOOP SRU-zoekdienst `https://repository.overheid.nl/sru` met
`c.product-area==officielepublicaties AND dt.title any "gelijkstelling" AND dt.title any "feestdag" AND dt.date>=2018-01-01`
(3 treffers; een bredere zoekvraag op "gelijkstelling" in de Staatscourant sinds 2018 gaf geen andere Atw-besluiten).
Tekst gelezen via `https://repository.overheid.nl/frbr/officielepublicaties/stcrt/<jaar>/<id>/1/xml/<id>.xml`.

| Besluit | Gelijkgestelde dagen |
|---|---|
| Stcrt. 2019, 53179 (Besluit 20 september 2019) | 22-5-2020, 14-5-2021, 27-5-2022 |
| Stcrt. 2022, 7812 (Besluit 8 maart 2022) | 28-4-2023, 19-5-2023, 10-5-2024, 27-12-2024, 30-5-2025 |
| Stcrt. 2025, 24713 (Besluit 1 juli 2025) | 2-1-2026, 15-5-2026, 7-5-2027, 28-4-2028, 26-5-2028 |

De tabel staat in `data/feestdagen.json`. Paasdata worden berekend; de test controleert dat Pasen + 40
dagen voor elk jaar 2020-2028 precies de gelijkgestelde vrijdag na Hemelvaart uit deze besluiten geeft.

## Rechtspraak (opgehaald via https://data.rechtspraak.nl/uitspraken/content?id=<ECLI>)

- **HR 1 september 2017, ECLI:NL:HR:2017:2225** (art. 339 lid 1, 358 lid 2, 402 lid 1, 426 lid 1 Rv).
  r.o. 3.4.1: de termijn begint te lopen met ingang van de dag volgend op die van de uitspraak.
  r.o. 3.4.3: "de driemaandentermijn [loopt] pas af aan het einde van de daarmee overeenstemmende dag drie maanden later"; uitspraak 28 februari (gewoon jaar) of 29 februari (schrikkeljaar), 30 april, 30 september: einde 28 of 29 mei, 30 juli, 30 december, "afgezien van de werking van de Algemene termijnenwet".
  r.o. 3.4.4: eindigt in beginsel op de dag met hetzelfde nummer; heeft de maand die dag niet, dan op de laatste dag van die maand.
  r.o. 3.1 (hof, niet bestreden): 29 mei 2016 (zondag) verlengd tot maandag 30 mei 2016 op grond van art. 1 lid 1 Atw.
- **HR 12 maart 2004, ECLI:NL:HR:2004:AO1315**: eindvonnis 29 november 2002; de cassatietermijn (art. 402 lid 1 Rv) eindigde op 28 februari 2003.

## Niet uit een primaire bron geverifieerd (juridische review nodig)

1. Weken-termijnen "te rekenen van de dag van de uitspraak" (kort geding appel 4 weken, cassatie 8 weken):
   het script telt de uitspraakdag niet mee (einde = uitspraak + 28/56 dagen). Dat is afgeleid van
   HR 2017:2225, dat alleen over maandtermijnen gaat. Geen HR-uitspraak over weken gelezen.
2. Strafappel: einde = uitspraak + 14 dagen ("binnen veertien dagen na"). Tekstuele lezing; geen
   rechtspraak gelezen.
3. Koningsdag: het script behandelt 27 april als feestdag als die op een werkdag valt. Waarom 26 april
   (bij 27 april op zondag) geen verschil maakt: 26 april is dan een zaterdag. De datumregel zelf
   (viering op 26 april) is niet in een primaire bron nagezocht.
4. Volledigheid van de gelijkstellingsbesluiten 2020-2028: gebaseerd op de SRU-zoekvragen hierboven.
   Een besluit met een afwijkende titel of een later gepubliceerd besluit kan ontbreken.
5. Art. 2 Atw: het script telt werkdagen vanaf dag 1 (de dag na de startdatum) tot en met de laatste dag.
   Die afbakening van "daarin" is een lezing van de wettekst.
6. De Atw wordt voor Rv-, Awb- en Sv-termijnen toegepast op grond van art. 1 Atw ("in een wet gestelde
   termijn"), art. 136 Sv en HR 2017:2225 r.o. 3.4.3. Bijzondere wetten die de Atw uitsluiten zijn niet
   onderzocht.
