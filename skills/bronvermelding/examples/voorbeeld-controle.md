# Voorbeeld: controlemodus

De tekst is verzonnen. De genoemde uitspraken, het Kamerstuk en de Handelingen zijn echt en gecontroleerd bij data.rechtspraak.nl en repository.overheid.nl.

## Verzoek van de gebruiker

> Klopt de bronvermelding in deze passage uit mijn memo? Verwijzingen staan tussen haakjes, geen voetnoten.
>
> (1) Art. 7:669 lid 3 sub b BW geeft de werkgever de mogelijkheid op te zeggen na twee jaar ziekte. (2) Volgens Xella, HR 08-11-2019, ECLI:NL:HR:2019:1734 r.o. 2.7.3, moet de werkgever dan in beginsel meewerken aan een beëindigingsvoorstel (artikel 7:611 jo. 7:669 BW). (3) De wetgever wilde slapende dienstverbanden tegengaan (Kamerstukken II 2013-2014, 33 818, nr. 3, blz. 12 e.v.; Handelingen TK 2013/14, nr. 54). (4) Het hof Den Bosch paste de maatstaf toe (ECLI:NL:GHSHE:2021:2156, a.w., r.o. 3.4.5).

## Output

| Nr. | Plaats in de tekst | Staat er | Wordt | Regel |
|---|---|---|---|---|
| 1 | zin 1 | Art. 7:669 lid 3 sub b BW | Artikel 7:669 lid 3 onder b BW | §1: lopende tekst "artikel"; §2: "onder", niet "sub" |
| 2 | zin 2 | Volgens Xella, HR 08-11-2019, ECLI:NL:HR:2019:1734 r.o. 2.7.3 | Volgens HR 8 november 2019, ECLI:NL:HR:2019:1734, r.o. 2.7.3 (*Xella*) | §3: datum voluit; komma voor r.o.; roepnaam cursief tussen haakjes aan het eind |
| 3 | zin 2 | (artikel 7:611 jo. 7:669 BW) | (art. 7:611 en 7:669 BW) | §1: tussen haakjes "art."; §2: geen "jo." |
| 4 | zin 3 | Kamerstukken II 2013-2014, 33 818, nr. 3, blz. 12 e.v. | Kamerstukken II 2013/14, 33818, nr. 3, p. 12-[laatste pagina] | §6: vergaderjaar met schuine streep, dossiernummer zonder spatie; §7: "p.", geen "blz."; geen "e.v." maar exacte pagina's |
| 5 | zin 3 | Handelingen TK 2013/14, nr. 54 | Handelingen II 2013/14, nr. 54, item [nummer] | §6: "II" voor de Tweede Kamer; item toevoegen |
| 6 | zin 4 | (ECLI:NL:GHSHE:2021:2156, a.w., r.o. 3.4.5) | (Hof 's-Hertogenbosch 8 juli 2021, ECLI:NL:GHSHE:2021:2156, r.o. 3.4.5) | §3: instantie en datum vóór de ECLI; nooit "a.w." |

Niet te beoordelen zonder bron: de laatste pagina van de passage in het Kamerstuk (correctie 4) en het itemnummer van de Handelingen (correctie 5). Het item waarin dossier 33818 plenair werd behandeld op 13 februari 2014 is item 9 (repository.overheid.nl, `h-tk-20132014-54-9`); of de gebruiker dat item bedoelt, blijkt niet uit de tekst.

Opmerking buiten de notatie: in zin 4 staat "Het hof Den Bosch". De officiële naam is Gerechtshof 's-Hertogenbosch; in de verwijzing is die gebruikt, de zin zelf is niet gewijzigd.
