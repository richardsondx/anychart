"""Deterministic SVG chart extraction.

No model is involved. The parser reads what the file actually contains:
text elements for title, axes, ticks, source and footer, and geometry
for the plotted series. Pixel positions are mapped to data values only
through tick labels read from the same file. If a tick label is missing,
the corresponding value is not invented: it is left null and flagged.

Supported in v0.1:
- line charts as <polyline> or <path> with M/L commands
- bar charts as <rect> elements (overlay rects are excluded, see below)
- one series per file (multi-series is a documented v0.2 gap)

Overlays are not data. A rect whose class, id, or fill marks it as a
recession shade, gridline, or background is recorded under overlays
and never turned into a series point. This is the CRED case: grey
C.D. Howe recession shading must not become a second series.
"""

from __future__ import annotations

import re
from datetime import date
from xml.etree import ElementTree as ET

from .detect import parse_number

DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
NS_RE = re.compile(r"^\{[^}]*\}")


def _local(tag: str) -> str:
    return NS_RE.sub("", tag)


def _texts(root):
    out = []
    for el in root.iter():
        if _local(el.tag) != "text":
            continue
        text = "".join(el.itertext()).strip()
        if not text:
            continue
        out.append(
            {
                "text": text,
                "x": float(el.get("x", "0") or 0),
                "y": float(el.get("y", "0") or 0),
                "font_size": float(el.get("font-size", "12") or 12),
            }
        )
    return out


def _parse_date(text: str):
    m = DATE_RE.match(text.strip())
    if not m:
        return None
    year, month, day = int(m.group(1)), int(m.group(2) or 1), int(m.group(3) or 1)
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _linear_map(pairs):
    """Return a function mapping pixel -> value, from sorted (pixel, value).

    With fewer than two calibration points, no mapping exists and None
    is returned. That is a deliberate fail-closed rule.
    """
    pairs = sorted(pairs)
    if len(pairs) < 2:
        return None
    (x0, v0), (x1, v1) = pairs[0], pairs[-1]
    if x1 == x0:
        return None
    slope = (v1 - v0) / (x1 - x0)

    def f(x):
        return v0 + slope * (x - x0)

    return f


def _path_points(d: str):
    """Extract (x, y) points from a simple M/L path. Curves are not guessed."""
    tokens = re.findall(r"[ML]|-?\d+(?:\.\d+)?", d or "")
    points, mode, buf = [], None, []
    for tok in tokens:
        if tok in ("M", "L"):
            mode = tok
            buf = []
        else:
            buf.append(float(tok))
            if len(buf) == 2:
                points.append((buf[0], buf[1]))
                buf = []
    return points


def parse_svg(data: bytes) -> dict:
    root = ET.fromstring(data)
    texts = _texts(root)

    title = None
    if texts:
        # Largest text is usually the chart title. Ties fall to document order.
        title = max(texts, key=lambda t: t["font_size"])["text"]

    source_text = next(
        (t["text"] for t in texts if t["text"].lower().startswith("source:")), None
    )
    footer = next(
        (t["text"] for t in texts if "cred.nshipyard.com" in t["text"]), None
    )

    # Axis calibration, read from the file, never assumed.
    # Fix found by extensive CRED/FRED testing, Oct 26: the v0.1 rule that
    # only counted numeric labels with at least 4 characters silently
    # dropped almost every real axis label, such as 0, 2, 4, 6 for a policy
    # rate, 140 for CPI, or 200 for housing starts. Only large labels
    # like 38,000,000 passed. The fix groups numeric labels by position:
    # y ticks share an x (the left axis), x ticks share a y (the bottom
    # axis). A stray numeric label elsewhere does not become a tick.
    from collections import Counter

    date_candidates = []  # (x, y, ordinal)
    number_candidates = []  # (x, y, value)
    for t in texts:
        d = _parse_date(t["text"])
        if d is not None:
            date_candidates.append((t["x"], t["y"], d.toordinal()))
            continue
        value = parse_number(t["text"])
        if value is not None:
            number_candidates.append((t["x"], t["y"], value))

    def _pick_group(candidates, axis_index):
        if not candidates:
            return []
        counts = Counter(c[axis_index] for c in candidates)
        best_coord, _ = counts.most_common(1)[0]
        return [c for c in candidates if c[axis_index] == best_coord]

    x_group = _pick_group(date_candidates, 1)
    x_ticks = [(x, ordinal) for x, _y, ordinal in x_group]
    y_group = _pick_group(number_candidates, 0)
    y_ticks = [(y, value) for _x, y, value in y_group]

    x_map = _linear_map(x_ticks)
    y_map = _linear_map(y_ticks)

    overlays = []
    series_points = []

    for el in root.iter():
        tag = _local(el.tag)
        cls = (el.get("class") or "") + " " + (el.get("id") or "")
        if tag == "rect" and ("recession" in cls or "shading" in cls or "overlay" in cls):
            overlays.append({"type": "recession_shading", "class": cls.strip()})
            continue
        if tag == "polyline" and el.get("points"):
            pts = []
            for pair in el.get("points").strip().split():
                if "," in pair:
                    a, b = pair.split(",", 1)
                    pts.append((float(a), float(b)))
            series_points.extend(pts)
        elif tag == "path" and el.get("d"):
            series_points.extend(_path_points(el.get("d")))

    def _clean_value(v):
        # Keep decimals for rates and percents, integers for large counts.
        # Rounding to an integer, as v0.1 did, turned 0.25 into 0 and
        # 2.25 into 2, which is a silent data error, not a rounding choice.
        if abs(v - round(v)) < 0.001:
            return int(round(v))
        return round(v, 3)

    data_points = []
    if x_map is not None and y_map is not None:
        for px, py in series_points:
            data_points.append(
                {
                    "date": date.fromordinal(round(x_map(px))).isoformat(),
                    "value": _clean_value(y_map(py)),
                    "method": "svg_geometry",
                    "confidence": "high",
                }
            )
    elif series_points:
        # Geometry exists but calibration does not: record the gap, do not
        # fabricate values from pixel positions.
        data_points = []

    return {
        "title": title,
        "source_text": source_text,
        "footer": footer,
        "texts": [t["text"] for t in texts],
        "x_tick_count": len(x_ticks),
        "y_tick_count": len(y_ticks),
        "overlays": overlays,
        "data": data_points,
        "calibrated": x_map is not None and y_map is not None,
        "method": "svg_geometry" if data_points else "svg_text_only",
    }
