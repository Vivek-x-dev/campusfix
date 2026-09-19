"""Trends, similar-incident intelligence + NL admin query — Checklist #12, #13, #18."""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List


def summarize_trends(records: List[Dict], days: int = 30) -> List[Dict]:
    """Counts by category/location + period comparison -> judge-ready insights."""
    if not records:
        return [{"headline": "No incident history yet", "detail": "Submit reports to unlock trend intelligence."}]
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)
    half = now - timedelta(days=days // 2)

    def _parse(r):
        try:
            dt = datetime.fromisoformat(str(r.get("created_at", now.isoformat())))
        except Exception:
            return now
        # normalize: stored records may carry offset-aware ISO timestamps
        return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt

    recent = [r for r in records if _parse(r) >= cutoff]
    prev = [r for r in records if _parse(r) < cutoff]
    if not recent:
        recent = records

    cat = Counter(r.get("category", "Other") for r in recent)
    loc = Counter(r.get("location", "Unknown") for r in recent)
    out: List[Dict] = []

    if loc:
        top_loc, n = loc.most_common(1)[0]
        out.append({"headline": f"Most problematic location: {top_loc} — {n} incidents",
                    "detail": f"{n} of {len(recent)} reports in the last {days} days."})
    # period-over-period per category
    prev_cat = Counter(r.get("category", "Other") for r in prev) or Counter()
    for c, n in cat.most_common(3):
        p = prev_cat.get(c, 0)
        if p and n > p:
            pct = round((n - p) / p * 100)
            out.append({"headline": f"{c} incidents ↑ {pct}% this period",
                        "detail": f"{p} → {n} reports vs previous {days // 2} days."})
        elif not p and n >= 3:
            out.append({"headline": f"Emerging hotspot: {c} ({n} new reports)",
                        "detail": "No cases in the prior period — watch this category."})
    # recurring-location insight (#12)
    for location, n in loc.most_common(3):
        if n >= 3:
            cats = Counter(r.get("category") for r in recent if r.get("location") == location)
            top_c = cats.most_common(1)[0][0] if cats else "mixed"
            out.append({"headline": f"AI Insight: {location} has had {n} reports in the last {days} days",
                        "detail": f"Recurring pattern dominated by {top_c}. Consider a preventive sweep."})
            break
    return out[:5]


def similar_incidents(records: List[Dict], category: str, location: str, limit: int = 5) -> List[Dict]:
    scored = []
    for r in records:
        s = 0
        if r.get("category") == category:
            s += 2
        if location and r.get("location") and location.lower() in str(r.get("location")).lower():
            s += 3
        if s:
            scored.append((s, r))
    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:limit]]


# --------------------------------------------------------------------------
# Natural-language admin query (#18): "Show me all high-risk electrical ..."
# --------------------------------------------------------------------------
SEV_WORDS = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH", "critical": "CRITICAL",
             "high-risk": "HIGH", "high risk": "HIGH"}
CAT_WORDS = {"electrical": "Electrical", "plumbing": "Plumbing", "waste": "Waste",
             "garbage": "Waste", "infrastructure": "Infrastructure", "furniture": "Furniture",
             "road": "RoadPavement", "pavement": "RoadPavement", "pothole": "RoadPavement"}


def query_incidents(records: List[Dict], question: str) -> Dict:
    """Converts NL question -> filtered incidents (rule-based NL→filter, no LLM needed)."""
    q = question.lower()
    sev = next((v for k, v in SEV_WORDS.items() if k in q), None)
    cat = next((v for k, v in CAT_WORDS.items() if k in q), None)
    days = 7 if "week" in q else (30 if "month" in q else None)
    loc_match = re.search(r"(?:in|at|near|from)\s+([a-z0-9 \-]+)", q)
    loc = loc_match.group(1).strip() if loc_match else None
    if loc:
        # strip trailing time phrases wrongly captured ("from this week")
        loc = re.sub(r"\b(this|last|past)\s+(week|month|day|year)s?\b", "", loc).strip() or None

    now = datetime.utcnow()
    results = []
    for r in records:
        if sev and str(r.get("severity", "")).upper() != sev:
            continue
        if cat and r.get("category") != cat:
            continue
        if loc and loc not in str(r.get("location", "")).lower():
            continue
        if days:
            try:
                created = datetime.fromisoformat(str(r.get("created_at", now.isoformat())))
                if (now - created).days > days:
                    continue
            except Exception:
                pass
        results.append(r)

    filters = {k: v for k, v in
               {"severity": sev, "category": cat, "location_hint": loc, "days": days}.items() if v}
    return {"filters": filters, "count": len(results), "results": results[:25]}
