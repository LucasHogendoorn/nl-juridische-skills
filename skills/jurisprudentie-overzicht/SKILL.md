---
name: jurisprudentie-overzicht
description: Maak een overzicht van Nederlandse (en eventueel EU-)rechtspraak over één rechtsvraag, met per uitspraak één randnummer, gesorteerd op uitkomst (vordering slaagt, faalt, of de maatstaf wordt niet bereikt), gevolgd door patronen en toepassing op de casus. Gebruik wanneer een jurist vraagt om "een jurisprudentieoverzicht", "wat zeggen rechters over X", "zet de rechtspraak op een rij" of "hoe vaak wordt Y toegewezen".
---

# Jurisprudentie-overzicht

Levert een **concept** voor een jurist. Het overzicht is zo volledig als de zoekweg; die zoekweg wordt altijd vermeld.

## Wanneer gebruiken

Een jurist wil weten hoe rechters een bepaalde regel of maatstaf toepassen en in welke gevallen een vordering slaagt of strandt, eventueel toegespitst op een eigen zaak. Voor een uitgewerkt advies met één lijn is een memo geschikter.

## Wat je nodig hebt

1. De rechtsvraag of maatstaf (bijvoorbeeld "wanneer moet een werkgever meewerken aan beëindiging van een slapend dienstverband").
2. Optioneel: de feiten van de eigen zaak, voor de toepassing in de laatste sectie.
3. Optioneel: periode, instanties, of uitspraken die de gebruiker al kent.

## Stappen

1. **Maatstaf vastzetten.** Zoek de wetsbepaling of het arrest van de hoogste rechter dat de maatstaf geeft. Haal de tekst op en citeer de maatstaf letterlijk in randnummer 2.
2. **Uitspraken zoeken.** Volg `references/werkwijze.md` (zoekroutes). Noteer elke zoekopdracht voor de zoekverantwoording.
3. **Elke uitspraak ophalen en lezen.** Via `https://data.rechtspraak.nl/uitspraken/content?id=<ECLI>`, of met een skill voor uitspraken als die in je omgeving beschikbaar is (bijvoorbeeld `rechtspraak` uit dit pakket). Een uitspraak die je niet hebt gelezen, komt niet in het overzicht.
4. **Indelen.** Per uitspraak: past de rechter de maatstaf werkelijk toe, en met welke uitkomst? Indeling in drie groepen volgens `references/werkwijze.md`. Uitspraken die de maatstaf niet toepassen maar wel verwant zijn, gaan hooguit naar de laatste sectie als "vergelijkbaar".
5. **Schrijven.** Gebruik `templates/overzicht-template.md`. Binnen elke groep chronologisch oplopend.
6. **Controle.** Loop de controlelijst in `references/werkwijze.md` door.

In Claude Code kun je uitspraken parallel laten ophalen en indelen door subagents. In Codex of zonder subagents: doe het één voor één zelf.

## Output

1. **Het overzicht**: metadata, daarna de secties uit de template: vraagstelling en maatstaf; slaagt; faalt; maatstaf niet bereikt; patronen, toepassing en advies. Een lege groep laat je weg en je zegt dat in de laatste sectie.
2. **Zoekverantwoording**: welke zoekroutes en termen, hoeveel treffers bekeken, welke uitspraken bewust niet opgenomen en waarom.

Voorbeeld op verzonnen cliëntfeiten met echte, gecontroleerde uitspraken: `examples/voorbeeld-slapend-dienstverband.md`.

## Grenzen

- Geen verzonnen ECLI's, datums, r.o.-nummers of citaten. Wat niet is opgehaald, staat er niet in.
- Het overzicht is geen volledige telling van alle rechtspraak. Zeg nooit "de rechtspraak is eenduidig" of "in x procent van de zaken" op basis van een steekproef.
- Een uitspraak van een feitenrechter vestigt geen maatstaf; alleen de hoogste rechter doet dat.
- Latere wetswijzigingen of hogere rechtspraak die de maatstaf veranderen, moeten apart worden nagegaan; benoem het als je dat niet hebt gedaan.
