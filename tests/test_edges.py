"""Edge cases that must fail closed, not invent data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anychart.model import to_record  # noqa: E402
from anychart.svg import parse_svg  # noqa: E402


def test_path_not_polyline():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500">'
        '<text x="100" y="30" font-size="24">Test Path</text>'
        '<text x="20" y="380" font-size="12">0</text>'
        '<text x="20" y="60" font-size="12">10</text>'
        '<text x="100" y="430" font-size="12">2021-01-01</text>'
        '<text x="700" y="430" font-size="12">2025-01-01</text>'
        '<path d="M 100,380 L 700,60" fill="none" stroke="black"/>'
        "</svg>"
    ).encode()
    record = to_record(svg)
    assert len(record["data"]) == 2
    assert record["data"][0]["value"] == 0
    assert record["data"][1]["value"] == 10


def test_missing_calibration_recovers_nothing():
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500">'
        '<text x="100" y="30" font-size="24">No Ticks</text>'
        '<polyline points="100,100 700,200" fill="none" stroke="black"/>'
        "</svg>"
    ).encode()
    record = to_record(svg)
    assert record["data"] == []
    assert record["status"] == "partial"
    assert "calibration" in " ".join(record["quality"]["validation"]["warnings"])


def test_unknown_format_recovers_nothing():
    record = to_record(b"not a chart at all")
    assert record["data"] == []
    assert record["quality"]["semanticInspection"]["status"] == "not_run"


def test_parse_svg_overlay_not_series():
    parsed = parse_svg(
        (Path(__file__).resolve().parents[1] / "examples" / "population.svg").read_bytes()
    )
    assert parsed["overlays"]
    assert len(parsed["data"]) == 5
