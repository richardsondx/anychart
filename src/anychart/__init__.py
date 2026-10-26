"""anychart: any chart in, one citable metadata record out.

Local by default. No AI model, no API call, no tokens, unless the user
explicitly opts into a hosted lane with --verify or --vision hosted.
"""

__version__ = "0.1.0"

from .model import to_markdown, to_record

__all__ = ["__version__", "to_record", "to_markdown"]
