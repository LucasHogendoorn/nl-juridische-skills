---
name: uitspraak-samenvatten
description: Vat een Nederlandse uitspraak (arrest, vonnis, beschikking, conclusie A-G) samen in een vaste structuur met r.o.-nummers en korte letterlijke citaten. Gebruik bij "vat deze uitspraak samen", "wat heeft de HR beslist in ECLI:NL:...", "maak een korte samenvatting / annotatie van dit arrest", of wanneer de gebruiker een ECLI of geplakte uitspraaktekst geeft en wil weten wat erin staat en wat het betekent voor zijn vraag.
---

# Uitspraak samenvatten

## Wat je nodig hebt
- Een **ECLI** (bijv. `ECLI:NL:HR:1981:AG4158`) of de **geplakte tekst** van de uitspraak.
- Optioneel: de **vraag van de gebruiker** (voor de sectie "Relevantie"). Geen vraag? Laat die sectie weg.
- Gewenste **variant**: standaard, kort (5 regels) of annotatie. Niet genoemd → standaard.

## Stappen
1. **Tekst ophalen** (bij ECLI). Vanuit deze skillmap:
   `python3 scripts/haal_uitspraak.py <ECLI> -o uitspraak.md`
   Bron: officiële open data `https://data.rechtspraak.nl/uitspraken/content?id=<ECLI>`. Rechtsoverwegingen staan in de uitvoer als `**3.2** ...`.
   - Geen volledige tekst gepubliceerd (alleen metadata)? Zeg dat en vat alleen de inhoudsindicatie samen, duidelijk gemarkeerd.
   - Geplakte tekst: gebruik die; vraag de ECLI als hij niet in de tekst staat, of noteer "ECLI onbekend".
   - Geen netwerk of script niet bruikbaar? Vraag de gebruiker de tekst te plakken. **Nooit samenvatten uit geheugen.**
2. **Lees de hele uitspraak** en markeer: feiten (waar de rechter "uitgaat van"), eerdere instanties, de klachten/grieven, de eigen overwegingen van deze rechter, het dictum.
3. **Schrijf de samenvatting** volgens `references/format.md` (standaard, kort of annotatie).
4. **Controleer vóór je antwoordt** (checklist onderaan `references/format.md`). Sla je samenvatting op en draai
   `python3 scripts/controleer_citaten.py samenvatting.md uitspraak.md` — elk citaat van vier woorden of meer moet letterlijk worden gevonden. Herstel of schrap wat niet gevonden wordt. Controleer daarna met de hand dat elk r.o.-nummer bij het citaat hoort en geen hof-overweging als HR-overweging is opgevoerd. Zet geen andere tekst dan citaten tussen dubbele aanhalingstekens.
   Geplakte tekst? Sla die eerst op als `uitspraak.md`.

## Regels
- **Citaten letterlijk en kort** (hooguit ± 40 woorden), tussen aanhalingstekens, met r.o.-nummer. Niet "opgeschoond".
- **Eigen overweging vs. geciteerde overweging.** Een HR-arrest citeert vaak het hof ("rov. 3.6"). Dat is niet het oordeel van de HR. Noem het "hof, rov. 3.6", en de HR-overweging "r.o. 3.1.2".
- **Oude uitspraken zonder r.o.-nummering**: gebruik de nummering zoals die in de tekst staat (bijv. "overweging 2") en zeg dat.
- **Verwijzing naar de conclusie A-G** ("slaagt op de gronden van de conclusie onder 3.23"): vermeld dat de dragende motivering in de conclusie staat. Wil je die inhoud noemen, haal dan de conclusie op (`ECLI:NL:PHR:...`, zie "Formele relaties" in de uitvoer) en citeer daaruit, met vermelding.
- **Art. 81 lid 1 RO**: klachten die met deze formule zijn afgedaan hebben geen motivering; ken ze geen inhoudelijke betekenis toe.
- **Eigen analyse** (betekenis, kritiek) altijd als zodanig herkenbaar. Geen doctrine of latere rechtspraak noemen die je niet in deze sessie hebt gecontroleerd; zeg anders "niet geverifieerd".
- Geanonimiseerde namen (`[eiser 1]`) laat je staan.

## Output
Zie `references/format.md` voor de drie varianten. Voorbeeld van alle drie: `examples/haviltex-HR-1981.md` (ECLI:NL:HR:1981:AG4158).

## Beperkingen
- Alleen Nederlandse ECLI's (`ECLI:NL:`). Voor Europese uitspraken is deze fetcher niet geschikt.
- Niet elke uitspraak is gepubliceerd; de open data bevatten soms alleen metadata.
- Vindplaatsen/annotaties (NJ, AA) staan in de metadata, maar de annotaties zelf zijn niet beschikbaar.
