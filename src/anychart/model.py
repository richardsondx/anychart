"""Build the output record.

The envelope follows Evidence's own standard, evidence.asset-metadata.v1,
in a local subset: identity, agent summary, provenance, delivery and
rights, quality, and audit. Fields that are not known are null with an
explicit status, never omitted silently and never invented.

Crucially, quality.semanticInspection.status is "not_run" in a local
run. No model inspected the image, so the record must not claim one did.
Only an explicit hosted vision lane may set it to "complete", with the
provider, model, and timestamp recorded alongside.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .detect import detect_format, png_dimensions, sha256_hex
from .svg import parse_svg


def _markdown(record: dict) -> str:
    agent = record["agent"]
    prov = record["provenance"]
    lines = [f"# {agent['summary']}", ""]
    lines.append(f"- Visual type: {record['identity']['visualType']}")
    lines.append(f"- Title: {agent.get('title') or 'unknown'}")
    lines.append(f"- Publisher: {prov.get('publisher') or 'unknown'}")
    lines.append(f"- Source: {prov.get('sourceUrl') or prov.get('source_text') or 'unknown'}")
    lines.append(f"- Geography: {agent['geography'].get('name') or 'unknown'}")
    lines.append(f"- Units: {agent.get('units') or 'unknown'}")
    lines.append(
        f"- Period: {agent['time'].get('start') or 'unknown'} to "
        f"{agent['time'].get('end') or 'unknown'}"
    )
    lines.append(f"- Status: {record['status']}")
    lines.append(f"- Extraction: {record['audit']['method']}")
    lines.append("")
    if record.get("data"):
        lines.append("| date | value | method | confidence |")
        lines.append("| --- | --- | --- | --- |")
        for row in record["data"]:
            lines.append(
                f"| {row['date']} | {row['value']:,} | {row['method']} | {row['confidence']} |"
            )
        lines.append("")
    if record["quality"]["validation"]["warnings"]:
        lines.append("Warnings:")
        for w in record["quality"]["validation"]["warnings"]:
            lines.append(f"- {w}")
    return "\n".join(lines) + "\n"


def to_record(data: bytes, filename: str = "chart", extra: dict | None = None) -> dict:
    """Convert chart bytes to an evidence.asset-metadata.v1 subset record.

    No network, no model, no tokens. `extra` is caller-supplied metadata
    only (for example a known series id from a registry); it is recorded
    under provenance, and it never overrides a value read from the file
    unless the file value is missing.
    """
    extra = extra or {}
    fmt = detect_format(data)
    warnings = []
    parsed = None
    method = "unparsed"

    if fmt == "svg":
        parsed = parse_svg(data)
        method = parsed["method"]
        if not parsed["calibrated"]:
            warnings.append(
                "SVG geometry found but axis calibration incomplete, "
                "so no values were recovered from pixels."
            )
    elif fmt in ("png", "jpeg", "gif", "webp"):
        warnings.append(
            "Raster image: local v0.1 does not recover values from pixels. "
            "Use --vision hosted explicitly for a vision read, or supply "
            "the vector (SVG) version for exact geometry."
        )
        method = "raster_unparsed"
    elif fmt == "pdf":
        warnings.append("PDF pages are not parsed in v0.1. Extract the chart first.")
        method = "pdf_unparsed"
    else:
        warnings.append("Unknown format: no values recovered.")
        method = "unknown_format"

    chart_data = parsed["data"] if parsed else []
    title = (parsed or {}).get("title") or extra.get("title")

    # Provenance: file facts first, caller facts second, unknowns explicit.
    publisher = extra.get("publisher")
    source_text = (parsed or {}).get("source_text")
    if source_text and "Statistics Canada" in source_text:
        publisher = "Statistics Canada, Population Estimates"

    start = chart_data[0]["date"] if chart_data else None
    end = chart_data[-1]["date"] if chart_data else None

    record = {
        "schema": "evidence.asset-metadata.v1",
        "status": "complete" if chart_data else "partial",
        "identity": {
            "assetId": f"anychart_{sha256_hex(data)[:16]}",
            "canonicalKey": sha256_hex(data),
            "assetClass": "visual_evidence",
            "visualType": "chart",
            "visualSubtype": "line" if chart_data else "unknown",
            "exposed": True,
        },
        "agent": {
            "title": title,
            "summary": title or "Chart with unknown title",
            "claim": {
                "text": title or "No title read from the chart.",
                "supportStatus": "not_evaluated",
                "confidence": None,
                "basis": "svg_text" if parsed else "none",
            },
            "entities": [],
            "metrics": [],
            "dimensions": [],
            "time": {
                "start": start,
                "end": end,
                "granularity": extra.get("frequency"),
                "status": "known" if start else "unknown",
            },
            "geography": {
                "name": extra.get("geography"),
                "type": "country" if extra.get("geography") else None,
                "status": "known" if extra.get("geography") else "unknown",
            },
            "direction": "increasing" if len(chart_data) >= 2 and chart_data[-1]["value"] > chart_data[0]["value"] else None,
            "units": extra.get("units"),
            "queryHints": {
                "searchText": " ".join(
                    x for x in [title, publisher, extra.get("series_id", "")] if x
                ),
                "keywords": [],
                "aliases": [extra["series_id"]] if extra.get("series_id") else [],
            },
        },
        "provenance": {
            "publisher": publisher,
            "document": extra.get("document"),
            "documentId": extra.get("series_id"),
            "sourceKind": extra.get("sourceKind", "other"),
            "sourceUrl": extra.get("sourceUrl"),
            "sourcePageUrl": extra.get("sourcePageUrl"),
            "sourceAssetUrl": None,
            "source_text": source_text,
            "footer_in_image": (parsed or {}).get("footer"),
            "series_id": extra.get("series_id"),
            "source_table": extra.get("source_table"),
            "vintage": extra.get("vintage"),
            "overlays": (parsed or {}).get("overlays", []),
        },
        "delivery": {
            "rights": {
                "label": extra.get("rights_label"),
                "deliveryMode": "unknown",
                "citationRequired": True if source_text or extra.get("sourceUrl") else None,
                "commercialUse": "not_evaluated",
            },
            "availability": "available" if chart_data else "unknown",
        },
        "quality": {
            "validation": {"status": "pass" if chart_data else "needs_review", "issues": [], "warnings": warnings},
            "semanticInspection": {
                "status": "not_run",
                "provider": None,
                "model": None,
                "inspectedAt": None,
            },
        },
        "audit": {
            "generatedBy": "anychart.v0.1",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "format": fmt,
            "dimensions": png_dimensions(data) if fmt == "png" else None,
            "sourceFingerprint": sha256_hex(data),
        },
        "data": chart_data,
    }
    return record


def to_markdown(data: bytes, filename: str = "chart", extra: dict | None = None) -> str:
    return _markdown(to_record(data, filename, extra))


def to_json(data: bytes, filename: str = "chart", extra: dict | None = None) -> str:
    return json.dumps(to_record(data, filename, extra), indent=2)
