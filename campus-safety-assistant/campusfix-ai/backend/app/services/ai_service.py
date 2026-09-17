"""Thin service wrapper so routes never import AI internals directly."""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional

# make `ai/` importable when running backend from backend/ or repo root
for cand in [Path(__file__).resolve().parents[3] / "ai",
             Path(__file__).resolve().parents[4] / "ai"]:
    if (cand / "inference.py").exists() and str(cand.parent) not in sys.path:
        sys.path.insert(0, str(cand.parent))

from ai.inference import analyze_incident, duplicate_index  # noqa: E402


def analyze(description: str = "", location: str = "", image_bytes: Optional[bytes] = None,
            filename: str = "", **ctx) -> dict:
    return analyze_incident(description=description, location=location,
                            image_bytes=image_bytes, filename=filename, **ctx)


def seed_duplicates(records: list) -> None:
    duplicate_index.seed(records)
