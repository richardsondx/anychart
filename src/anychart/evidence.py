"""Optional, explicit hosted lane: match a record against Evidence.

This module is never imported by a local run. The CLI only calls it
when the user passes --verify, and it requires EVIDENCE_API_KEY.
No key, no network call, no silent fallback to a vision model.

Evidence search is a retrieval call, not generation: it returns ranked
published originals with their own provenance. The local record stays
the thing being matched; the hosted result never overwrites a value
read from the file.
"""

from __future__ import annotations

import json
import os
import urllib.request

BASE_URL = os.environ.get("EVIDENCE8_BASE_URL", "https://evidence8.com")


def verify(record: dict) -> dict:
    api_key = os.environ.get("EVIDENCE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "EVIDENCE_API_KEY is not set. Set it to verify against "
            "evidence8.com, or run locally without --verify."
        )
    query = record["agent"]["queryHints"]["searchText"] or record["agent"]["summary"]
    payload = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/v1/search",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())
