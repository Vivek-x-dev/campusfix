"""Admin routes — human-in-the-loop overrides (Checklist #10)."""
from __future__ import annotations
from fastapi import APIRouter

router = APIRouter()
OVERRIDES: list = []


@router.post("/admin/override")
async def override(payload: dict):
    """Allow admin to correct AI: {incident_id, category, severity, note}."""
    OVERRIDES.append(payload)
    return {"ok": True, "stored": payload, "message": "Correction stored for future model improvement."}


@router.get("/admin/overrides")
async def list_overrides():
    return {"count": len(OVERRIDES), "overrides": OVERRIDES}
