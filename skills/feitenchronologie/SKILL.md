---
name: feitenchronologie
description: Maak van een dossier (geplakte tekst of een map met .md/.txt/.pdf/.docx) een chronologische feitentabel met bron per feit, onderscheid vaststaand/stelling van partij, betwist/onbetwist en korte juridische relevantie; signaleert tegenstrijdigheden tussen stukken. Gebruik bij "maak een tijdlijn / chronologie / feitenoverzicht van dit dossier", ter voorbereiding van een processtuk, memo of zitting.
---

# Feitenchronologie

Uitkomst is een **werkdocument voor een jurist**: het geeft weer wat in de stukken staat, geen oordeel over wat bewezen is.

## Wat je nodig hebt
- De stukken: geplakte tekst, of een map/bestanden die de gebruiker aanwijst.
- Voor welke partij je werkt (bepaalt niets aan de feiten, wel aan de kolom "juridische relevantie"). Onbekend? Neutraal blijven.

## Stukken inlezen
- `.md` / `.txt`: gewoon lezen.
- `.pdf`: in Claude Code leest de Read-tool pdf's (met paginanummers). Anders: `pdftotext -layout bestand.pdf -` (als het geïnstalleerd is). Gescande pdf zonder tekstlaag → meld dat; niet raden.
- `.docx`: `python3 scripts/docx_naar_tekst.py bestand.docx` (alleen standaardbibliotheek; nummert alinea's). Op macOS kan ook `textutil -convert txt`.
- Geplakte tekst met meerdere stukken: nummer de stukken zelf in de geplakte volgorde (D1, D2, ...) en verwijs naar punt, artikel of regelnummer binnen het stuk.
- Geef elk stuk een code **D1, D2, ...** met datum, soort, afzender/opsteller. Noteer per feit de plek: eigen nummering van het stuk als die er is (randnummer, punt, r.o.); anders pdf: `p. 2, alinea 3` (alinea = tekstblok tussen lege regels, geteld vanaf de bovenkant van de pagina, briefhoofd en aanhef meegeteld); docx: het alineanummer uit `docx_naar_tekst.py`; e-mail/app: datum en tijdstip van het bericht.

## Stappen
1. **Stukkenlijst** maken (D-codes). Controleer of alle aangewezen bestanden zijn gelezen; noem wat niet leesbaar was.
2. **Feiten per stuk** noteren: één gebeurtenis per rij, met bron (`D3, p. 2` / `D5, r.o. 4` / `D2, alinea 3`).
3. **Datum** per feit, volgens `references/regels.md`: exact (`2024-03-14`), deels (`2024-03`), afgeleid (`± 2024-03-07 (afgeleid: "vorige week" in D4 van 14-03-2024)`) of `onbekend`. Nooit een datum invullen die niet in de stukken staat zonder "afgeleid" en de afleiding.
4. **Status** per feit (zie `references/regels.md`): `vaststaand` / `stelling <partij> — onbetwist` / `stelling <partij> — betwist (<bron betwisting>)` / `stelling <partij>` (reactie wederpartij niet in dossier).
5. **Tegenstrijdigheden**: zelfde gebeurtenis, verschillende datum of inhoud in verschillende stukken → aparte rijen met beide bronnen én een regel in de sectie Tegenstrijdigheden. Niet zelf kiezen welke versie klopt.
6. **Juridische relevantie**: hooguit één korte zin, alleen als er een concreet aanknopingspunt is (termijn, verzuim, klacht, verjaring, bewijs). Gebruik de checklist in `references/regels.md`. Anders leeg laten.
7. **Sorteer** op datum (onbekende data onderaan), en **controleer** met `python3 scripts/naar_csv.py chronologie.md --controleer`. Herstel elke melding.
8. Optioneel: CSV voor Excel met `python3 scripts/naar_csv.py chronologie.md -o chronologie.csv`.

## Output
```
## Stukken
| Code | Datum stuk | Soort | Van / opsteller | Bestand |

## Chronologie
| # | Datum | Gebeurtenis | Bron | Status | Juridische relevantie |
|---|-------|-------------|------|--------|-----------------------|

## Tegenstrijdigheden
- <gebeurtenis>: D2 (p. 1) zegt X; D5 (alinea 12) zegt Y.

## Open punten
- Ontbrekende stukken, onleesbare pagina's, feiten zonder datum, vragen aan de cliënt.
```
Uitgewerkt voorbeeld: `examples/` (zes verzonnen stukken en de chronologie).

## Regels
- **Elk feit heeft een bron.** Geen bron, geen rij.
- Formuleer feitelijk en neutraal; stellingen als stelling ("Volgens Bakker ..."), niet als feit.
- Citeer kort en letterlijk als de formulering ertoe doet (toezegging, opzegging, klacht).
- Geen feiten uit eigen kennis of uit eerdere gesprekken toevoegen.
- Veel stukken (meer dan ± 15)? In Claude Code mag je per stuk een subagent de feiten laten extraheren (zelfde kolommen) en daarna zelf samenvoegen, dedupliceren en tegenstrijdigheden zoeken. In Codex of zonder subagents: stuk voor stuk zelf.

## Beperkingen
- Geen OCR: gescande stukken zonder tekstlaag kan de skill niet lezen.
- "Vaststaand" betekent: blijkt uit het stuk zelf of wordt door niemand in het dossier betwist — niet dat de rechter het zo zal vaststellen.
