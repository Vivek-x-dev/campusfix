"""Reasoning module — Checklist #2, #6, #7, #8, #9, #11, #14, #17.

Multimodal: image caption + description + location all influence severity.
Location-aware: labs / electrical rooms / hostels escalate; gardens de-escalate.
Deterministic rule-engine core + optional Gemini LLM upgrade (validated JSON).
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Tuple

# --------------------------------------------------------------------------
# Department mapping (#8)
# --------------------------------------------------------------------------
DEPT_MAP = {
    "Electrical": "Electrical Maintenance",
    "Plumbing": "Plumbing",
    "Waste": "Sanitation",
    "Infrastructure": "Civil Works",
    "Furniture": "Facilities",
    "RoadPavement": "Civil Works",
    "Other": "General Administration",
    "OtherUnknown": "General Administration",
}

ACTION_MAP = {
    "Electrical": "Restrict access to the area and de-energize the circuit if safe; call Electrical Maintenance immediately.",
    "Plumbing": "Shut off the nearest valve, place warning signage for slip risk, and dispatch Plumbing.",
    "Waste": "Cordon the pile, arrange same-day clearance with Sanitation, and disinfect if needed.",
    "Infrastructure": "Barricade the affected zone and schedule Civil Works inspection within 24h.",
    "Furniture": "Remove/tape-off the broken item and raise a Facilities replacement ticket.",
    "RoadPavement": "Place cones/barriers, warn at night, and schedule Civil Works patching.",
    "Other": "Send staff to inspect and log findings.",
    "OtherUnknown": "Send staff to inspect and log findings.",
}

RISK_MAP = {
    "Electrical": "Possible electrical shock / short-circuit fire",
    "Plumbing": "Slip hazard, seepage and equipment-damage risk",
    "Waste": "Hygiene hazard, odour and pest risk",
    "Infrastructure": "Falling debris / structural weakening risk",
    "Furniture": "Injury from collapse / sharp edges",
    "RoadPavement": "Trip-and-fall / vehicle-damage risk",
    "Other": "Unverified hazard — needs inspection",
    "OtherUnknown": "Unverified hazard — needs inspection",
}

CRITICAL_PATTERNS = [
    "exposed wire", "exposed wiring", "live wire", "sparking", "spark",
    "short circuit", "smoke", "burning smell", "shock", "current leakage",
    "fire", "blast", "gas leak",
    "ceiling fell", "roof fell", "slab fell", "wall fell",
    "roof collapse", "ceiling collapse", "building collapse", "slab collapse",
    "open manhole", "manhole without cover",
]
HIGH_PATTERNS = [
    "power outlet", "socket", "switch board", "electrical lab", "server room",
    "computer room", "leak near", "beside power", "water ingress",
    "heavy leakage", "getting worse", "flooding", "blocked exit",
    "broken glass", "glass broken", "shards", "glass piece", "deep pothole",
    "may fall", "fall on", "plaster fell", " fell ",
    "burst", "gushing", "skid", "lab equipment",
]
MEDIUM_PATTERNS = ["leak", "drip", "crack", "broken", "overflow", "peeling",
                   "wobbly", "pothole", "collaps"]  # 'collaps' catches collapsed (bench) but not building collapse

WASTE_MINOR_WORDS = ["small", "minor", "slight", "tiny", "little", "paper cup"]
WASTE_HEAVY_WORDS = ["overflow", "heavy", "piles", "days", "large", "lot of", "everywhere", "smell"]

# location escalation (#6, #11)
HIGH_RISK_PLACES = [
    "electrical lab", "electrical room", "server room", "computer room",
    "laboratory", "lab", "hostel", "dormitory", "canteen", "kitchen",
    "hospital", "clinic", "staircase", "main entrance", "library",
]
LOW_RISK_PLACES = ["garden", "park", "playground", "parking", "store room", "empty corridor"]


def _contains_any(text: str, patterns: List[str]) -> List[str]:
    t = text.lower()
    return [p for p in patterns if p in t]


def assess_severity(category: str, description: str, location: str, caption: str = "") -> Tuple[str, List[str], int]:
    """Returns (severity, explanation_bullets, score). Location-aware."""
    ctx = f"{description} {location} {caption}".lower()
    score = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    bullets: List[str] = []
    level = 1  # default MEDIUM

    crit = _contains_any(ctx, CRITICAL_PATTERNS)
    high = _contains_any(ctx, HIGH_PATTERNS)
    med = _contains_any(ctx, MEDIUM_PATTERNS)

    if crit:
        level = 3
        bullets.append(f"Critical hazard signature detected: {', '.join(crit[:3])}.")
    elif high:
        level = 2
        bullets.append(f"High-risk indicator: {', '.join(high[:3])}.")

    # multimodal context test from the brief: same leak, different severity
    if "leak" in ctx or "water" in ctx:
        if any(p in ctx for p in ["electrical lab", "power outlet", "socket", "server", "computer room", "switch"]):
            level = max(level, 2)
            bullets.append("Water leak adjacent to electrical / computing equipment — escalation to HIGH.")
        elif any(p in ctx for p in ["garden", "plants", "park"]):
            level = min(level, 1) if level < 3 else level
            bullets.append("Leak in low-occupancy green area — severity tempered.")

    # location-aware risk (#11)
    low_place = None
    for place in LOW_RISK_PLACES:
        if place in ctx:
            low_place = place
            break
    # small waste in a low-occupancy spot is LOW, not MEDIUM
    if (category == "Waste" and level == 1 and not crit
            and (low_place or any(w in ctx for w in WASTE_MINOR_WORDS))
            and not any(w in ctx for w in WASTE_HEAVY_WORDS)):
        level = 0
        bullets.append(
            f"Minor waste report in low-occupancy area ({low_place or 'open area'}) — LOW.")
    for place in HIGH_RISK_PLACES:
        if place in ctx:
            if level < 3:
                level += 0  # don't auto-max; just record factor (escalate once if LOW)
                if level == 0:
                    level = 1
            bullets.append(f"Sensitive location: {place} — higher occupancy/equipment exposure.")
            break
    for place in LOW_RISK_PLACES:
        if place in ctx and level == 2 and not crit:
            bullets.append(f"Location ({place}) is low-occupancy — kept at HIGH, not CRITICAL.")
            break

    if category == "Electrical" and level < 2 and ("wire" in ctx or "socket" in ctx):
        level = 2
        bullets.append("Electrical category with visible hardware fault — minimum HIGH.")
    if category == "Waste" and level > 1 and not crit:
        level = min(level, 1) if "small" in ctx or "minor" in ctx else level
    if not med and not high and not crit and level == 1 and category in ("Other", "OtherUnknown"):
        level = 1
        bullets.append("No strong hazard signature — default MEDIUM pending inspection.")

    sev = {v: k for k, v in score.items()}[level]
    if category in ("Other", "OtherUnknown") and sev in ("HIGH", "CRITICAL"):
        sev = "MEDIUM"  # never scream about what we can't see
        bullets.append("Capped at MEDIUM: category unverified.")
    return sev, bullets, level


def estimate_damage(category: str, description: str) -> Tuple[str, str]:
    """Checklist #17 — Minor/Moderate/Severe only when supported."""
    t = description.lower()
    if any(w in t for w in ["severe", "heavy", "flooding", "collapsed", "fell down", "burnt", "fire", "large crack", "deep pothole"]):
        return "Severe", "Extent words indicate large/advanced damage."
    if any(w in t for w in ["moderate", "spreading", "getting worse", "multiple", "broken", "leaking", "crack", "overflow"]):
        return "Moderate", "Visible functional damage, contained for now."
    if any(w in t for w in ["small", "minor", "slight", "tiny", "little"]):
        return "Minor", "Reporter describes limited extent."
    return "Unknown", "Extent not clearly evidenced — no claim made."


