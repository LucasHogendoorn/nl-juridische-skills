# Werkwijze: zoeken, indelen, controleren

## 1. Zoekroutes

Gebruik er meerdere; één route mist uitspraken.

1. **Het maatgevende arrest en de conclusie van de advocaat-generaal.** Conclusies bij de Hoge Raad bevatten vaak een overzicht van lagere rechtspraak. Haal ze op via `https://data.rechtspraak.nl/uitspraken/content?id=<ECLI>` (ECLI's van conclusies beginnen met `ECLI:NL:PHR:`).
2. **Zoeken op het web** met de kernbegrippen, beperkt tot `uitspraken.rechtspraak.nl`. Gebruik de termen die rechters zelf gebruiken (de roepnaam van het arrest, de woorden van de maatstaf), niet alleen je eigen samenvatting.
3. **Verwijzingen in gevonden uitspraken.** Rechters noemen eerdere uitspraken ("vgl. ..."). Volg die, maar lees ze zelf: een verwijzing zegt niets over hoe de uitspraak werkelijk luidt.
4. **Open data op metadata.** `https://data.rechtspraak.nl/uitspraken/zoeken?type=Uitspraak&date=<van>&date=<tot>&creator=<instantie>&max=<n>` geeft lijsten van ECLI's met korte samenvatting. Deze route kent geen zoeken in de volledige tekst; gebruik haar om een periode of instantie door te lopen.
5. **Rechtspraak van de hoogste rechter na de maatstaf.** Controleer of de Hoge Raad (of een andere hoogste rechter) de maatstaf later heeft verfijnd of gewijzigd.

Noteer per route: zoektermen, datum, aantal bekeken treffers.

## 2. Wat telt als toepassing

Een uitspraak komt in secties 2 tot en met 4 alleen als de rechter de onderzochte maatstaf zelf toepast op de feiten. Niet voldoende:

- de maatstaf wordt alleen in de weergave van een partijstelling genoemd;
- de rechter verwijst er "vgl." naar bij een andere vraag;
- de zaak is vergelijkbaar maar gaat over een andere regel.

Zulke uitspraken gaan hooguit naar sectie 5 als "vergelijkbaar", met die kwalificatie erbij, of blijven weg.

## 3. Indeling op uitkomst

| Groep | Wanneer |
|---|---|
| **Slaagt** | De rechter past de maatstaf toe en de vordering of het verzoek op die grond wordt (grotendeels) toegewezen. |
| **Faalt** | De rechter past de maatstaf toe, maar de vordering strandt op de maatstaf zelf: een uitzondering of tegenbewijs slaagt. |
| **Maatstaf niet bereikt** | De rechter komt aan de inhoudelijke toets niet toe of wijst af op een voorvraag: de toepassingsvoorwaarden van de maatstaf zijn niet vervuld, een termijn is verstreken, de regel is in de tijd niet van toepassing, of er is een procesrechtelijk beletsel. |

Is de maatstaf een verweer of een bevoegdheid van de rechter in plaats van een grondslag voor een vordering (bijvoorbeeld matiging van een boete, art. 6:94 BW, of de klachtplicht, art. 6:89 BW), zeg dan in randnummer 3 waarop "slaagt" en "faalt" slaan (bijvoorbeeld: het beroep op matiging slaagt) en pas de kopjes van secties 2 en 3 daarop aan.

Twee zelfstandige gronden in één uitspraak: deel in naar de grond die de rechter als eerste of als dragend noemt, en noem de tweede grond in de uitkomstzin.

Een voorlopig oordeel (kort geding, "voorshands") en een verstekzaak (wederpartij niet verschenen) blijven meetellen, maar de uitkomstzin vermeldt dat uitdrukkelijk. Zij wegen in de patronen minder zwaar.

## 4. Verbatim-discipline

1. Citaat letter voor letter uit de opgehaalde tekst; weglatingen met `[...]`.
2. Citeer de eigen overweging van de rechter, niet de weergave van een partijstelling of van een eerder arrest. Begint een alinea met "[eiser] stelt ...", citeer dan het deel waarin de rechter oordeelt. Steunt je uitkomstzin toch op het deel dat een partijstelling weergeeft (bijvoorbeeld bij verstek), zeg dat in de uitkomstzin.
3. Het r.o.-nummer lees je af in de tekst. Staat het citaat midden in een lange alinea, noem dan het nummer van die alinea.
4. Partijnamen: gebruik de rol ("de werkgever", "de werknemer") of de naam zoals die in de uitspraak staat. Geen namen uit je geheugen.
5. Klopt iets in de uitspraak zelf niet (bijvoorbeeld een verkeerde datum van een aangehaald arrest), neem het citaat ongewijzigd over en meld de onjuistheid in de zoekverantwoording.

## 5. Controlelijst vóór levering

1. Elke ECLI is opgehaald en gelezen; instantie en datum komen uit de metadata van de uitspraak.
2. Elk citaat staat letterlijk in de opgehaalde tekst en is een oordeel van de rechter, geen partijstelling.
3. Elk r.o.-nummer is afgelezen.
4. Elke uitspraak in secties 2-4 past de maatstaf zelf toe; de indeling volgt de tabel in §3.
5. Binnen elke groep chronologisch oplopend; randnummers doorlopend.
6. Elk randnummer heeft de vier elementen: kop, casus, citaat, "Uitkomst:".
6a. De casusbeschrijving is gecontroleerd tegen de feitenparagrafen van de uitspraak (data, wie deed wat), niet samengesteld uit losse fragmenten of de inhoudsindicatie.
7. Kort geding en verstek zijn in de uitkomstzin vermeld.
8. Een lege groep is weggelaten en in de laatste sectie benoemd; de overige secties zijn doorgenummerd (geen sprong van 2 naar 4).
9. Sectie 5 herhaalt geen feiten of citaten maar verwijst naar randnummers.
10. Geen uitspraken over "de" rechtspraak die verder gaan dan de gevonden uitspraken dragen. Elke zin over een patroon noemt het aantal gevonden uitspraken waarop hij steunt ("in de drie gevonden uitspraken ...").
11. Nagegaan of de maatstaf later door de hoogste rechter of de wetgever is gewijzigd; zo niet nagegaan, dan staat dat in de zoekverantwoording. Conclusies van de advocaat-generaal die in de treffers verschijnen, zijn gelezen of staan in de zoekverantwoording als niet gelezen.
11a. Elk wetsartikel dat je in eigen tekst noemt, is gecontroleerd (zie §6) of gemarkeerd als `[niet geverifieerd]`.
12. Geen opsommingstekens, geen voetnoten, geen gedachtestreepjes in eigen tekst. In lopende tekst "artikel", tussen haakjes "art.".

## 6. Wetsartikelen controleren

Gebruik de `wettekst`-skill als die is geïnstalleerd. Zo niet: haal geen pagina's van wetten.overheid.nl op (de site sluit AI-agents uit in haar robots.txt), maar gebruik de officiële KOOP-bestanden. Zoek de geldende versie met `https://zoekservice.overheid.nl/sru/Search?x-connection=BWB&operation=searchRetrieve&version=1.2&maximumRecords=5&query=dcterms.identifier==<BWB-id> and overheidbwb.geldigheidsdatum==<JJJJ-MM-DD>` (query URL-gecodeerd), haal het XML-bestand uit `overheidbwb:locatie_toestand` op en zoek het `<artikel>` met het juiste `<kop><nr>`. BW Boek 7 is `BWBR0005290`, Boek 6 `BWBR0005289`, Rv `BWBR0001827`. In de output mag je voor lezers naar wetten.overheid.nl linken.
