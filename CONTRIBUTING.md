# Meebouwen

## Opbouw

```
skills/<naam>/
  SKILL.md            instructies voor het model (wanneer, wat, stappen, grenzen)
  agents/openai.yaml  weergavenaam en aanroepbeleid voor Codex
  scripts/            Python 3.9+, alleen de standaardbibliotheek
  references/ templates/ examples/   waar nodig
  tests/              offline unittests en een live smoketest
shared/               gedeelde clients voor de officiële bronnen
tools/build.py        kopieert shared/ naar de skills die het gebruiken
```

Elke skillmap moet zelfstandig werken als je alleen die map kopieert naar `~/.claude/skills/`
of `~/.codex/skills/`. Verwijs daarom nooit naar bestanden buiten de eigen map.

## Gedeelde code

Code die meerdere skills gebruiken, staat in `shared/`. Welke bestanden een skill nodig heeft,
staat in `skills/<naam>/bundle.txt`. Pas alleen `shared/` aan, nooit de kopieën in `scripts/`,
en draai daarna:

```bash
python3 tools/build.py          # kopieën bijwerken
python3 tools/build.py --check  # controleren dat alles synchroon is
```

## Tests

```bash
# offline, per skill
python3 -m unittest discover -s skills/rechtspraak/tests

# alle skills
for s in skills/*; do python3 -m unittest discover -s "$s/tests"; done

# live tegen de officiële bronnen (vanuit de skillmap)
cd skills/rechtspraak && python3 tests/smoke_live.py
```

## Spelregels

- Alleen officiële, gedocumenteerde openbare bronnen. Identificeer je eerlijk met een eigen
  User-Agent en vraag rustig op.
- Geen echte cliëntgegevens in voorbeelden of tests. Gebruik verzonnen feiten en partijen.
- Een ECLI of artikel in een voorbeeld is opgehaald en gecontroleerd: het bestaat en zegt wat
  er staat.
- Rekenhulpen: elke regel met een unittest, met de bron van de verwachte uitkomst erbij. Toon
  altijd de wettelijke grondslag en een controleregel.
- Alle tekst voor de gebruiker is Nederlands. Code en commentaar mogen Engels zijn.
