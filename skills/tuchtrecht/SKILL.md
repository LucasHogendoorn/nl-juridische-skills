---
name: tuchtrecht
description: Zoekt en haalt tuchtrechtuitspraken op (advocaten, gezondheidszorg/BIG, notarissen, gerechtsdeurwaarders, accountants, dierenartsen) uit de officiële KOOP-bron achter tuchtrecht.overheid.nl. Gebruik bij vragen als "advocaat belangenverstrengeling 2024", "tuchtcollege huisarts dossiervoering", "notaris zorgplicht", of wanneer je een tuchtuitspraak met ECLI (ECLI:NL:TADRAMS:..., ECLI:NL:TGZRAMS:..., ECLI:NL:TNORAMS:...) wilt lezen. Geeft een lijst met ECLI, datum, college en inhoudsindicatie, of de volledige uitspraak.
---

# Tuchtrecht

Zoekt in de gepubliceerde tuchtrechtuitspraken van tuchtrecht.overheid.nl. Het zoeken gaat via
de officiële SRU-dienst van KOOP (`https://repository.overheid.nl/sru`, collectie `tuchtrecht`).
Het script toont een lijst met samenvattingen of haalt de volledige tekst van één uitspraak op.

## Wat je nodig hebt
Een onderwerp (trefwoorden) en zo mogelijk een beroepsgroep en een periode. Om één uitspraak
te lezen heb je de ECLI nodig.

## Stappen
Alle commando's draai je vanuit de map van deze skill.

1. **Zoeken**: `python3 scripts/tuchtrecht.py zoek belangenverstrengeling --domein advocaten --van 2024-01-01 --tot 2024-12-31 --strikt`
   - `--domein`: advocaten, gezondheidszorg, notarissen, gerechtsdeurwaarders, accountants,
     diergeneeskundigen (zie `python3 scripts/tuchtrecht.py waarden`).
   - `--beroep` (alleen gezondheidszorg): arts, huisarts, tandarts, verpleegkundige,
     gz-psycholoog, ... Uitspraken van na ±september 2021 hebben geen beroepsveld meer.
     Daarom zoekt `--beroep` op het veld óf op het woord in de inhoudsindicatie. `huisarts`
     heeft geen eigen veld: dan wordt gezocht op beroepsgroep Arts met het woord "huisarts".
   - `--strikt`: de zoektermen moeten in de inhoudsindicatie staan. **Begin hiermee.** Zonder
     `--strikt` wordt in de volledige tekst gezocht. In een test ging dan maar de helft van de
     treffers echt over het onderwerp (12 van 25). Laat `--strikt` pas weg als je te weinig vindt.
   - `--onderwerp Belangenconflict` filtert op het (sub)onderwerp dat het college heeft toegekend.
   - `--uitkomst berisping` zoekt het woord in de beslissing of de inhoudsindicatie.
   - Standaard staan de nieuwste uitspraken eerst. Met `--sorteer relevantie` krijg je de volgorde van de zoekdienst.
     Met `-n 25` krijg je meer resultaten, met `--json` machineleesbare uitvoer.
2. **Beoordelen**: lees de inhoudsindicaties en kies de uitspraken die echt over de vraag gaan.
   Een treffer betekent alleen dat het woord voorkomt, niet dat de uitspraak erover gaat.
3. **Volledige tekst**: `python3 scripts/tuchtrecht.py haal ECLI:NL:TADRARL:2024:292`
   (of `-o uitspraak.md`; `--meta` geeft alleen de kop en de inhoudsindicatie).
4. **Rapporteren**: geef per uitspraak de ECLI, het college, de datum, in één of twee zinnen wat
   er werd verweten en wat het oordeel was, en de link naar tuchtrecht.overheid.nl. Citeer alleen
   letterlijk uit de opgehaalde tekst.

## Uitvoer
Een genummerde lijst in deze vorm: **ECLI** — college, datum · zaaknummer · beslissing ·
onderwerp, de inhoudsindicatie als citaat en de link. `haal` geeft markdown met een kop
(instantie, datum, zaaknummer, onderwerp), de inhoudsindicatie en de volledige uitspraak.

## Grenzen
- Alleen uitspraken die de colleges publiceren. De dekking verschilt per beroep en per
  periode, en niet alle uitspraken worden gepubliceerd. Een lege zoekopdracht bewijst dus
  niet dat er geen tuchtrecht over bestaat.
- Het veld "beslissing" wordt niet overal gebruikt. Bij advocaten staat er vaak "Regulier" of
  "Voorzittersbeslissing", en de uitkomst (berisping, gegrond) staat dan in de inhoudsindicatie.
- Uitspraken van de gewone rechter en het CBb staan op rechtspraak.nl, niet hier.
- Partijnamen zijn in de uitspraken geanonimiseerd. Gebruik de tekst niet om personen te
  identificeren.
