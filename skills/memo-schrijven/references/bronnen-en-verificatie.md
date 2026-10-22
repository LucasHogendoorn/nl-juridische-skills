# Bronnen en verificatie

## Rangorde van bronnen

Het memo bouwt de rechtsregel op van boven naar beneden:

1. **Wet en regelgeving**, inclusief EU-recht en verdragen. Het artikel is het vertrekpunt; de wettekst gaat voor elke samenvatting ervan.
2. **Hoge Raad** (en de andere hoogste rechters: Hof van Justitie EU, Afdeling bestuursrechtspraak Raad van State, Centrale Raad van Beroep, College van Beroep voor het bedrijfsleven). Deze rechters stellen de maatstaf vast.
3. **Lagere rechtspraak** (hoven, rechtbanken). Die past de maatstaf toe. Een feitenrechter is geen precedent: schrijf "het hof paste de maatstaf toe", niet "het hof bepaalde dat de regel is".
4. **Literatuur** (handboeken, artikelen, annotaties). Ondersteunend, nooit de enige basis voor een regel die ook in wet of rechtspraak te vinden is.

Bij een contractuele vraag gaat de tekst van de overeenkomst voor het regelend recht: het algemene recht vult aan waar de overeenkomst zwijgt, tenzij van een wettelijke bepaling niet mag worden afgeweken.

## Waar je bronnen ophaalt

| Bron | Officiële vindplaats |
|---|---|
| Nederlandse uitspraken | `https://data.rechtspraak.nl/uitspraken/content?id=<ECLI>` (volledige tekst als XML) |
| Wetten en regelingen | het officiële BWB-bestand van KOOP (zie hieronder); in de output mag je naar `https://wetten.overheid.nl` linken |
| Kamerstukken, Staatsblad, Staatscourant | `https://zoek.officielebekendmakingen.nl` |
| EU-wetgeving en HvJ-arresten | `https://eur-lex.europa.eu` of `http://publications.europa.eu/resource/celex/<CELEX>` |
| EHRM | `https://hudoc.echr.coe.int` |

Heb je een skill voor uitspraken of wetteksten tot je beschikking (bijvoorbeeld `rechtspraak` of `wettekst`), gebruik die. Zo niet: WebFetch op de vindplaatsen hierboven. WebSearch alleen om een ECLI of vindplaats te vinden, nooit als bron voor de inhoud zelf.

**Wettekst zonder `wettekst`-skill.** Haal de pagina's van wetten.overheid.nl niet zelf op: de site sluit AI-agents uit in haar robots.txt. Gebruik de officiële KOOP-bestanden:

1. Zoek de versie die geldt op de relevante datum: `https://zoekservice.overheid.nl/sru/Search?x-connection=BWB&operation=searchRetrieve&version=1.2&maximumRecords=5&query=dcterms.identifier==<BWB-id> and overheidbwb.geldigheidsdatum==<JJJJ-MM-DD>` (query URL-gecodeerd). Het antwoord bevat in `overheidbwb:locatie_toestand` de URL van het XML-bestand.
2. Haal dat XML-bestand op (`https://repository.officiele-overheidspublicaties.nl/bwb/<BWB-id>/...xml`) en zoek het `<artikel>` waarvan `<kop><nr>` het artikelnummer is. Negeer de `<meta-data>`-elementen.
3. BWB-id's van veelgebruikte wetten: BW Boek 6 `BWBR0005289`, BW Boek 7 `BWBR0005290`, Rv `BWBR0001827`, Awb `BWBR0005537`. Een ander id vind je via dezelfde SRU met `query=overheidbwb.titel any "<citeertitel>"`; dat geeft veel treffers, kies het record waarvan `dcterms:title` precies de citeertitel is.

Deze bestanden zijn groot (enkele MB); haal ze één keer op per wet.

## Verbatim-discipline

1. **Alleen citeren wat je hebt opgehaald.** Een citaat tussen aanhalingstekens of in een blokcitaat komt letter voor letter uit de opgehaalde tekst, inclusief interpunctie. Weglatingen met `[...]`, toevoegingen tussen vierkante haken.
2. **R.o.-nummers uit de tekst zelf.** Het rechtsoverwegingsnummer (bijvoorbeeld r.o. 3.4) lees je af in de opgehaalde uitspraak. Oudere arresten hebben soms alleen genummerde alinea's; noem dan dat nummer zoals het in de tekst staat.
3. **Partijnamen en roepnamen** (zoals *Haviltex*) alleen als ze in de opgehaalde tekst of de kop van de uitspraak staan. Staat er `[eiser]`, dan gebruik je geen bijnaam uit je geheugen.
4. **Wettekst van de geldende versie.** Controleer welke versie geldt op de relevante datum (stap 1 hierboven, of de `wettekst`-skill). Is de wet gewijzigd sinds de relevante feiten, benoem dan welke versie je toepast.
5. **Literatuur**: noem een handboek of artikel alleen als je de passage zelf hebt gelezen. Kun je de vindplaats (nummer, pagina) niet zelf zien, laat de bron weg.
6. **Wat je niet kunt verifiëren**, markeer je in de tekst met `[niet geverifieerd]` en neem je op in het beslissingenlog. Een ongemarkeerde onzekere bron is de ernstigste fout die dit memo kan bevatten.

## Bekende fouten van taalmodellen in juridisch werk

Deze fouten komen steeds terug. Controleer er actief op.

1. **Verzonnen of verwisselde ECLI's.** Een ECLI die plausibel oogt maar niet bestaat, of bestaat maar over iets anders gaat. Elke ECLI ophalen en de inhoudsindicatie lezen.
2. **Citaat uit het geheugen.** Een "letterlijke" rechtsoverweging die in de uitspraak anders luidt. Alleen kopiëren uit de opgehaalde tekst.
3. **Bijnaam op basis van associatie.** Een arrestnaam die bij het onderwerp past maar niet bij deze ECLI. Alleen namen uit de tekst.
4. **Handboekclaim zonder tekst.** "Asser stelt ..." zonder dat je de passage hebt gezien. Weglaten.
5. **Verzachting als zekerheid.** Een uitspraak die "in lijn met" of "vergelijkbaar met" de regel is, gepresenteerd alsof zij de regel toepast. Benoem de werkelijke verhouding: toegepast, vergelijkbaar, of anders.
6. **Feitenrechter als maatstaf.** Een rechtbankvonnis gepresenteerd als vaste regel. Alleen de Hoge Raad (of een andere hoogste rechter) stelt de maatstaf.
7. **Verouderde wettekst.** Een artikel in een oude redactie, of een vernummerd artikel. Geldende versie ophalen.

Bij twijfel: weglaten of markeren. Een eerlijk gat is bruikbaar voor de jurist; een verzonnen invulling niet.
