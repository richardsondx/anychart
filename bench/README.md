# Benchmark plan, not yet a benchmark

A benchmark that uses synthetic charts would prove nothing, because the
hard part is matching a real published original.

Planned corpus: 100 real published charts from SEC filings, Statistics
Canada via CRED, FRED, IMF, and similar publishers, with their published
values as ground truth.

Planned scoring, per chart:
- Title, axes, units, period, geography, and source correct
- Series values within tolerance, with SVG exactness scored separately from raster estimates
- Hallucinated values penalised heavily, more than missing values
- Overlays correctly separated from series
- Unknowns correctly reported, not filled with guesses

No corpus is shipped in v0.1, and no score is claimed yet.
