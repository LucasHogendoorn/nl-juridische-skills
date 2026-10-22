---
name: rechtspraak
description: Haalt de officiële tekst en metadata van Nederlandse uitspraken (ECLI:NL, via de open data van de Rechtspraak) en van EU-uitspraken en EU-wetgeving (ECLI:EU, CELEX, zaaknummer C-xxx/yy, via het Publicatiebureau van de EU) op, en zoekt uitspraken op instantie, datum en rechtsgebied. Gebruik deze skill wanneer de inhoud van een specifieke uitspraak of EU-tekst ertoe doet voor het antwoord (wat de rechter besliste, een rechtsoverweging, de formele relaties, vindplaatsen) of wanneer recente uitspraken van een bepaalde instantie of een bepaald rechtsgebied nodig zijn. Niet nodig voor algemene vragen over het recht zonder concrete uitspraak.
---

# Rechtspraak (NL en EU)

Haal uitspraken op uit de officiële bronnen in plaats van ze uit het geheugen te citeren. Als een ophaalactie mislukt, zeg dat; vul de inhoud niet zelf in.

## Wanneer

- Er wordt een ECLI, CELEX-nummer of HvJ-zaaknummer genoemd en de inhoud is relevant.
- Je gaat een uitspraak citeren of samenvatten (r.o.-nummer, dictum, conclusie A-G).
- Je zoekt recente uitspraken van een instantie of rechtsgebied in een periode.
- Je wilt weten of een uitspraak een conclusie, eerdere aanleg of cassatie heeft (formele relaties).

## Scripts

Draai de scripts vanuit de map van deze skill. Alleen de Python-standaardbibliotheek (3.9+) is nodig; er is geen API-sleutel nodig.

| Doel | Commando |
|---|---|
| Uitspraak ophalen (volledige tekst) | `python3 scripts/fetch_ecli.py ECLI:NL:HR:2025:667` |
| Alleen metadata en inhoudsindicatie | `python3 scripts/fetch_ecli.py ECLI:NL:HR:1981:AG4158 --alleen-meta` |
| Meerdere uitspraken naar bestanden | `python3 scripts/fetch_ecli.py ECLI:NL:HR:2025:667 ECLI:NL:PHR:2024:1131 --uitvoer-map bronnen/` |
| Zoeken op metadata | `python3 scripts/zoek_uitspraken.py --instantie RBAMS --rechtsgebied arbeidsrecht --van 2026-08-01 --tot 2026-08-31 --met-tekst` |
| Oud LJN-nummer naar ECLI | `python3 scripts/zoek_uitspraken.py --ljn AG4158` |
| HvJ-arrest via zaaknummer | `python3 scripts/fetch_celex.py C-131/12` (met `--soort conclusie` voor de conclusie van de A-G) |
| EU-verordening of -richtlijn | `python3 scripts/fetch_celex.py 32016R0679` |
| Europese ECLI | `python3 scripts/fetch_ecli.py ECLI:EU:C:2014:317` |
| Verbinding controleren | `python3 scripts/doctor.py` |

Instantiecodes zijn de ECLI-codes (HR, PHR, RVS, CRVB, CBB, GHAMS, GHARL, GHDHA, GHSHE, RBAMS, RBDHA, ...). Toon ze met `--lijst-instanties`, de rechtsgebieden met `--lijst-rechtsgebieden`.

## Zoeken: wat wel en niet kan

De officiële zoek-API van de Rechtspraak filtert alleen op metadata: instantie, uitspraakdatum, rechtsgebied, soort (uitspraak of conclusie), wijzigingsdatum en LJN. **Zoeken op trefwoorden in de tekst kan niet**; de API negeert zulke parameters zonder foutmelding. `--trefwoord` filtert daarom alleen lokaal op de titel en de ingekorte samenvatting van maximaal 1000 opgehaalde resultaten, en de uitvoer zegt dat erbij. Gebruik voor echt zoeken op inhoud de zoekfunctie op uitspraken.rechtspraak.nl in de browser en haal de gevonden ECLI's daarna hier op.

## Werkwijze

1. Heb je een ECLI of CELEX: haal de uitspraak op. Voor een snelle check eerst `--alleen-meta`.
2. Citeer rechtsoverwegingen met het nummer uit de tekst (`**3.4**` in de uitvoer is r.o. 3.4; bij HvJ-arresten is `**80**` punt 80).
3. Controleer de formele relaties (conclusie A-G, eerdere aanleg) en haal die zo nodig ook op.
4. Vermeld de bron-URL uit de uitvoer.

## Uitvoer

Markdown met: kop (ECLI, titel), metadata (instantie, datum, zaaknummer, procedure, rechtsgebied, vindplaatsen, LJN), formele relaties, inhoudsindicatie, de volledige tekst met behouden paragraafnummers en voetnoten. `--json` geeft de velden als JSON.

## Grenzen

- Niet elke uitspraak staat in de open data; dan volgt een nette foutmelding (exitcode 1). Van oudere uitspraken is soms alleen de metadata gepubliceerd; de uitvoer zegt dat.
- De zoek-API sorteert op wijzigingsdatum, niet op uitspraakdatum, en geeft maximaal 1000 resultaten per verzoek (gebruik `--offset` om verder te bladeren).
- Het zaaknummer-naar-CELEX-mechanisme (C-131/12 wordt 62012CJ0131) is mechanisch; controleer de kop van het opgehaalde document.
- EU-teksten komen als XHTML van het Publicatiebureau; zeer oude documenten zijn niet altijd als HTML beschikbaar.
- De scripts houden minstens 1 seconde tussen verzoeken aan dezelfde server en proberen het opnieuw bij overbelasting (HTTP 429/5xx).

Meer over de gebruikte API's: `references/bronnen.md`.
