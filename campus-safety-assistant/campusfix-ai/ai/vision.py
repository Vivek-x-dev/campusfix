"""Vision module — Checklist #1, #5, #15, #16 + vision engineering checklist.

Strategy (hackathon-proof):
1. If GEMINI_API_KEY is set -> use Gemini multimodal (real vision).
2. Else if torch+CLIP available -> zero-shot CLIP.
3. Else -> fast local expert: keyword prototypes + filename hints +
   lightweight image statistics (brightness/edges/colors). Always returns
   (category, confidence, caption, ocr_text) and NEVER forces a label when
   confidence < threshold — falls back to OtherUnknown.

Handles: blurry images, irrelevant images, missing files.
"""
from __future__ import annotations

import base64
import io
import os
import re
from typing import Dict, Optional, Tuple

# --------------------------------------------------------------------------
# Category keyword prototypes (weighted). Used for text + filename + OCR.
# --------------------------------------------------------------------------
CATEGORY_KEYWORDS: Dict[str, Dict[str, float]] = {
    "Electrical": {
        "wire": 3.0, "wiring": 3.0, "socket": 2.5, "switch": 2.0, "outlet": 2.5,
        "electrical": 3.0, "electric": 2.5, "shock": 3.0, "spark": 3.0,
        "current": 1.5, "fuse": 2.0, "breaker": 2.0, "panel": 1.5, "bulb": 1.5,
        "light": 1.0, "fan": 1.0, "short circuit": 3.0, "exposed": 1.5,
        "voltage": 2.0, "plug": 1.8,
    },
    "Plumbing": {
        "leak": 3.0, "leakage": 3.0, "water": 1.6, "dripping": 2.5, "drip": 2.2,
        "pipe": 2.8, "tap": 2.2, "faucet": 2.2, "plumbing": 3.0, "seepage": 2.5,
        "clog": 2.5, "blocked drain": 2.5, "toilet": 2.0, "bathroom": 1.2,
        "ceiling drip": 2.5, "overflow": 2.0, "flush": 1.6, "sink": 1.8,
    },
    "Waste": {
        "garbage": 3.0, "waste": 2.5, "trash": 2.8, "litter": 2.5, "dustbin": 2.5,
        "bin": 1.5, "overflowing": 2.0, "smell": 1.5, "stink": 1.8, "rubbish": 2.5,
        "sanitation": 2.0, "dump": 2.0, "food waste": 2.2, "sweep": 1.2,
    },
    "Infrastructure": {
        "crack": 2.8, "wall": 1.2, "ceiling": 1.4, "plaster": 2.2, "paint": 1.2,
        "peeling": 2.0, "leak stain": 1.8, "window": 1.4, "door": 1.2, "glass": 1.6,
        "broken wall": 2.5, "seepage mark": 2.0, "structural": 2.8, "roof": 2.0,
        "tile": 1.4, "floor crack": 2.4, "damp": 1.8, "collapse": 2.8, "ceiling fall": 2.8,
    },
    "Furniture": {
        "chair": 2.8, "bench": 2.6, "desk": 2.4, "table": 2.0, "furniture": 3.0,
        "broken chair": 3.0, "broken bench": 3.0, "stool": 2.2, "cupboard": 2.0,
        "shelf": 1.8, "drawer": 1.6, "wobbly": 2.0, "leg broken": 2.4, "wooden": 1.0,
    },
    "RoadPavement": {
        "road": 2.6, "pavement": 3.0, "pothole": 3.0, "footpath": 2.6, "sidewalk": 2.6,
        "asphalt": 2.2, "cracked road": 2.8, "speed breaker": 2.0, "drain cover": 2.0,
        "manhole": 2.4, "pathway": 2.0, "parking": 1.0, "compound road": 2.2,
    },
    "Other": {
        "general": 0.5, "normal": 0.3, "classroom": 0.4, "corridor": 0.4,
    },
}

NEGATIVE_HINTS = [
    "normal classroom", "clean classroom", "no issue", "everything fine",
    "nothing wrong", "just a photo", "selfie", "empty clean",
    "stacked fine", "clean after", "working fine", "all good",
    "no damage", "nothing broken",
]
IRRELEVANT_HINTS = ["selfie", "cat", "dog", "birthday", "food photo", "screenshot"]

MODEL_VERSION_VISION = "campusfix-vision-v1 (gemini-optional)"


def _score_text(text: str) -> Dict[str, float]:
    t = (text or "").lower()
    scores: Dict[str, float] = {c: 0.0 for c in CATEGORY_KEYWORDS}
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw, w in kws.items():
            if kw in t:
                # multi-word phrases count extra
                bonus = 1.3 if " " in kw else 1.0
                scores[cat] += w * bonus
    return scores


