"""Pytest suite — testing checklist: categories, severity, duplicates,
low-quality/irrelevant/missing inputs, LLM-failure fallback, override store."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ai.embeddings import DuplicateIndex  # noqa: E402
from ai.inference import analyze_incident, batch_evaluate  # noqa: E402
from ai.schemas import AIAnalysisResult  # noqa: E402


def test_electrical_critical():
    out = analyze_incident("Exposed electrical wire sparking near socket", "Lab 304",
                           filename="electrical.jpg", check_duplicates=False)
    assert out["category"] == "Electrical"
    assert out["severity"] in ("HIGH", "CRITICAL")
    assert out["confidence"] > 0.55
    AIAnalysisResult(**{k: out[k] for k in AIAnalysisResult.model_fields})


def test_multimodal_context_shift():
    lab = analyze_incident("Water leaking beside power outlet", "Electrical Lab",
                           check_duplicates=False)
    garden = analyze_incident("Small amount of water near plants", "Garden",
                              check_duplicates=False)
    order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    assert order[lab["severity"]] > order[garden["severity"]]


def test_negative_image_low_confidence():
    out = analyze_incident("Clean classroom, everything normal", "Room 201", check_duplicates=False)
    assert out["category"] in ("Other", "OtherUnknown")
    assert out["needs_human_review"] is True


def test_missing_inputs_do_not_crash():
    out = analyze_incident("", "", check_duplicates=False)
    assert out["category"] in ("Other", "OtherUnknown", "Waste", "Plumbing",
                               "Electrical", "Infrastructure", "Furniture", "RoadPavement")
    AIAnalysisResult(**{k: out[k] for k in AIAnalysisResult.model_fields})


def test_duplicate_detection():
    idx = DuplicateIndex()  # default tuned threshold (0.62)
    idx.add("INC-018", "Water leakage near Block B computer room", "Block B")
    is_dup, matches = idx.check("Water leaking in computer room Block B", "Block B")
    assert is_dup and matches[0]["incident_id"] == "INC-018"
    is_dup2, _ = idx.check("Broken chair in library reading hall", "Library")
    assert not is_dup2


def test_fallback_schema():
    fb = AIAnalysisResult.fallback("test")
    assert fb.category == "OtherUnknown" and fb.needs_human_review


def test_metrics_harness_runs():
    m = batch_evaluate([{"description": "Overflowing garbage bins", "location": "Canteen",
                         "expected_category": "Waste", "expected_severity": "MEDIUM"}])
    assert "category_accuracy" in m and "avg_inference_ms" in m
