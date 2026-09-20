"""Incident + AI routes: POST /ai/analyze, POST /ai/duplicate-check, insights, query."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from ..models.incident import Incident, STATUSES
from ..services import ai_service, duplicate_service

import os

router = APIRouter()

# Use DATA_DIR env var for persistent storage, otherwise fallback to local dir
data_dir = os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent))
STORE_PATH = Path(data_dir) / "incidents_store.json"

SEED_STORE: List[dict] = [
    {"incident_id": "INC-018", "description": "Water leakage near Block B computer room, dripping from ceiling",
     "location": "Block B", "issue": "Water leakage", "category": "Plumbing", "severity": "HIGH",
     "status": "Open", "created_at": "2026-09-01T09:00:00+00:00", "analysis": None, "duplicate_of": None},
    {"incident_id": "INC-022", "description": "Exposed electrical wire next to wall socket in Lab 304",
     "location": "Lab 304", "issue": "Exposed wire", "category": "Electrical", "severity": "CRITICAL",
     "status": "Open", "created_at": "2026-09-02T10:30:00+00:00", "analysis": None, "duplicate_of": None},
]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_store() -> List[dict]:
    if STORE_PATH.exists():
        try:
            data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return [dict(r) for r in SEED_STORE]


def _save_store() -> None:
    try:
        STORE_PATH.write_text(json.dumps(STORE, indent=2), encoding="utf-8")
    except OSError:
        pass  # in-memory still works; persistence is best-effort


def _find(incident_id: str) -> dict | None:
    for rec in STORE:
        if rec.get("incident_id") == incident_id:
            return rec
    return None


# in-memory store (JSON-file backed so reports survive restarts)
STORE: List[dict] = _load_store()
ai_service.seed_duplicates(STORE)


@router.post("/ai/analyze")
async def ai_analyze(
    description: str = Form(""),
    location: str = Form(""),
    building: str = Form(""),
    room: str = Form(""),
    location_type: str = Form(""),
    image: UploadFile | None = File(default=None),
):
    img_bytes = await image.read() if image is not None else None
    fname = image.filename if image is not None else ""
    return ai_service.analyze(description, location, img_bytes, fname,
                              building=building, room=room, location_type=location_type)


@router.post("/ai/duplicate-check")
async def ai_duplicate_check(payload: dict):
    return duplicate_service.check(payload.get("description", ""), payload.get("location", ""))


def _record_from_analysis(description: str, location: str, analysis: dict) -> dict:
    inc = Incident(description=description, location=location, ai=analysis)  # type: ignore
    if analysis.get("duplicate", {}).get("is_duplicate"):
        matches = analysis["duplicate"].get("matches") or []
        if matches:
            inc.duplicate_of = matches[0]["incident_id"]
    return {
        "incident_id": inc.id,
        "description": description,
        "location": location,
        "issue": analysis.get("summary", "") or description,
        "category": analysis.get("category"),
        "severity": analysis.get("severity"),
        "status": "Open",
        "created_at": inc.created_at.isoformat() if isinstance(inc.created_at, datetime) else str(inc.created_at),
        "analysis": analysis,
        "duplicate_of": inc.duplicate_of,
    }


@router.post("/incidents")
async def create_incident(
    description: str = Form(""),
    location: str = Form(""),
    image: UploadFile | None = File(default=None),
):
    """Analyze an uploaded incident AND save it (single call for the Report page)."""
    img_bytes = await image.read() if image is not None else None
    analysis = ai_service.analyze(description, location, img_bytes, image.filename if image else "")
    record = _record_from_analysis(description, location, analysis)
    STORE.append(record)
    ai_service.seed_duplicates([{"incident_id": record["incident_id"],
                                 "description": description, "location": location}])
    _save_store()
    return {"incident": record, "analysis": analysis}


@router.post("/incidents/save")
async def save_incident(payload: dict):
    """Save an already-computed analysis (e.g. from the AI Analysis page) without re-running vision."""
    description = payload.get("description", "")
    location = payload.get("location", "")
    analysis = payload.get("analysis") or {}
    record = _record_from_analysis(description, location, analysis)
    STORE.append(record)
    ai_service.seed_duplicates([{"incident_id": record["incident_id"],
                                 "description": description, "location": location}])
    _save_store()
    return {"incident": record}


@router.get("/incidents")
async def list_incidents():
    return {"count": len(STORE), "incidents": STORE}


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    rec = _find(incident_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Unknown incident {incident_id}")
    return {"incident": rec}


@router.patch("/incidents/{incident_id}/status")
async def update_incident_status(incident_id: str, payload: dict):
    """Admin control: transition status (Open -> Assigned -> In Progress -> Resolved -> Closed)."""
    rec = _find(incident_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Unknown incident {incident_id}")
    status = (payload.get("status") or "").strip()
    valid = {s.lower(): s for s in STATUSES}
    if status.lower() not in valid:
        raise HTTPException(status_code=400,
                            detail=f"Invalid status {status!r}. Use one of: {STATUSES}")
    rec["status"] = valid[status.lower()]
    rec["status_updated_at"] = _utcnow_iso()
    if payload.get("note"):
        rec.setdefault("status_notes", []).append(
            {"at": rec["status_updated_at"], "note": payload["note"]})
    _save_store()
    return {"incident": rec}


@router.post("/ai/query")
async def ai_query(payload: dict):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from ai.trends import query_incidents, summarize_trends
    q = payload.get("question", "")
    if payload.get("trends"):
        return {"insights": summarize_trends(STORE)}
    return query_incidents(STORE, q)


@router.get("/ai/insights")
async def ai_insights():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from ai.trends import summarize_trends
    return {"insights": summarize_trends(STORE)}
