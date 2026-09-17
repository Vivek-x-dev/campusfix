"""CampusFix AI pipeline — implements the IDEAL AI PIPELINE from the brief:

    IMAGE -> Computer Vision (category+confidence) -> Context+LLM Reasoning
    (severity+risk+action) -> Embedding -> Duplicate Detection
    -> Confidence Check -> Auto ticket / Human review
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

from .embeddings import DuplicateIndex
from .reasoning import reason
from .schemas import (
    AIAnalysisResult,
    CONFIDENCE_THRESHOLD,
    DUPLICATE_THRESHOLD,
)
from .vision import classify_image

# Shared in-memory duplicate index (backend injects history at startup)
duplicate_index = DuplicateIndex(threshold=DUPLICATE_THRESHOLD)


def analyze_incident(
    description: str = "",
    location: str = "",
    image_bytes: Optional[bytes] = None,
    filename: str = "",
    building: str = "",
    floor: str = "",
    room: str = "",
    location_type: str = "",
    check_duplicates: bool = True,
) -> Dict:
    """Run the full pipeline. Always returns JSON-serializable validated output."""
    t0 = time.perf_counter()
    loc_full = " ".join(p for p in [location, building, floor, room, location_type] if p).strip()

    try:
        category, confidence, caption, ocr_text = classify_image(
            image_bytes=image_bytes, description=description,
            location=loc_full, filename=filename,
        )
    except Exception:
        category, confidence, caption, ocr_text = "OtherUnknown", 0.0, "Vision step failed.", None

    fields = reason(category, confidence, description, loc_full, caption, ocr_text or "")

    needs_review = bool(confidence < CONFIDENCE_THRESHOLD or category == "OtherUnknown")

    # Duplicate detection (#4)
    dup_info: Dict = {"is_duplicate": False, "matches": []}
    if check_duplicates:
        try:
            is_dup, matches = duplicate_index.check(description or caption, loc_full)
            dup_info = {"is_duplicate": is_dup, "matches": matches}
        except Exception:
            pass

    elapsed_ms = (time.perf_counter() - t0) * 1000
    try:
        result = AIAnalysisResult(
            category=category, confidence=round(float(confidence), 3),
            severity=fields["severity"], risk=fields["risk"], action=fields["action"],
            department=fields["department"], summary=fields["summary"],
            explanation=fields["explanation"], damage=fields.get("damage", "Unknown"),
            caption=caption, ocr_text=ocr_text, needs_human_review=needs_review,
            inference_time_ms=round(elapsed_ms, 1),
        )
    except Exception:
        result = AIAnalysisResult.fallback("validation failed")
        result.inference_time_ms = round(elapsed_ms, 1)

    out = result.model_dump()
    out["duplicate"] = dup_info
    out["decision"] = "human_review" if needs_review else "auto_ticket"
    return out


def batch_evaluate(cases: List[Dict]) -> Dict:
    """Metrics harness for judges (#METRICS): accuracy + latency on a test set."""
    correct_cat = correct_sev = 0
    lat: List[float] = []
    low_conf = 0
    for c in cases:
        t0 = time.perf_counter()
        out = analyze_incident(
            description=c.get("description", ""), location=c.get("location", ""),
            filename=c.get("filename", ""), check_duplicates=False,
        )
        lat.append((time.perf_counter() - t0) * 1000)
        if out["category"] == c.get("expected_category"):
            correct_cat += 1
        if out["severity"] == c.get("expected_severity"):
            correct_sev += 1
        if out["needs_human_review"]:
            low_conf += 1
    n = max(1, len(cases))
    return {
        "n": len(cases),
        "category_accuracy": round(correct_cat / n, 3),
        "severity_accuracy": round(correct_sev / n, 3),
        "avg_inference_ms": round(sum(lat) / n, 1),
        "human_review_rate": round(low_conf / n, 3),
    }
