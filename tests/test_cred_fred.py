"""Extensive SVG test, Oct 26 2026.

Go criteria, set before running:
- Title correct for every chart
- Every recovered value within 1 percent of the true value, or within
  0.05 for rates and percents under 10, whichever is larger
- Recovered date within 7 days of the true date for every point
  (tick spacing is linear in pixels, not calendar days, so a point
  near a year boundary can recover as Dec 31 instead of Jan 1)
- Recession shading never counted as a series point
- semanticInspection stays not_run, no field invented

Truth sources:
- CRED: live CRED API observations fetched Oct 26 2026, Jan values
  2021 to 2025, plus series metadata from /api/series
- FRED UNRATE: live FRED /data/UNRATE.txt, Jan values 2021 to 2025
- FRED GDP: live FRED series page observations, Q2 2025 to Q2 2026
- FRED CPIAUCSL, FEDFUNDS, HOUST: metadata only in this file, from
  their FRED series pages (source, units, frequency). Their values are
  NOT claimed as exact FRED observations here, so they are not in the
  recovery test. The FRED csv endpoint returned 403 to a text fetch,
  and the .txt pages for those series returned notes only, so claiming
  exact values for them would be invention. See TEST_REPORT.md.

Fixtures are rendered in the same SVG structure a publisher chart
uses: title text, axis tick texts, a polyline, a source line, and for
CRED a recession rect. The test measures parser fidelity: input
geometry to output record, against the true values used to draw it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anychart.model import to_record  # noqa: E402


def fmt_number(v):
    if abs(v - round(v)) < 0.001:
        return f"{int(round(v)):,}"
    return str(v)


def make_svg(title, dates, values, y_ticks, source, footer=None, recession=True):
    # Plot area: x 100 to 700, y 60 (top, y_tick max) to 380 (bottom, min)
    y_min, y_max = min(y_ticks), max(y_ticks)
    xs = [100 + i * 150 for i in range(len(dates))]
    points = []
    for x, v in zip(xs, values):
        y = 380 - (v - y_min) / (y_max - y_min) * 320
        points.append(f"{x},{y:.2f}")
    y_tick_texts = []
    for tick in y_ticks:
        y = 380 - (tick - y_min) / (y_max - y_min) * 320
        y_tick_texts.append(f'<text x="20" y="{y:.2f}" font-size="12">{fmt_number(tick)}</text>')
    x_tick_texts = [
        f'<text x="{x}" y="430" font-size="12">{d}</text>' for x, d in zip(xs, dates)
    ]
    recession_rect = (
        '<rect class="recession" x="300" y="50" width="100" height="350" fill="#cccccc" opacity="0.2"/>'
        if recession
        else ""
    )
    footer_text = f'<text x="650" y="490" font-size="12">{footer}</text>' if footer else ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">'
        f'<text x="100" y="30" font-size="24">{title}</text>'
        f'<text x="100" y="470" font-size="12">Source: {source}</text>'
        f"{footer_text}"
        + "".join(y_tick_texts)
        + "".join(x_tick_texts)
        + recession_rect
        + f'<polyline points="{" ".join(points)}" fill="none" stroke="#0F1B2B" stroke-width="3"/>'
        + "</svg>"
    ).encode()


CASES = [
    # CRED, live API, Jan 2021-2025
    {
        "name": "CRED POPULATION",
        "title": "Population",
        "dates": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
        "values": [38058291, 38559788, 39477134, 40670178, 41435888],
        "y_ticks": [38000000, 40000000, 42000000],
        "source": "Statistics Canada, Population Estimates via CRED",
        "footer": "cred.nshipyard.com",
    },
    {
        "name": "CRED POLICY_RATE",
        "title": "Bank of Canada Policy Interest Rate",
        "dates": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
        "values": [0.25, 0.25, 4.5, 5.0, 3.0],
        "y_ticks": [0, 2, 4, 6],
        "source": "Bank of Canada, Valet via CRED",
        "footer": "cred.nshipyard.com",
    },
    {
        "name": "CRED UNRATE_CA",
        "title": "Unemployment Rate",
        "dates": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
        "values": [9.2, 6.4, 5.1, 5.7, 6.7],
        "y_ticks": [0, 5, 10],
        "source": "Statistics Canada, Labour Force Survey via CRED",
        "footer": "cred.nshipyard.com",
    },
    {
        "name": "CRED HOUSING_STARTS",
        "title": "Housing Starts",
        "dates": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
        "values": [291.29, 229.125, 205.585, 228.574, 233.83],
        "y_ticks": [200, 250, 300],
        "source": "Canada Mortgage and Housing Corporation via Statistics Canada via CRED",
        "footer": "cred.nshipyard.com",
    },
    {
        "name": "CRED CPI_ALLITEMS_SA",
        "title": "Consumer Price Index, All-items (Seasonally Adjusted)",
        "dates": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
        "values": [139.1, 146.3, 154.9, 159.4, 162.5],
        "y_ticks": [120, 160, 200],
        "source": "Statistics Canada, Consumer Price Index via CRED",
        "footer": "cred.nshipyard.com",
    },
    # FRED, live .txt / series page
    {
        "name": "FRED UNRATE",
        "title": "Unemployment Rate",
        "dates": ["2021-01-01", "2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"],
        "values": [6.4, 4.0, 3.5, 3.7, 4.0],
        "y_ticks": [0, 5, 10],
        "source": "U.S. Bureau of Labor Statistics via FRED",
        "footer": None,
        "recession": False,
    },
    {
        "name": "FRED GDP",
        "title": "Gross Domestic Product",
        "dates": ["2025-04-01", "2025-07-01", "2025-10-01", "2026-01-01", "2026-04-01"],
        "values": [30630.174, 31180.493, 31462.523, 31906.274, 32563.03],
        "y_ticks": [30000, 31500, 33000],
        "source": "U.S. Bureau of Economic Analysis via FRED",
        "footer": None,
        "recession": False,
    },
]


def check_case(case):
    svg = make_svg(
        case["title"],
        case["dates"],
        case["values"],
        case["y_ticks"],
        case["source"],
        footer=case.get("footer"),
        recession=case.get("recession", True),
    )
    record = to_record(svg, extra={"series_id": case["name"], "geography": "Canada" if case["name"].startswith("CRED") else "United States"})
    assert record["agent"]["title"] == case["title"], (case["name"], record["agent"]["title"])
    assert record["provenance"]["source_text"] == f"Source: {case['source']}", case["name"]
    assert record["quality"]["semanticInspection"]["status"] == "not_run"
    assert len(record["data"]) == len(case["values"]), (case["name"], record["data"])
    if case.get("recession", True):
        assert record["provenance"]["overlays"], case["name"]
    from datetime import date as _date

    max_rel_error = 0.0
    for row, true_value, true_date in zip(record["data"], case["values"], case["dates"]):
        recovered = _date.fromisoformat(row["date"])
        expected = _date.fromisoformat(true_date)
        assert abs((recovered - expected).days) <= 7, (case["name"], row, true_date)
        tol = max(abs(true_value) * 0.01, 0.05 if abs(true_value) < 10 else 0.0)
        err = abs(row["value"] - true_value)
        assert err <= tol, (case["name"], row, true_value, tol)
        if true_value:
            max_rel_error = max(max_rel_error, err / abs(true_value))
    return max_rel_error


def test_all():
    for case in CASES:
        check_case(case)


if __name__ == "__main__":
    for case in CASES:
        err = check_case(case)
        print(f"{case['name']}: PASS, max relative error {err:.6%}")
    print(f"TOTAL: {len(CASES)} charts, {sum(len(c['values']) for c in CASES)} points, all PASS")
