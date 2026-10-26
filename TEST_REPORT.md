# Test report, Oct 26 2026

## Go criteria, set before running

- Title correct for every chart
- Every recovered value within 1 percent of the true value, or within
  0.05 for rates and percents under 10, whichever is larger
- Recovered date within 7 days of the true date
- Recession shading never counted as a series point
- semanticInspection stays not_run, no field invented

## Result: PASS for SVG, scoped

All tests pass:

```
7 passed, 0 failed
tests/test_cred_fred.py: 7 charts, 35 points
tests/test_svg.py: population fixture, raster fail-closed
tests/test_edges.py: path, missing calibration, unknown format, overlay
```

Per-chart max relative error, from `tests/test_cred_fred.py`:

- CRED POPULATION: 0.000130 percent
- CRED POLICY_RATE: 0.000000 percent
- CRED UNRATE_CA: 0.000000 percent
- CRED HOUSING_STARTS: 0.000486 percent
- CRED CPI_ALLITEMS_SA: 0.000000 percent
- FRED UNRATE: 0.000000 percent
- FRED GDP: 0.000119 percent

Scales covered: 0.25 percent to 41,798,407 persons, plus index,
thousands of units, and billions of dollars. Units covered: Persons,
Percent, Index 2002=100, Thousands of units, Billions of Dollars.

## Truth sources, checked Oct 26 2026

CRED, live API:
- POPULATION, POLICY_RATE, UNRATE_CA, HOUSING_STARTS, CPI_ALLITEMS_SA
- Jan 2021 to Jan 2025 observations, plus series metadata from
  /api/series (source, table, units, frequency)

FRED, live pages:
- UNRATE: /data/UNRATE.txt, Jan 2021 6.4, Jan 2022 4.0, Jan 2023 3.5,
  Jan 2024 3.7, Jan 2025 4.0, Percent, Monthly, Seasonally Adjusted,
  source U.S. Bureau of Labor Statistics
- GDP: series page observations, Q2 2025 30,630.174 to Q2 2026
  32,563.030, Billions of Dollars, Quarterly, Seasonally Adjusted
  Annual Rate, source U.S. Bureau of Economic Analysis
- CPIAUCSL, FEDFUNDS, HOUST: metadata only, from their series pages.
  Their values are NOT in the recovery test.

## Two bugs found by this test, and fixed

1. Y tick filter: v0.1 only counted numeric labels with at least 4
   characters. That dropped 0, 2, 4, 6, 140, 200, and almost every real
   axis label except large population labels. Fixed by grouping
   numeric labels by axis position.
2. Integer rounding: v0.1 rounded every recovered value to an integer.
   That turned 0.25 into 0 and 2.25 into 2. Fixed by keeping decimals
   for small values and integers only where the value is integral.

Without this test, both bugs would have shipped in a public repo.

## What this test does NOT prove

- It does not prove anychart parses FRED's actual Highcharts DOM or
  CRED's actual React-rendered SVG out of the box. Fixtures use the
  same SVG structure a publisher chart uses, title, tick texts,
  polyline or path, source line, recession rect, but publisher DOMs
  vary in transforms, curves, and label placement. That is the next
  validation, and it is listed as a gap, not hidden.
- It does not prove raster charts work. Raster tests pass only in the
  fail-closed sense: no values invented. A raster chart is not useful
  output in v0.1, only a clear partial record.
- It does not prove multi-series, bar, pie, map, or table charts work.
  Those are not in v0.1.
- FRED csv endpoint returned 403 to a text fetch, and the .txt pages
  for CPIAUCSL and FEDFUNDS returned notes only, not tables. That is
  why those two series are metadata only here. Claiming exact values
  for them without a verified source would have been invention.

## Verdict

Useful, if scoped honestly: an SVG chart to Evidence metadata record,
local, no AI, no tokens, with explicit unknowns. Not useful, and not
claimed, as a universal raster chart reader. That is why v0.1 ships
with this report, not with a broader claim.
