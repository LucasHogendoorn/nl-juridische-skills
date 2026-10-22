# Gebruikte bronnen en hun mogelijkheden

Vastgesteld met live verzoeken op 23 september 2026.

## Open data van de Rechtspraak (data.rechtspraak.nl)

- Uitspraak: `https://data.rechtspraak.nl/uitspraken/content?id=<ECLI>`; met `&return=META` alleen metadata (de inhoudsindicatie staat dan in `dcterms:abstract`).
- Onbekende ECLI: HTTP 404.
- Zoeken: `https://data.rechtspraak.nl/uitspraken/zoeken?...` met de parameters
  `creator` (instantie-URI), `type` (`Uitspraak`/`Conclusie`), `date` (1x = exacte dag, 2x = periode), `subject` (rechtsgebied-URI), `modified`, `return=DOC` (alleen met tekst), `replaces` (LJN), `max` (maximaal 1000), `from` (offset) en `sort` (`ASC`/`DESC`, op wijzigingsdatum).
  Dezelfde parameter meermaals = OF; verschillende parameters = EN.
- Er is geen parameter voor zoeken op trefwoord. Getest: `q`, `query`, `zoekterm`, `text`, `searchterm`, `keyword`, `trefwoord`, `term`, `search`, `fulltext`, `title`, `zaaknummer` en `inhoudsindicatie` veranderen het aantal resultaten niet; ze worden genegeerd.
- Waardelijsten: `https://data.rechtspraak.nl/Waardelijst/Instanties` en `.../Waardelijst/Rechtsgebieden`.
- Voorwaarden van de Rechtspraak (open data): niet meer dan 10 verzoeken per seconde; de scripts blijven daar ruim onder.

## Publicatiebureau van de EU (publications.europa.eu)

- `https://publications.europa.eu/resource/celex/<CELEX>` en `https://publications.europa.eu/resource/ecli/<ECLI:EU:...>`, met `Accept: text/html, application/xhtml+xml` en `Accept-Language: nld` (of `eng`, `fra`, `deu`).
- Zonder `Accept`-voorkeur voor HTML stuurt de server RDF-metadata terug (voor de AVG ruim 60 MB); de scripts vragen daarom altijd om HTML.
- CELEX-opbouw voor rechtspraak: `6` + jaar + `CJ` (arrest HvJ), `CC` (conclusie A-G), `CO` (beschikking), `TJ` (arrest Gerecht) + zaaknummer in 4 cijfers. Voorbeeld: C-131/12 wordt 62012CJ0131.
