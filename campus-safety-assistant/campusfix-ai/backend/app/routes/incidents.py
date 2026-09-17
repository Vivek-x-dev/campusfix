"""Incident + AI routes: POST /ai/analyze, POST /ai/duplicate-check, insights, query."""
from __future__ import annotations
from typing import List
from fastapi import APIRouter, UploadFile, File, Form

from ..models.incident import Incident
from ..services import ai_service, duplicate_service

router = APIRouter()

# in-memory store (Mongo optional); seeded with a couple of history items for dedup demo
STORE: List[dict] = [
    {"incident_id": "INC-018", "description": "Water leakage near Block B computer room, dripping from ceiling",
     "location": "Block B", "issue": "Water leakage", "category": "Plumbing", "severity": "HIGH"},
    {"incident_id": "INC-022", "description": "Exposed electrical wire next to wall socket in Lab 304",
     "location": "Lab 304", "issue": "Exposed wire", "category": "Electrical", "severity": "CRITICAL"},
]
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


@router.post("/incidents")
async def create_incident(
    description: str = Form(""),
    location: str = Form(""),
    image: UploadFile | None = File(default=None),
):
    img_bytes = await image.read() if image is not None else None
    analysis = ai_service.analyze(description, location, img_bytes, image.filename if image else "")
    inc = Incident(description=description, location=location, ai=analysis)  # type: ignore
    if analysis.get("duplicate", {}).get("is_duplicate"):
        inc.duplicate_of = analysis["duplicate"]["matches"][0]["incident_id"]
    STORE.append({"incident_id": inc.id, "description": description, "location": location,
                  "issue": analysis.get("summary", ""), "category": analysis.get("category"),
                  "severity": analysis.get("severity")})
    ai_service.seed_duplicates([{"incident_id": inc.id, "description": description, "location": location}])
    return {"incident": inc.model_dump(), "analysis": analysis}


@router.get("/incidents")
async def list_incidents():
    return {"count": len(STORE), "incidents": STORE}


@router.post("/ai/query")
async def ai_query(payload: dict):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from ai.trends import query_incidents, summarize_trends
    q = payload.get("question", "")
    if payload.get("trends"):
        return {"insights": summarize_trends(STORE)}
    return query_incidents(STORE, q)


@router.get("/ai/insights")
async def ai_insights():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from ai.trends import summarize_trends
    return {"insights": summarize_trends(STORE)}
