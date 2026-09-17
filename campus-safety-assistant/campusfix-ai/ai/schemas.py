"""Pydantic schemas — the single source of truth for structured AI output.

Every LLM / heuristic output is validated through these models so the
backend always receives predictable JSON (Checklist #3).
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

CATEGORIES = [
    "Electrical",
    "Plumbing",
    "Waste",
    "Infrastructure",
    "Furniture",
    "RoadPavement",
    "Other",
    "OtherUnknown",  # low-confidence fallback, never forced
]

SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

DEPARTMENTS = [
    "Electrical Maintenance",
    "Plumbing",
    "Sanitation",
    "Facilities",
    "Civil Works",
    "General Administration",
]

DAMAGE_LEVELS = ["Minor", "Moderate", "Severe", "Unknown"]

# Tunable thresholds (Checklist #5, #10)
CONFIDENCE_THRESHOLD = 0.55      # below -> human review
DUPLICATE_THRESHOLD = 0.40       # cosine similarity above -> duplicate (tuned: true dupes >=0.48, hard negatives <=0.29)


class LocationContext(BaseModel):
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    location_type: Optional[str] = None  # e.g. lab, hostel, garden, corridor
    raw: Optional[str] = None


class AIAnalysisResult(BaseModel):
    """Target schema from `things to do.txt` #3 (+ extensions for #2,#7-#14,#17)."""

    model_config = {"protected_namespaces": ()}

    category: str = Field(..., description="One of CATEGORIES")
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: str = Field(..., description="LOW|MEDIUM|HIGH|CRITICAL")
    risk: str = Field(..., description="Possible risk in plain English")
    action: str = Field(..., description="Recommended immediate action")
    department: str = Field(...)
    summary: str = Field(..., description="Concise incident summary, no invented facts")
    explanation: List[str] = Field(default_factory=list, description="Why bullets")
    damage: str = Field(default="Unknown")
    caption: Optional[str] = None
    ocr_text: Optional[str] = None
    needs_human_review: bool = False
    model_version: str = "campusfix-ai-v1"
    inference_time_ms: Optional[float] = None

    @field_validator("category")
    @classmethod
    def _check_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}, got {v!r}")
        return v

    @field_validator("severity")
    @classmethod
    def _check_severity(cls, v: str) -> str:
        v = v.upper()
        if v not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}")
        return v

    @classmethod
    def fallback(cls, reason: str = "LLM failure") -> "AIAnalysisResult":
        """Safe fallback — never invents details (Checklist #5)."""
        return cls(
            category="OtherUnknown",
            confidence=0.0,
            severity="MEDIUM",
            risk="Unverified issue — manual inspection required.",
            action="Dispatch staff to inspect the location.",
            department="General Administration",
            summary=f"Report could not be auto-verified ({reason}). Human review required.",
            explanation=["AI output was unavailable or malformed.", "Routed to human review."],
            damage="Unknown",
            needs_human_review=True,
        )


class AnalyzeRequest(BaseModel):
    description: str = ""
    location: str = ""
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    location_type: Optional[str] = None


class DuplicateMatch(BaseModel):
    incident_id: str
    similarity: float  # 0..1
    location: Optional[str] = None
    issue: Optional[str] = None


class DuplicateCheckResult(BaseModel):
    is_duplicate: bool
    matches: List[DuplicateMatch] = Field(default_factory=list)
    threshold: float = DUPLICATE_THRESHOLD


class TrendInsight(BaseModel):
    headline: str
    detail: str


class IncidentRecord(BaseModel):
    incident_id: str
    category: str = "Other"
    severity: str = "MEDIUM"
    description: str = ""
    location: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
