---
name: termijnen
description: Rekenhulp voor Nederlandse procestermijnen. Gebruik wanneer de gebruiker de laatste dag van een termijn wil weten ("wanneer verloopt de appeltermijn", "tot wanneer kan ik bezwaar maken", "cassatietermijn", "hoger beroep strafzaak", "10 dagen na betekening"). Rekent vanaf de datum van uitspraak of bekendmaking en past de Algemene termijnenwet toe (weekend, feestdagen, gelijkgestelde dagen uit de Staatscourant).
---

# Termijnen

Rekenhulp, geen advies. De uitkomst altijd zelf controleren.

## Wanneer
- Hoger beroep civiel: art. 339 Rv (3 maanden; kort geding 4 weken).
- Cassatie civiel: art. 402 Rv (3 maanden; kort geding 8 weken via lid 2).
- Bezwaar of beroep bestuursrecht: art. 6:7 en 6:8 lid 1 Awb (6 weken vanaf de dag na bekendmaking).
- Hoger beroep strafrecht: art. 408 lid 1 Sv (14 dagen na de einduitspraak).
- Generiek: N dagen, weken of maanden na een datum, met of zonder Atw.

## Invoer
Een datum (JJJJ-MM-DD) en het soort termijn. Draai vanuit deze skillmap:
```
python3 scripts/termijnen.py hoger-beroep-civiel --uitspraak 2026-01-31 [--kort-geding]
python3 scripts/termijnen.py cassatie-civiel --uitspraak 2025-10-02 [--kort-geding]
python3 scripts/termijnen.py bezwaar-beroep-awb --bekendmaking 2026-04-24
python3 scripts/termijnen.py hoger-beroep-straf --uitspraak 2026-12-11
python3 scripts/termijnen.py generiek --datum 2026-06-01 --aantal 10 --eenheid dagen --wettelijk
```
Voeg `--json` toe voor gestructureerde uitvoer.

## Voorbeeld
Vonnis kantonrechter zaterdag 31 januari 2026, hoger beroep: april heeft geen 31e, dus de termijn
eindigt op donderdag 30 april 2026 (HR 1 september 2017, ECLI:NL:HR:2017:2225). Geen weekend of
feestdag, dus geen verlenging.

## Uitvoer
Uitkomst (laatste dag met weekdag), rekenstappen, juridische grondslag, aandachtspunten en de regel
"Controleer de uitkomst zelf; dit is een rekenhulp, geen advies." Geef die vier onderdelen aan de
gebruiker door; laat de waarschuwingen niet weg.

## Grenzen
- Alleen termijnen die eindigen in 2020-2028. Daarbuiten weigert het script: de in de Staatscourant
  gelijkgestelde dagen zijn alleen voor die jaren gecontroleerd (stand 23 september 2026).
- Geen terugrekentermijnen (art. 1 lid 2 Atw), geen termijnen in uren of jaren.
- Niet: beschikkingen (art. 358 Rv), tussenvonnissen (art. 337 Rv), verkorte bijzondere termijnen
  (bijv. faillissement), art. 6:8 lid 2-4 Awb, art. 408 lid 2 Sv (gebruik dan `generiek --wettelijk`
  met de datum van bekendwording).
- Tijdige indiening (art. 6:9 Awb, betekening, griffierecht) valt buiten de berekening.
- Bronnen en wat niet uit een primaire bron kon worden geverifieerd: `references/bronnen.md`.
