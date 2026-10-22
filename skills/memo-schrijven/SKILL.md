---
name: memo-schrijven
description: Schrijf een Nederlands juridisch memo (vijf vaste secties, doorlopende randnummers, bronnen inline) op basis van feiten die de gebruiker aanlevert. Gebruik wanneer een advocaat of jurist vraagt om "een memo", "een juridisch advies in memovorm" of "zet dit uit in een memo" over een Nederlandse rechtsvraag. Niet voor losse bronvermeldingsvragen of een overzicht van rechtspraak zonder advies.
---

# Memo schrijven

Levert een **concept** voor een jurist. De jurist blijft verantwoordelijk voor inhoud en bronnen.

## Wanneer gebruiken

Een rechtsvraag naar Nederlands recht (eventueel met EU-recht) waarop de gebruiker een onderbouwd antwoord in memovorm wil: kader, rechtspraak, toepassing, advies, conclusie.

## Wat je nodig hebt

1. De feiten (wie in welke rol, wat is er gebeurd, wat wordt gevorderd of betwist).
2. De tekst van de relevante contractsbepaling(en), als het om een overeenkomst gaat. Vraag erom als die ontbreekt; parafraseer een clausule nooit uit het hoofd.
3. Voor wie het memo is (cliënt, kantoorgenoot) en namens welke partij je schrijft.

Ontbreekt iets dat de uitkomst bepaalt, vraag het één keer, kort. Kan de gebruiker het niet leveren, schrijf dan door en benoem het in het memo als ontbrekend feit.

## Stappen

1. **Rechtsvraag vastzetten.** Formuleer de rechtsvraag in één zin en de toepasselijke regels (artikelen, leerstukken) met hun vereisten.
2. **Bronnen ophalen.** Volg `references/bronnen-en-verificatie.md`: rangorde van bronnen, alleen citeren wat je zelf hebt opgehaald, r.o.-nummers uit de opgehaalde tekst. Als in je omgeving een skill voor uitspraken of wetteksten beschikbaar is (bijvoorbeeld `rechtspraak` of `wettekst` uit dit pakket), mag je die gebruiken. Zonder die skills: haal zelf op via WebFetch/WebSearch bij de officiële bronnen uit dat bestand. Wat je niet kunt ophalen, markeer je als `[niet geverifieerd]` of laat je weg.
3. **Eén lijn kiezen.** Bepaal vóór het schrijven welk leerstuk dragend is, welke lijn het antwoord draagt en welke tegenargumenten sterk genoeg zijn om te behandelen. Zwakke tegenargumenten gaan naar het beslissingenlog, niet in het memo.
4. **Schrijven.** Gebruik `templates/memo-template.md` en de regels in `references/stijlgids.md`.
5. **Beslissingenlog.** Vul `templates/beslissingenlog-template.md` in: wat je hebt behandeld, weggelaten en waarom, en welke bronnen niet geverifieerd zijn.
6. **Zelfcontrole.** Loop `references/zelfcontrole.md` volledig door en herstel wat faalt voordat je levert.

In Claude Code kun je bronnen parallel laten ophalen door subagents. In Codex of zonder subagents: haal ze één voor één zelf op.

## Output

Twee blokken, in deze volgorde:

1. **Het memo**: metadata (Aan, Van, Datum, Betreft), daarna exact vijf secties: Rechtsvraag en relevante bepaling(en); Juridisch kader en rechtspraak; Toepassing op de casus; Advies; Conclusie. Doorlopende randnummers, bronnen inline tussen haakjes, geen voetnoten, geen opsommingstekens.
2. **Beslissingenlog** (voor de gebruiker, niet voor de lezer van het memo), afgesloten met de lijst niet-geverifieerde bronnen (of "geen").

Een volledig uitgewerkt voorbeeld op verzonnen feiten staat in `examples/voorbeeld-huur-cv-ketel.md`.

## Grenzen

- Geen verzonnen ECLI's, r.o.-nummers, citaten, partijnamen van arresten of literatuurvindplaatsen. Liever een gat dat je benoemt dan een plausibele invulling.
- Literatuur alleen noemen als je de tekst zelf hebt gelezen; anders weglaten.
- Het memo is een concept. Controle van bronnen en eindoordeel liggen bij de jurist.
- Geen processtuk of brief: daarvoor zijn andere vormen nodig.
