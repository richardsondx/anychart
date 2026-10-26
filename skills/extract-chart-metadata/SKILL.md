---
name: extract-chart-metadata
description: Turn a chart image into a citable metadata record before using it or citing it. Use when an agent is handed a chart, graph, figure, or table image and needs its title, period, units, geography, source, series id, and data, or needs to match it against Evidence.
---

# Extract chart metadata with anychart

## Rule

Structure first, vision last, and only on a shortlist.

1. Run anychart locally. It uses no model and no tokens by default.
2. Read the JSON record, not a prose description of the image.
3. If a field is null or the status is partial, say so. Do not fill it from a guess.
4. Only if the local record is insufficient, use an explicit hosted lane, and record that the model inspected it.
5. Never cite a value recovered from pixels as if it were a published value. Pixel estimates carry error bounds. SVG geometry is exact only where the vector file actually contains it.

## Commands

```bash
anychart chart.svg --json
anychart chart.svg --json --cred-population
anychart chart.svg --verify
```

`--verify` is the only flag that contacts evidence8.com, and it requires `EVIDENCE_API_KEY`. Without it, there is no network call.

## What to check before citing

- Title, publisher, source URL, and source page URL are present, or marked unknown
- Period, units, geography, and vintage match the question being answered
- Overlays, such as recession shading, are not mistaken for data series
- Rights are not assumed from the existence of an image URL
- `quality.semanticInspection.status` is `not_run` for a local run, and must stay that way in any report of a local run
