---
name: wederpartij
description: Lees een concept-memo, advies of processtuk zoals de advocaat van de wederpartij het zou lezen en lever gestructureerde bezwaren (objectie, vindplaats in het stuk, waarom, sterkte, wat nodig is om te weerleggen) of een uitdrukkelijke PASS. Alleen vinden, niet herschrijven. Gebruik wanneer een jurist vraagt "waar gaat de wederpartij in hakken", "doe een tegenlezing", "pleit hier eens tegen" of "red team dit stuk".
---

# Wederpartij-review

Een tegenlezing als hulpmiddel voor een jurist. De bezwaren zijn geen oordeel over de uitkomst van de zaak.

## Wanneer gebruiken

Er ligt een concept (memo, advies, dagvaarding, conclusie, verweerschrift, sommatie) en de jurist wil weten waar het kwetsbaar is voordat het de deur uitgaat.

## Wat je nodig hebt

1. Het stuk zelf, liefst met randnummers of alineanummers.
2. Voor wie het stuk is geschreven en welke uitkomst het bepleit.
3. Optioneel: de onderliggende feiten of stukken, en uitspraken of bronnen die de gebruiker al heeft.

## Stappen

1. **Lees het hele stuk** en noteer per randnummer de dragende stellingen en waarop elk steunt (wet, uitspraak, feit, niets). Heeft het stuk geen randnummers, tel dan de alinea's en gebruik die nummering.
2. **Neem de tegenovergestelde positie in.** Zegt het stuk "toewijsbaar", zoek waarom afwijsbaar; zegt het "geen aansprakelijkheid", zoek waarom wel.
3. **Loop de checklist in `references/werkwijze.md` door**: ontbrekende vereisten, bewijslast, termijnen en procesrecht, bronnen die niet zeggen wat het stuk beweert, feitenrechter als maatstaf, weggelaten feiten, ontbrekende tegenargumenten.
4. **Controleer de bronnen van het stuk** waar dat kan: haal aangehaalde uitspraken en wetsartikelen op en kijk of ze zeggen wat het stuk stelt. Gebruik de skills `rechtspraak` of `wettekst` als die zijn geïnstalleerd; anders de officiële routes in `references/werkwijze.md`. Een bezwaar dat op een eigen bron steunt, mag alleen een bron noemen die je hebt opgehaald.
5. **Schrijf de bezwaren** volgens `templates/bezwaren-template.md`, sterkste eerst. Of schrijf een PASS als je na zorgvuldig lezen niets substantieels vindt.
6. **Stop.** Herschrijf het stuk niet, ook niet als de oplossing voor de hand ligt.

Zonder subagents of in Codex werkt dit hetzelfde: het is één doorlopende lezing.

## Output

Een lijst van ten hoogste 12 bezwaren, elk met: objectie, vindplaats in het stuk (randnummer en korte letterlijke aanhaling), waarom het werkt, sterkte (**kritiek**, **wezenlijk** of **beperkt**), en wat nodig is om het te weerleggen. Of één regel `PASS: geen wezenlijke bezwaren`, met een korte motivering.

Voorbeeld: `examples/voorbeeld-huurder-zelf-vervangen.md`.

## Grenzen

- Alleen vinden. Geen herschreven passages, geen "zo moet het luiden".
- Geen stijlbezwaren, tenzij de formulering juridisch schaadt (bijvoorbeeld "in beginsel" zonder de uitzondering te noemen die de wederpartij zal inroepen).
- Geen verzonnen tegen-uitspraken of literatuur. Kun je een tegenargument niet met een opgehaalde bron onderbouwen, formuleer het dan als redenering of feitelijk punt en zeg dat er geen bron bij is.
- Vind je minder dan drie bezwaren, lees het stuk dan nog één keer langs de checklist. Blijven het er minder, lever wat je hebt en zeg dat. Vul nooit aan met zwakke bezwaren; een PASS is beter dan een verzonnen bezwaar.
