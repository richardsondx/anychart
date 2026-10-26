"""anychart CLI.

Examples:
    anychart chart.svg
    anychart chart.svg --json
    anychart chart.png --json
    anychart chart.svg --verify   # requires EVIDENCE_API_KEY, network only here
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .model import to_markdown, to_record

CRED_POPULATION = {
    "series_id": "POPULATION",
    "title": "Population",
    "publisher": "Statistics Canada, Population Estimates",
    "sourceUrl": "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1710000901",
    "sourcePageUrl": "https://cred.nshipyard.com/series/POPULATION",
    "source_table": "17-10-0009-01",
    "sourceKind": "government",
    "geography": "Canada",
    "units": "Persons",
    "frequency": "Quarterly",
    "vintage": "observations as of 2026-10-26",
    "rights_label": "Source: Statistics Canada, Population Estimates via CRED. Rights not stated in image.",
}


def build_parser():
    p = argparse.ArgumentParser(prog="anychart", description="Any chart in, one citable metadata record out.")
    p.add_argument("file", help="Chart file: SVG, PNG, JPG, WebP, GIF, or PDF page image")
    p.add_argument("--json", action="store_true", help="Print the full metadata record as JSON")
    p.add_argument("--cred-population", action="store_true",
                   help="Attach the known CRED POPULATION registry metadata (series id, table, source URL). Use only for that chart.")
    p.add_argument("--verify", action="store_true",
                   help="Match against evidence8.com. Requires EVIDENCE_API_KEY. This is the only flag that makes a network call.")
    p.add_argument("--vision", choices=["hosted"], default=None,
                   help="Explicit hosted vision lane. Not implemented in the local v0.1 build; it fails closed rather than silently using a model.")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = Path(args.file)
    if not path.exists():
        print(f"anychart: file not found: {path}", file=sys.stderr)
        return 2
    if args.vision == "hosted":
        print(
            "anychart: --vision hosted is not in the local build. "
            "Local runs never use a model. Record semanticInspection as not_run "
            "and use the vector version for exact geometry, or wait for the hosted lane.",
            file=sys.stderr,
        )
        return 2
    extra = CRED_POPULATION if args.cred_population else {}
    data = path.read_bytes()
    record = to_record(data, filename=path.name, extra=extra)
    if args.verify:
        from .evidence import verify

        try:
            record["evidence_match"] = verify(record)
        except Exception as exc:  # keep the local record, report the hosted failure
            print(f"anychart: verify failed: {exc}", file=sys.stderr)
            return 2
    if args.json:
        print(json.dumps(record, indent=2))
    else:
        print(to_markdown(data, filename=path.name, extra=extra))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