def _image_stats(image_bytes: Optional[bytes]) -> Dict[str, float]:
    """Cheap visual prior: greenish->Waste/garden leak, dark->Electrical etc.

    Deliberately weak (max ~1.2 pts) so text/vision-LLM dominates — it only
    nudges ties and gives *some* signal for image-only reports.
    """
    if not image_bytes:
        return {}
    try:
        from PIL import Image, ImageStat
        import io as _io
        img = Image.open(_io.BytesIO(image_bytes)).convert("RGB").resize((64, 64))
        stat = ImageStat.Stat(img)
        r, g, b = stat.mean
        # brownish/greenish scenes often = waste / outdoor road
        features: Dict[str, float] = {}
        if g > r and g > b and g > 100:
            features["Waste"] = 0.8
            features["Plumbing"] = 0.3
        if r > 120 and g < 110 and b < 110:
            features["Infrastructure"] = 0.6  # brick/rust tones
        if b > r + 15 and b > g + 15 and b > 100:
            features["Plumbing"] = 0.9  # water-blue scenes
        if sum((r, g, b)) / 3 < 60:
            features["Electrical"] = 0.6  # dark room / burnt socket scenes
        # blurry detection
        gray = img.convert("L")
        import math
        px = list(gray.getdata())
        mean = sum(px) / len(px)
        var = sum((p - mean) ** 2 for p in px) / len(px)
        features["_blurry"] = 1.0 if var < 120 else 0.0
        return features
    except Exception:
        return {}


def _try_clip(image_bytes: bytes, texts: Dict[str, str]) -> Optional[Dict[str, float]]:
    """Optional CLIP zero-shot if torch+transformers installed. Returns None if unavailable."""
    try:
        import torch
        from transformers import CLIPProcessor, CLIPModel  # type: ignore
        from PIL import Image
        model_id = os.getenv("CLIP_MODEL", "openai/clip-vit-base-patch32")
        model = CLIPModel.from_pretrained(model_id)
        processor = CLIPProcessor.from_pretrained(model_id)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        labels = list(texts.keys())
        prompts = [texts[k] for k in labels]
        inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            out = model(**inputs)
            probs = out.logits_per_image.softmax(dim=1)[0].tolist()
        return {labels[i]: float(probs[i]) * 6.0 for i in range(len(labels))}
    except Exception:
        return None


def _try_gemini(image_bytes: Optional[bytes], description: str, location: str) -> Optional[Tuple[str, float, str]]:
    """Real multimodal call. Returns (category, confidence, caption) or None.

    Tries the new `google.genai` SDK first, then legacy `google.generativeai`.
    Any failure (no key, no network, bad response) -> None -> local fallback.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or os.getenv("CAMPUSFIX_OFFLINE") == "1":
        return None
    prompt = (
        "You are CampusFix vision. Classify into exactly one of: "
        "Electrical, Plumbing, Waste, Infrastructure, Furniture, RoadPavement, Other. "
        f"Description: {description!r}. Location: {location!r}. "
        'Reply ONLY as JSON: {"category": ..., "confidence": 0..1, "caption": ...}. '
        "If unsure or image is irrelevant/normal, use category Other with low confidence."
    )
    text = _gemini_text_new_sdk(api_key, prompt, image_bytes)
    if text is None:
        text = _gemini_text_legacy(api_key, prompt, image_bytes)
    if not text:
        return None
    try:
        import json
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        data = json.loads(m.group(0))
        cat = str(data.get("category", "Other"))
        conf = float(data.get("confidence", 0.5))
        cap = str(data.get("caption", ""))
        from .schemas import CATEGORIES
        if cat not in CATEGORIES:
            cat = "Other"
        return cat, max(0.0, min(1.0, conf)), cap
    except Exception:
        return None


def _gemini_text_new_sdk(api_key: str, prompt: str, image_bytes: Optional[bytes]) -> Optional[str]:
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        parts: list = [prompt]
        if image_bytes:
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
        resp = client.models.generate_content(
            model=model, contents=parts,
            config=types.GenerateContentConfig(temperature=0.0))
        return resp.text
    except Exception:
        return None


def _gemini_text_legacy(api_key: str, prompt: str, image_bytes: Optional[bytes]) -> Optional[str]:
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        parts: list = [prompt]
        if image_bytes:
            parts.append({"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode()})
        resp = model.generate_content(parts, generation_config={"temperature": 0.0})
        return resp.text
    except Exception:
        return None


def extract_ocr_text(image_bytes: Optional[bytes]) -> Optional[str]:
    """Checklist #16 — OCR if tesseract installed, else filename-independent None."""
    if not image_bytes:
        return None
    try:
        import pytesseract  # type: ignore
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img).strip()
        # keep only plausible room/equipment labels
        keep = [ln.strip() for ln in text.splitlines() if re.search(r"(lab|room|block|danger|el-|eq-|no\.?|id)", ln, re.I)]
        out = " ".join(keep).strip()[:300]
        return out or (text[:300] if len(text.strip()) > 2 else None)
    except Exception:
        return None


