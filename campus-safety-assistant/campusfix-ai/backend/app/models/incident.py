"""Incident schemas shared by backend + AI (Checklist #3: consistent schema)."""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

CATEGORIES = ["Electrical", "Plumbing", "Waste", "Infrastructure", "Furniture", "RoadPavement", "Other", "OtherUnknown"]
SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
STATUSES = ["Open", "Assigned", "In Progress", "Resolved", "Closed"]


class IncidentCreate(BaseModel):
    description: str = ""
    location: str = ""
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    location_type: Optional[str] = None


class AIResult(BaseModel):
    category: str = "OtherUnknown"
    confidence: float = 0.0
    severity: str = "MEDIUM"
    risk: str = ""
    action: str = ""
    department: str = "General Administration"
    summary: str = ""
    explanation: List[str] = Field(default_factory=list)
    damage: str = "Unknown"
    caption: Optional[str] = None
    ocr_text: Optional[str] = None
    needs_human_review: bool = True


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:8])
    description: str = ""
    location: str = ""
    status: str = "Open"
    ai: Optional[AIResult] = None
    duplicate_of: Optional[str] = None
    human_override: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