def summarize(description: str, category: str, location: str, caption: str = "") -> str:
    """Checklist #7 — extractive, no invention. Keeps facts, drops filler."""
    filler = re.compile(r"\b(hi+|hello|please|kindly|urgent+|sir|madam|there'?s|theres|just|actually|basically)\b", re.I)
    text = filler.sub("", description or "").strip(" ,.-")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        text = caption or "Issue reported with photo evidence."
    # cap length, keep first 2 sentences max
    sents = re.split(r"(?<=[.!?])\s+", text)
    short = " ".join(sents[:2])[:280].strip()
    loc = location.strip()
    where = f" at {loc}" if loc and loc.lower() not in short.lower() else ""
    cat_word = {"Electrical": "electrical fault", "Plumbing": "water/plumbing issue",
                "Waste": "waste/hygiene issue", "Infrastructure": "infrastructure defect",
                "Furniture": "furniture damage", "RoadPavement": "road/pavement defect"}.get(category, "reported issue")
    if cat_word not in short.lower():
        return f"{short}{where} — classified as {cat_word}.".strip()
    return f"{short}{where}.".strip()


def _try_llm_upgrade(payload: Dict) -> Optional[Dict]:
    """Optional Gemini reasoning pass. Must return validated dict or None (LLM checklist)."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or os.getenv("CAMPUSFIX_OFFLINE") == "1":
        return None
    prompt = (
        "You are CampusFix risk triage. Given JSON context, reply ONLY with JSON keys: "
        "severity (LOW|MEDIUM|HIGH|CRITICAL), risk, action, department, summary, explanation (list of <=4 strings), damage (Minor|Moderate|Severe|Unknown). "
        "Be deterministic, never invent room numbers. Context: " + json.dumps(payload)[:3000]
    )
    text = _llm_text_new_sdk(api_key, prompt)
    if text is None:
        text = _llm_text_legacy(api_key, prompt)
    if not text:
        return None
    try:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        data = json.loads(m.group(0))
        if data.get("severity") not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            return None
        return data
    except Exception:
        return None  # malformed -> rule engine stands


def _llm_text_new_sdk(api_key: str, prompt: str) -> Optional[str]:
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"), contents=[prompt],
            config=types.GenerateContentConfig(temperature=0.0))
        return resp.text
    except Exception:
        return None


def _llm_text_legacy(api_key: str, prompt: str) -> Optional[str]:
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        return model.generate_content(prompt, generation_config={"temperature": 0.0}).text
    except Exception:
        return None  # timeout/failure -> rule engine fallback


def reason(
    category: str,
    confidence: float,
    description: str,
    location: str,
    caption: str = "",
    ocr_text: str = "",
) -> Dict:
    """Main reasoning entry — always returns validated fields (LLM checklist: fallback)."""
    severity, bullets, _ = assess_severity(category, description, location, caption)
    risk = RISK_MAP.get(category, RISK_MAP["Other"])
    # enrich risk with location type
    if location and any(p in location.lower() for p in HIGH_RISK_PLACES):
        risk += f" near sensitive area ({location.strip()[:60]})"
    action = ACTION_MAP.get(category, ACTION_MAP["Other"])
    department = DEPT_MAP.get(category, "General Administration")
    summary = summarize(description, category, location, caption)
    damage, damage_why = estimate_damage(category, description)

    explanation = bullets + [f"Category signal: {category} (vision confidence {confidence:.0%})."]
    if ocr_text:
        explanation.append(f"Signage/labels read from image: {ocr_text[:80]}.")
    explanation.append(damage_why)
    if category in ("Other", "OtherUnknown"):
        explanation.append("Uncertain classification — routed for human verification.")

    # LLM upgrade attempt (validated; ignored if malformed)
    llm = _try_llm_upgrade({
        "category": category, "confidence": confidence, "description": description,
        "location": location, "caption": caption, "ocr": ocr_text,
        "severity_hint": severity,
    })
    if llm:
        try:
            severity = llm.get("severity", severity).upper()
            risk = str(llm.get("risk", risk))[:300]
            action = str(llm.get("action", action))[:400]
            dept = str(llm.get("department", department))
            if dept:
                department = dept[:80]
            summary = str(llm.get("summary", summary))[:400]
            exp = llm.get("explanation")
            if isinstance(exp, list) and exp:
                explanation = [str(x)[:200] for x in exp[:4]]
            if llm.get("damage") in ("Minor", "Moderate", "Severe", "Unknown"):
                damage = llm["damage"]
        except Exception:
            pass

    return {
        "severity": severity,
        "risk": risk,
        "action": action,
        "department": department,
        "summary": summary,
        "explanation": explanation[:5],
        "damage": damage,
    }
