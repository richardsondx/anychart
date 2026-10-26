# anychart

Any chart in, one citable metadata record out.

Built for [Evidence](https://evidence8.com), the visual evidence index for financial research agents. Evidence retrieves published charts, tables, maps, and figures with their source attached. anychart is the local companion: it turns a chart you already have into the same kind of record, so an agent can use it, compare it, or match it against Evidence, without first sending the image to a vision model.

## The problem

A chart image on its own is opaque to an agent. It has to open the image, read it with a vision model, and guess the title, period, units, geography, and source. That costs tokens on every chart, and the guesses are not attached to provenance.

Evidence's answer, at the index level, is metadata first: per-visual structured fields, provenance, period, units, geography, vintage, series identifiers, extraction geometry, and per-visual rights. Claim checking is downstream of that metadata, not a replacement for it.

anychart brings that same metadata layer to a single file, locally.

## What it does, and what it does not do

Local, by default, with no AI and no tokens:

- Detects the format from bytes, not the file extension
- Reads SVG text for title, axis labels, ticks, source line, and footer
- Maps SVG geometry to data values through tick labels read from the same file
- Records overlays separately. Grey recession shading is an overlay, not a second series
- Outputs the Evidence metadata envelope, `evidence.asset-metadata.v1`, in a local subset
- Leaves unknown fields null with an explicit status, instead of inventing them
- Records `quality.semanticInspection.status: "not_run"` on every local run, because no model inspected the image

It does not, in v0.1:

- Recover exact values from a raster PNG or JPG. A raster image does not contain the data, only pixels. The local run says so, marks the record partial, and does not fabricate values.
- Use a vision model silently. `--vision hosted` fails closed in the local build. A hosted vision lane, when it exists, must record provider, model, and timestamp in the record.
- Claim redistribution rights. Rights are recorded as stated in the image, or as `not_evaluated`. A URL in an image is not a licence.

## Quick start

```bash
pip install -e .
anychart examples/population.svg
anychart examples/population.svg --json
```

The first command prints Markdown. The second prints the full JSON record.

To attach known registry metadata for the CRED example only:

```bash
anychart examples/population.svg --json --cred-population
```

To match against Evidence, and only then make a network call:

```bash
export EVIDENCE_API_KEY="..."
anychart chart.svg --verify
```

Without `--verify`, anychart makes no network call at all.

## Example: a real CRED chart

Input: the CRED Population chart, Statistics Canada, Population Estimates via CRED.

CRED series id `POPULATION`, StatCan table `17-10-0009-01`, geography Canada, units Persons, frequency Quarterly. The live CRED page lists Q3 2026 as 41,798,407 persons.

Output, trimmed:

```json
{
  "schema": "evidence.asset-metadata.v1",
  "status": "complete",
  "agent": {
    "title": "Population",
    "time": {"start": "2021-01-01", "end": "2025-01-01", "granularity": "Quarterly"},
    "geography": {"name": "Canada", "status": "known"},
    "units": "Persons",
    "direction": "increasing"
  },
  "provenance": {
    "publisher": "Statistics Canada, Population Estimates",
    "sourceUrl": "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000901",
    "sourcePageUrl": "https://cred.nshipyard.com/series/POPULATION",
    "series_id": "POPULATION",
    "source_table": "17-10-0009-01",
    "overlays": [{"type": "recession_shading"}]
  },
  "quality": {
    "semanticInspection": {"status": "not_run", "provider": null, "model": null}
  },
  "data": [
    {"date": "2021-01-01", "value": 38058250, "method": "svg_geometry", "confidence": "high"},
    {"date": "2025-01-01", "value": 41435875, "method": "svg_geometry", "confidence": "high"}
  ]
}
```

The full fixture, its generated record, and its test live in `examples/population.svg`, `examples/population.json`, and `tests/test_svg.py`. The fixture values are real CRED observations for 2021 to 2025, and the recovered values above are within 50 persons of them, which is the rounding error from two-decimal SVG coordinates, not a model guess. Two middle dates recover as Jan 2 rather than Jan 1, because tick spacing is linear in pixels, not in calendar days. The test allows that calendar tolerance and checks years and values, not exact day strings.

## Agent skill

```bash
npx skills add richardsondx/anychart
```

See `skills/extract-chart-metadata/SKILL.md`. The rule for agents is simple: structure first, vision last, and only on a shortlist. Never paste a chart into a model and cite the model's guess as if it were the source.

## How this differs from nearby tools

This is not a claim that no chart tool exists. Nearby tools solve different jobs:

- WebPlotDigitizer: manual digitizing, with a human calibrating axes and tracing curves
- Reducto chart extraction: hosted, vision-model based extraction as a paid API
- ChartOCR and similar research code: chart understanding research, not a metadata record with provenance, vintage, series ids, and rights
- Generic image-to-markdown converters: they describe an image, they do not return an Evidence-shaped record an agent can filter, match, and cite

No open tool we found combines all of these: local deterministic extraction, no AI by default, an Evidence-compatible metadata envelope, explicit unknowns, overlay separation, and an optional hosted match against a published-original index. That combination is the point of anychart. If you know one, open an issue and we will correct this claim.

## Tested, with limits

See `TEST_REPORT.md` for the full report. In short: 7 charts, 35 points,
from CRED and FRED, all pass, with max relative error under 0.0005
percent, across scales from 0.25 percent to 41 million persons. That
test also found and fixed two bugs that would otherwise have shipped.

What it does not prove: parsing FRED's actual Highcharts DOM or CRED's
actual React SVG out of the box, raster charts, multi-series, bar, pie,
map, or table charts. Those are gaps, not claims.

Rust: not in v0.1. See `RUST_PLAN.md` for why Python first, and what
a Rust v1 would need to prove before it replaces the Python core.

## Roadmap

- v0.1: SVG line charts, raster fail-closed, Evidence metadata subset, CLI, agent skill
- v0.2: SVG bar charts, multi-series, PDF chart extraction, table-as-image OCR (local, opt-in)
- Later: hosted vision lane with full model provenance, Evidence `--verify` matching by geometry and series id, benchmark on 100 real published charts (see `bench/`)

## Licence

MIT. See `LICENSE`.