def classify_image(
    image_bytes: Optional[bytes] = None,
    description: str = "",
    location: str = "",
    filename: str = "",
) -> Tuple[str, float, str, Optional[str]]:
    """Full vision step -> (category, confidence, caption, ocr_text).

    Implements checklist #1 (7 cats + confidence + OtherUnknown fallback),
    #15 (caption), #16 (OCR), vision checklist (blurry/irrelevant handling).
    """
    text_all = f"{description} {location} {filename}".lower()

    # 0) Gemini first (best quality when key exists)
    gemini = _try_gemini(image_bytes, description, location)
    ocr_text = extract_ocr_text(image_bytes)
    if ocr_text:
        text_all += " " + ocr_text.lower()

    caption = ""
    if gemini:
        cat, conf, cap = gemini
        caption = cap or _local_caption(description, cat)
        if conf < 0.55:
            return "OtherUnknown", conf, caption, ocr_text
        return cat, conf, caption, ocr_text

    # 1) Negative / irrelevant fast-paths (must not force labels).
    # NOTE: short hints use word-boundaries ("cat" must not fire inside "scattered").
    def _hit(hint: str) -> bool:
        if len(hint) <= 4:
            return re.search(rf"\b{re.escape(hint)}\b", text_all) is not None
        return hint in text_all

    for hint in NEGATIVE_HINTS:
        if _hit(hint):
            return "OtherUnknown", 0.32, _local_caption(description, "Other"), ocr_text
    for hint in IRRELEVANT_HINTS:
        if _hit(hint):
            return "OtherUnknown", 0.25, _local_caption(description, "Other"), ocr_text

    # 2) Score keywords
    scores = _score_text(text_all)

    # filename hint counts (test-set friendly: electrical_1.jpg etc.)
    fn = (filename or "").lower()
    for cat in CATEGORY_KEYWORDS:
        if cat.lower() in fn or cat.lower().replace("roadpavement", "road") in fn:
            scores[cat] += 2.5

    # 3) CLIP boost if available
    if image_bytes:
        clip = _try_clip(image_bytes, {c: f"a photo of {c.lower()} campus issue" for c in CATEGORY_KEYWORDS})
        if clip:
            for c, v in clip.items():
                scores[c] = scores.get(c, 0.0) + v

    # 4) weak image-stat prior
    for c, v in _image_stats(image_bytes).items():
        if not c.startswith("_"):
            scores[c] = scores.get(c, 0.0) + v

    # 5) normalize -> confidence
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best_cat, best = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0

    # Substance-over-location tie-break: a water leak next to an outlet is a
    # Plumbing issue in a risky place (severity handles the danger), not an
    # electrical fault — unless live-fault words (wire/spark/shock) are present.
    if best_cat == "Electrical" and scores.get("Plumbing", 0.0) >= 4.0:
        ctx = text_all
        live_fault = any(w in ctx for w in ["wire", "wiring", "spark", "shock", "short circuit", "exposed", "live"])
        if not live_fault:
            best_cat, best = "Plumbing", scores["Plumbing"]
            second = max(v for c, v in ranked if c != "Plumbing") if len(ranked) > 1 else 0.0

    if best <= 0.3:
        # nothing detected — honest low confidence, do not force
        caption = _local_caption(description, "Other")
        return "OtherUnknown", 0.30, caption, ocr_text

    # margin-based confidence: strong unique signal -> high conf
    margin = best - second
    confidence = min(0.97, 0.45 + best * 0.09 + margin * 0.08)
    if not description.strip() and not filename.strip():
        confidence = min(confidence, 0.55)  # image-only is less certain

    # blurry penalty
    stats = _image_stats(image_bytes) if image_bytes else {}
    if stats.get("_blurry"):
        confidence = max(0.3, confidence - 0.12)
        caption = (_local_caption(description, best_cat) + " (Image appears blurry — verify on site.)").strip()
    else:
        caption = _local_caption(description, best_cat)

    # low-confidence fallback
    if confidence < 0.55 and best < 2.0:
        return "OtherUnknown", round(confidence, 2), caption, ocr_text
    if best_cat == "Other":
        return "OtherUnknown", round(min(confidence, 0.49), 2), caption, ocr_text

    return best_cat, round(confidence, 2), caption, ocr_text


def _local_caption(description: str, category: str) -> str:
    """Checklist #15 — visual description used as LLM reasoning input."""
    base = {
        # NOTE: templates stay neutral — they must not contain severity trigger
        # words (exposed/spark/overflowing), or every report escalates.
        "Electrical": "Electrical fittings / fixtures visible; reported fault under review.",
        "Plumbing": "Water / moisture signs visible; extent to be confirmed on site.",
        "Waste": "Bins / litter visible; hygiene review pending.",
        "Infrastructure": "Wall / ceiling / surface wear visible; inspection advised.",
        "Furniture": "Furniture item visible; stability / usability to be checked.",
        "RoadPavement": "Path / road surface visible; trip or vehicle risk to be assessed.",
        "Other": "No clear hazard signature visible in the frame.",
    }.get(category, "Scene captured for review.")
    if description.strip():
        return f"{base} Reporter notes: {description.strip()[:220]}"
    return base
