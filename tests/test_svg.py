"""Tests for anychart v0.1, runnable with pytest or plain python.

The fixture uses real CRED POPULATION values for 2021 to 2025, from
Statistics Canada, Population Estimates via CRED. Dates recovered from
SVG geometry are allowed a small calendar tolerance because tick
spacing is linear in pixels, not in calendar days.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from anychart.model import to_record  # noqa: E402

EXPECTED_VALUES = [38058291, 38559788, 39477134, 40670178, 41435888]
EXPECTED_YEARS = ["2021", "2022", "2023", "2024", "2025"]


def test_population_svg():
    data = (Path(__file__).resolve().parents[1] / "examples" / "population.svg").read_bytes()
    record = to_record(data, extra={"series_id": "POPULATION", "geography": "Canada", "units": "Persons"})
    assert record["schema"] == "evidence.asset-metadata.v1"
    assert record["agent"]["title"] == "Population"
    assert record["quality"]["semanticInspection"]["status"] == "not_run"
    assert record["provenance"]["overlays"], "recession shading must be recorded, not dropped"
    assert len(record["data"]) == 5
    for row, expected_value, expected_year in zip(record["data"], EXPECTED_VALUES, EXPECTED_YEARS):
        assert row["date"].startswith(expected_year), row
        assert abs(row["value"] - expected_value) < 1000, row
        assert row["method"] == "svg_geometry"
        assert row["confidence"] == "high"


def test_raster_does_not_invent_values(tmp_path):
    png = bytes.fromhex("89504e470d0a1a0a") + b"\x00" * 40
    record = to_record(png)
    assert record["data"] == []
    assert record["status"] == "partial"
    assert record["quality"]["semanticInspection"]["status"] == "not_run"


if __name__ == "__main__":
    test_population_svg()
    print("population SVG test passed")
