---
name: parlementaire-geschiedenis
description: Zoekt en haalt parlementaire geschiedenis op (Kamerstukken en Handelingen) uit de officiële KOOP-bron op repository.overheid.nl. Gebruik bij vragen als "wat zei de wetgever over art. 7:673 BW", "MvT bij de transitievergoeding", "alle stukken van dossier 33818", "Nota n.a.v. verslag Wet arbeidsmarkt in balans", of bij een memo of processtuk dat een beroep doet op de wetsgeschiedenis. Ook voor stukken van vóór 1995 (Staten-Generaal Digitaal, OCR). Geeft passages met vindplaats in Kamerstukken-notatie.
---

# Parlementaire geschiedenis

Vindt Kamerstukken (wetsvoorstel, MvT, Raad van State, verslagen, nota's n.a.v. verslag,
nota's van wijziging, amendementen, EK-stukken) en Handelingen. Het script haalt de tekst op
en toont de passages over een artikel of een trefwoord, met vindplaats.

Bron: de officiële SRU-zoekdienst van KOOP (`https://repository.overheid.nl/sru`):
- `officielepublicaties`: stukken vanaf ±1995, als gestructureerde XML;
- `sgd` (Staten-Generaal Digitaal): stukken van 1814 tot 1995, als OCR van scans.

## Wat je nodig hebt
Een van deze vier: een dossiernummer (33818), een wetsnaam ("Wet werk en zekerheid"), een
artikel met een trefwoord (art. 7:673 BW + transitievergoeding), of vrije zoektermen.

## Stappen
Alle commando's draai je vanuit de map van deze skill.

1. **Dossier bepalen**
   - Van een wetsnaam naar een dossiernummer: `python3 scripts/parlgesch.py wet "Wet arbeidsmarkt in balans"`.
     Gebruik de citeertitel, geen afkorting: "Wet werk en zekerheid", niet "WWZ".
   - Van een artikel naar een dossier: `python3 scripts/parlgesch.py zoek --artikel "7:673 BW" --soort mvt`.
     Dit geeft alle MvT's waarin "7:673" staat, ook begrotingen en verzamelwetten. Kies zelf het dossier dat het artikel invoerde of wijzigde.
   - Tip: als de skill `wetshistorie` geïnstalleerd is, geeft die per artikel de wijzigingswetten
     met hun dossiernummers. Die skill is niet nodig; de route hierboven werkt ook zonder.
2. **Overzicht van het dossier**: `python3 scripts/parlgesch.py dossier 33818`. Dit geeft de
   kernstukken per soort en daarnaast de Handelingen (via `w.behandeldDossier`) en de
   Staatsblad-publicatie. Voeg `--alles` toe voor moties, brieven en bijlagen.
3. **Gericht zoeken**: `python3 scripts/parlgesch.py zoek transitievergoeding --soort toelichting --dossier 33818`.
   - `--soort` kan zijn: `mvt`, `nnavv`, `nvw`, `mva`, `verslag`, `wetsvoorstel`,
     `raad-van-state`, `amendement` of `toelichting` (= mvt + nnavv + nvw + mva).
   - Elke zoekterm moet voorkomen. Geef zinsneden als één argument tussen aanhalingstekens.
   - Andere filters: `--van`/`--tot` (JJJJ-MM-DD), `--kamer tk|ek`, `--sorteer datum`.
4. **Passages ophalen**: `python3 scripts/parlgesch.py haal kst-33818-3 --artikel "7:673 lid 7" --trefwoord transitievergoeding`.
   - Je krijgt de best passende alinea's, de meest relevante eerst, met paragraafkop en
     paginanummer. Het paginanummer komt uit de voettekst van de officiële pdf.
   - Het hele stuk als markdown: `haal kst-33818-3 --volledig -o mvt.md`.
5. **Vóór 1995**:
   - Zoeken: `python3 scripts/parlgesch.py zoek "onrechtmatige daad" --voor-1995 --dossier 7729`.
   - Passages ophalen: `haal 0000194825 --trefwoord "onrechtmatige daad"`.
   - NBW-stukken en de eerste Awb-tranche gebruiken de ontwerpnummering (bv. `6.3.1.1`,
     of `3.2.3` voor wat nu art. 3:4 Awb is), niet de huidige nummers. Zoek daarom op
     trefwoord, of op het ontwerpnummer als je dat kent (`--artikel "3.2.3 lid 2"`).
   - Het script haalt één OCR-pagina per seconde op. Een groot stuk (250 pagina's) kost
     ruim 4 minuten. Beperk dat met `--paginas 120-200`. Eerder opgehaalde pagina's komen
     uit de cache.
6. **Lees en controleer.**
   - Lees de gevonden passages zelf en citeer alleen wat er echt staat.
   - Bij OCR-tekst: controleer het citaat tegen de pdf-scan (de link staat in de uitvoer).
   - Vermeld bij een ledennummer dat het in het stuk verwijst naar de toen voorgestelde
     tekst. De nummering kan later zijn gewijzigd; check de wettekst van dat moment.

## Uitvoer
Een lijst of passages in markdown. Elke vindplaats staat in Kamerstukken-notatie:
- `Kamerstukken II 2013/14, 33818, nr. 3, p. 112`;
- `Kamerstukken I 2013/14, 33818, nr. C`;
- `Handelingen II 2013/14, nr. 55, item 18`.

Staat er geen paginanummer, dan kon de pdf niet worden gelezen. Verwijs dan naar de
paragraafkop, of zoek de pagina op in de pdf.

## Grenzen
- **Alleen ruwe Kamerstukken en Handelingen.** De samengestelde boekenreeks
  *Parlementaire Geschiedenis van het Nieuwe Burgerlijk Wetboek* (per artikel geordend) is
  commercieel en zit hier niet in. Een BW-artikel koppelen aan de juiste passage kan alleen
  door in de dossiers te zoeken.
- De koppeling artikel → passage is een tekstheuristiek. Het script herkent "7:673",
  "artikel 673" en alinea's na een introductie als "Met dit onderdeel wordt artikel 7:673
  ingevoegd". Het kan passages missen of er te veel tonen. Lees daarom altijd na.
- Stukken van vóór ±2009 staan soms alleen als pdf of scan. Van vóór 1995 is er alleen
  OCR. Die kan fouten bevatten (bv. "5.2.3-8'a").
- Het zoeken op datum (`--van`/`--tot`) werkt niet voor `--voor-1995`.
- Wetten.overheid.nl-pagina's worden niet gebruikt. Wil je de wettekst zelf, gebruik dan een
  wettekst-skill of de officiële BWB-bron.
