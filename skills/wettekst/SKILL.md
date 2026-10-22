---
name: wettekst
description: Haalt de officiële, actuele tekst van een Nederlands wetsartikel op, per lid, uit het Basiswettenbestand (BWB), en desgewenst de tekst zoals die op een eerdere datum gold. Begrijpt notaties als "6:162 BW", "art. 7:673 lid 2 BW", "art. 8:1 Awb" en "art. 350 Sr". Gebruik deze skill wanneer de precieze wettekst ertoe doet (citeren, toetsen aan een lid of onderdeel, controleren of een artikel nog geldt of wat er op een peildatum gold). Niet nodig voor algemene uitleg van een leerstuk zonder dat de letterlijke tekst nodig is.
---

# Wettekst

Citeer wetsartikelen uit de officiële bron, niet uit het geheugen. Wetten veranderen; zeker bedragen, termijnen en artikelnummers. Als het ophalen mislukt, zeg dat.

## Wanneer

- Je citeert of parafraseert een wetsartikel of lid.
- Je moet weten of een artikel nog geldt of vervallen is.
- Je hebt de tekst nodig zoals die gold op een bepaalde datum (bijvoorbeeld de datum van een overeenkomst, ontslag of feit).

## Script

Draai het script vanuit de map van deze skill. Alleen de Python-standaardbibliotheek (3.9+) is nodig.

| Doel | Commando |
|---|---|
| Artikel (alle leden) | `python3 scripts/fetch_wet.py "6:162 BW"` |
| Eén lid | `python3 scripts/fetch_wet.py "art. 7:673 lid 2 BW"` |
| Tekst op een peildatum | `python3 scripts/fetch_wet.py "art. 7:673 lid 2 BW" --datum 2016-01-01` |
| Meerdere artikelen | `python3 scripts/fetch_wet.py "art. 8:1 Awb" "art. 350 Sr" "art. 3:40 BW"` |
| Regeling zonder afkorting | `python3 scripts/fetch_wet.py --bwb BWBR0002448 --artikel 1` (BWB-id staat in de URL op wetten.overheid.nl) |
| Welke versies bestaan er | `python3 scripts/fetch_wet.py "art. 7:673 BW" --versies` |
| JSON-uitvoer | `--json` |
| Verbinding controleren | `python3 scripts/doctor.py` |

Bekende afkortingen: BW (boeken 1 t/m 8, 7A en 10; altijd met boeknummer, "6:162 BW"), Rv, Sr, Sv, Awb, Gw/Grondwet, UAVG, Fw, K/WvK, RO, WOR, Wft, Ow, WVW 1994, Opiumwet, Vw 2000, Uhw, Advocatenwet, Wna, AWR, Wet OB 1968. "sub"/"onder" in een citaat wordt herkend; het script toont dan het volledige lid.

## Werkwijze

1. Haal het artikel op met het citaat zoals de gebruiker het schrijft.
2. Gaat het om feiten uit het verleden, haal dan ook de versie op de relevante datum op (`--datum`) en vergelijk.
3. Neem in je antwoord de versie-regel over ("geldig van ... t/m ...") en de bronlink.
4. Staat er "vervallen", zeg dat en zoek zo nodig de opvolger (bijvoorbeeld via de versie van vóór de vervaldatum en de wetsgeschiedenis).

## Uitvoer

Markdown met: regeling en BWB-id, peildatum, geldigheidsperiode van de gebruikte versie, een link naar wetten.overheid.nl voor de lezer, de artikelkop (en titel, als het artikel die heeft) en de leden als `**1.** ...`, met opsommingen (a., b., ...) op eigen regels.

## Grenzen

- De repository bevat geconsolideerde versies vanaf ongeveer 2002; voor eerdere peildata volgt een foutmelding.
- EU-verordeningen (zoals de AVG) staan niet in het BWB.
- Regelingen worden in hun geheel gedownload (1 tot 6 MB) en daarna lokaal bewaard in `~/.cache/nl-juridische-skills/bwb` (andere map: zet `NLJS_CACHE_DIR`). Het eerste verzoek per regeling duurt daardoor 1 à 2 seconden.
- Het script leest geen webpagina's van wetten.overheid.nl, alleen de officiële XML-repository; de link in de uitvoer is bedoeld voor de lezer.
