---
name: bronvermelding
description: Nederlandse juridische bronvermelding voor wetsartikelen, uitspraken (met ECLI en vindplaats), Kamerstukken, Handelingen, Staatsblad, EU-bronnen, literatuur en voetnoten, in lijn met de Leidraad voor juridische auteurs. Gebruik wanneer iemand vraagt hoe je een bron juridisch correct noteert, een verwijzing wil laten opmaken, of een tekst plakt met de vraag de bronvermelding te controleren ("klopt mijn bronvermelding", "check de verwijzingen").
---

# Bronvermelding

Regels voor het noteren van juridische bronnen in Nederlandse memo's, processtukken en artikelen. De regels volgen de gangbare conventies, in lijn met de *Leidraad voor juridische auteurs*; ze zijn in eigen woorden geformuleerd en de voorbeelden zijn eigen voorbeelden. Deze skill is niet verbonden aan de uitgever of de redactie van de Leidraad.

## Wanneer gebruiken

- **Opmaakmodus**: iemand wil weten hoe een bron te noteren, of geeft gegevens ("HR-arrest van 13 maart 1981 over uitleg") en wil de juiste notatie.
- **Controlemodus**: iemand plakt een tekst en wil weten welke verwijzingen niet kloppen.

## Wat je nodig hebt

Opmaakmodus: de gegevens van de bron (instantie, datum, ECLI, dossiernummer, auteur, titel, jaar, pagina). Ontbreekt een gegeven, vul het niet uit het geheugen in maar laat een zichtbare plek open (`[pagina]`) of zoek het op bij de officiële bron.

Controlemodus: de tekst, en of het om een memo of processtuk (verwijzingen tussen haakjes in de tekst) of om een publicatie met voetnoten gaat. Vraag het als het niet uit de tekst blijkt.

## Stappen

1. Bepaal de context: lopende tekst, tussen haakjes, of voetnoot. Dat bepaalt "artikel" of "art." (zie `references/regels.md` §1). Schrijft de gebruiker voor een tijdschrift of andere publicatie met voetnoten, vraag of de Leidraad wordt gevolgd; zo ja, gebruik in de hoofdtekst de volledige vorm uit §1 en zet bronvermeldingen alleen in de noten (§8).
2. Bepaal per bron het type en pas de regel uit `references/regels.md` toe.
3. **Controlemodus**: loop de tekst van begin tot eind door, verwijzing voor verwijzing, en lever de tabel uit "Output". Wijzig niets aan de inhoud van zinnen, alleen de notatie van bronnen.
4. Ontbreekt in controlemodus een gegeven (bijvoorbeeld de ECLI bij een uitspraak), geef dat aan met een zichtbare plek (`[ECLI]`) tenzij de gebruiker vraagt het op te zoeken. Gegevens zoals een ECLI of datum controleer je alleen als de gebruiker daarom vraagt of als ze onmogelijk zijn (bijvoorbeeld een ECLI met een jaartal na de uitspraakdatum). Controleren kan via `https://data.rechtspraak.nl/uitspraken/content?id=<ECLI>`, of met een skill voor uitspraken als die beschikbaar is.

## Output

Opmaakmodus: de genoteerde bron, klaar om te plakken, en in één zin de toegepaste regel.

Controlemodus: een tabel.

| Nr. | Plaats in de tekst | Staat er | Wordt | Regel |
|---|---|---|---|---|
| 1 | alinea 2, zin 1 | Art. 6:162 BW | artikel 6:162 BW | §1: lopende tekst voluit |

Daarna: punten die je niet kon beoordelen (bijvoorbeeld een ontbrekende paginaverwijzing die je niet kent) en, als gevraagd, de uitkomst van de controle van ECLI's. Geen tabel als alles klopt: dan één regel "Geen correcties nodig."

Voorbeeld van de controlemodus: `examples/voorbeeld-controle.md`.

## Grenzen

- De skill controleert notatie, niet of de bron de stelling in de tekst draagt.
- Kantoren en tijdschriften hebben soms een eigen huisstijl; die gaat voor. Vraag ernaar bij twijfel.
- Een vindplaats in een tijdschrift (nummer, annotator) vul je nooit uit het geheugen aan.
