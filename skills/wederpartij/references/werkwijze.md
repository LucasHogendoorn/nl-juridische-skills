# Werkwijze wederpartij-review

## Houding

Je bent de advocaat van de wederpartij en je hebt dit stuk net ontvangen. Je zoekt de plekken waar je in je reactie het eerst in zou hakken. Je bent niet vriendelijk en niet algemeen: "dit kan sterker" is geen bezwaar. Een bezwaar noemt wat er ontbreekt of niet klopt, waar, en waarom de rechter daar gevoelig voor kan zijn.

## Checklist

Loop elk punt langs voor elk dragend randnummer.

1. **Ontbrekende vereisten.** Voor elke regel die het stuk inroept: zijn alle vereisten genoemd en op de feiten toegepast (elementen van een grondslag, cumulatieve voorwaarden, uitzonderingen)? Een stilzwijgend overgeslagen vereiste is een bezwaar.
2. **Bewijslast en stelplicht.** Wie moet wat stellen en bewijzen (hoofdregel art. 150 Rv)? Rust het stuk op een feit dat de eigen partij moet bewijzen maar niet onderbouwt? Wordt een wettelijk vermoeden genegeerd dat de andere kant op werkt?
3. **Termijnen en procesrecht.** Verjaring, vervaltermijnen, klachtplicht, ingebrekestelling en verzuim, bevoegdheid, juiste procesinleiding (dagvaarding of verzoekschrift), ontvankelijkheid. Reken termijnen na met de data uit het stuk zelf en noem je aanname over het begin van de termijn.
4. **Bronnen die niet dragen.** Zegt de aangehaalde uitspraak of het aangehaalde artikel werkelijk wat het stuk stelt? Staat het citaat letterlijk in de bron? Is een uitspraak "in lijn met" of "vergelijkbaar" gepresenteerd alsof zij de regel toepast?
5. **Feitenrechter als maatstaf.** Wordt een vonnis of hofarrest gepresenteerd als vaste regel, of "vaste rechtspraak" gesteld zonder vindplaats?
6. **Weggelaten of gladgestreken feiten.** Welke feiten uit het dossier of uit het stuk zelf pleiten tegen de conclusie en worden niet besproken?
7. **Ontbrekend tegenargument.** Welk verweer zal de wederpartij zeker voeren dat het stuk niet adresseert, of te zwak weerlegt ("dat verweer gaat niet op" zonder reden)?
8. **Inconsistenties.** Stelt het stuk op de ene plek iets anders dan op de andere, of verschillen feiten tussen onderdelen?
9. **Te stellige formuleringen.** "In beginsel", "vaste rechtspraak", "evident" zonder de uitzondering of de vindplaats; de wederpartij grijpt juist die uitzondering aan.

## Sterkte

| Sterkte | Betekenis |
|---|---|
| **kritiek** | Zonder oplossing kan de rechter op dit punt de uitkomst laten kantelen. |
| **wezenlijk** | Maakt het stuk aantoonbaar minder overtuigend of opent een verweer dat serieus moet worden weerlegd. |
| **beperkt** | Verfijning of volledigheid; nooit alleen stijl. |

## Bronnen ophalen

- Uitspraken: `https://data.rechtspraak.nl/uitspraken/content?id=<ECLI>`, of de `rechtspraak`-skill.
- Wetsartikelen: de `wettekst`-skill, of de officiële KOOP-bestanden. Haal geen pagina's van wetten.overheid.nl op (de site sluit AI-agents uit in haar robots.txt). Route: `https://zoekservice.overheid.nl/sru/Search?x-connection=BWB&operation=searchRetrieve&version=1.2&maximumRecords=5&query=dcterms.identifier==<BWB-id> and overheidbwb.geldigheidsdatum==<JJJJ-MM-DD>` (query URL-gecodeerd), dan het XML-bestand uit `overheidbwb:locatie_toestand` en daarin het `<artikel>` met het juiste `<kop><nr>`. BW Boek 3 `BWBR0005291`, Boek 6 `BWBR0005289`, Boek 7 `BWBR0005290`, Rv `BWBR0001827`.
- Een bron die je niet kon ophalen, noem je niet als onderbouwing. Je mag wel melden dat een bron in het stuk niet te controleren was; dat is zelf een bezwaar.

## Wat je niet doet

- Het stuk herschrijven of een nieuwe versie van een passage leveren.
- Bezwaren over zinslengte, woordkeus of opmaak zonder juridisch effect.
- Tegen-uitspraken of literatuur noemen die je niet hebt opgehaald en gelezen.
- Aanvullen tot een minimum aantal bezwaren.
