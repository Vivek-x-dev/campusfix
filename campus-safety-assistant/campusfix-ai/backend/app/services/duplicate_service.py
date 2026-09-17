"""Duplicate service — cosine-similarity dedup (Checklist #4)."""
from __future__ import annotations
from .ai_service import duplicate_index


def check(description: str, location: str = "", top_k: int = 3) -> dict:
    is_dup, matches = duplicate_index.check(description, location, top_k=top_k)
    return {"is_duplicate": is_dup, "matches": matches,
            "threshold": duplicate_index.threshold}
