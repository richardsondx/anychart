"""Format detection from bytes, not from the file extension.

This mirrors the anydoc idea: a mislabelled file still converts correctly.
Only stdlib is used, and no network call is made here.
"""

import hashlib
import re

SIGNATURES = {
    b"\x89PNG": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF8": "gif",
    b"RIFF": "webp",  # refined below: RIFF....WEBP
    b"%PDF": "pdf",
}


def detect_format(data: bytes) -> str:
    """Return png, jpeg, gif, webp, pdf, svg, or unknown."""
    stripped = data.lstrip()
    if stripped.startswith(b"<svg") or b"<svg" in stripped[:4096]:
        return "svg"
    for sig, name in SIGNATURES.items():
        if data.startswith(sig):
            if name == "webp" and not data[8:12] == b"WEBP":
                continue
            return name
    return "unknown"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_dimensions(data: bytes):
    """Return (width, height) for a PNG, or None. IHDR is at a fixed offset."""
    if len(data) < 24 or not data.startswith(b"\x89PNG"):
        return None
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def parse_number(text: str):
    """Parse '41,798,407' or '40.5' to a float, or None."""
    cleaned = text.strip().replace(",", "").replace("%", "")
    if not re.fullmatch(r"-?\d+(\.\d+)?", cleaned):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None
