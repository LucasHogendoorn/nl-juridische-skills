---
name: wettelijke-rente
description: Rekenhulp voor wettelijke rente (art. 6:119 BW) en wettelijke handelsrente (art. 6:119a BW) over een hoofdsom en periode, met jaarlijkse rente-op-rente en optionele deelbetalingen (toerekening art. 6:44 BW). Gebruik bij "bereken de wettelijke rente", "hoeveel rente over deze factuur", "handelsrente sinds vervaldatum", incasso- en sommatieberekeningen.
---

# Wettelijke rente

Rekenhulp, geen advies. De uitkomst altijd zelf controleren.

## Wanneer
- Niet-handelstransacties en schadevergoeding: art. 6:119 BW (percentages 2002 tot nu, per Staatsblad).
- Handelsovereenkomsten gesloten op of na 16 maart 2013: art. 6:119a BW (ECB-rente + 8 procentpunten).

## Invoer
- `--soort niet-handel|handel`, `--hoofdsom`, `--vanaf` (eerste rentedag), `--tot` (laatste rentedag, bijv. betaaldag).
- Optioneel: `--kosten` (worden bij betaling eerst afgelost, dragen geen rente), `--betaling DATUM:BEDRAG`
  (herhaalbaar), `--dagbasis 365|jaar`, `--json`.
- Bij handel verplicht: `--overeenkomst-datum`.

```
python3 scripts/wettelijke_rente.py --soort niet-handel --hoofdsom 12500 --vanaf 2019-03-01 --tot 2026-03-01 --kosten 875 --betaling 2022-06-15:5000
```

## Voorbeeld
Hoofdsom EUR 10.000 vanaf 1-1-2025 tot en met 31-12-2026: 2025 6% = EUR 600,00, daarna rente-op-rente;
2026 4% over EUR 10.600 = EUR 424,00; totaal EUR 1.024,00.

## Uitvoer
Uitkomst (rente, open hoofdsom, rente en kosten), elke rekenstap met percentage en Staatsblad/ECB-bron,
juridische grondslag, aandachtspunten en "Controleer de uitkomst zelf; dit is een rekenhulp, geen advies."
Geef ook de aandachtspunten door.

## Grenzen
- Niet-handel vanaf 1-1-2002; alles tot en met 31-12-2026 (tabel bijgewerkt tot 23-9-2026).
- Handelsrente alleen voor overeenkomsten gesloten op of na 16-3-2013 (overgangsrecht rond de verhoging
  van 7 naar 8 procentpunten is onduidelijk; het script weigert).
- Geen bedongen rente (art. 6:119 lid 3, 6:119a lid 9), geen overheidstransacties (art. 6:119b),
  geen rente over kosten, geen buitengerechtelijke incassokosten berekenen.
- Welke dag de rente begint te lopen (verzuim, vervaldag, factuur + 30 dagen) bepaalt de gebruiker.
- Rekenconventies (dagtelling, toerekening) en niet-geverifieerde punten: `references/bronnen.md`.
