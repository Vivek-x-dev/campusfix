"""Judge demo — runs the whole story in one command: python -m ai.demo.

Shows: classification + severity + multimodal context shift + duplicates +
human-review + trends + NL query. Zero downloads, works offline.
"""
from __future__ import annotations

from .embeddings import DuplicateIndex
from .inference import analyze_incident, batch_evaluate, duplicate_index
from .trends import query_incidents, summarize_trends

CASES = [
    {"description": "Exposed electrical wire next to wall socket, sparking slightly",
     "location": "Lab 304", "filename": "electrical_1.jpg",
     "expected_category": "Electrical", "expected_severity": "CRITICAL"},
    {"description": "Water leaking beside power outlet in electrical lab",
     "location": "Electrical Lab, Block A", "filename": "leak_lab.jpg",
     "expected_category": "Plumbing", "expected_severity": "HIGH"},
    {"description": "Small amount of water near plants",
     "location": "Garden", "filename": "leak_garden.jpg",
     "expected_category": "Plumbing", "expected_severity": "MEDIUM"},
    {"description": "Overflowing dustbins with garbage scattered",
     "location": "Canteen back gate", "filename": "waste_1.jpg",
     "expected_category": "Waste", "expected_severity": "MEDIUM"},
    {"description": "Clean classroom, everything looks normal", "location": "Room 201",
     "filename": "normal.jpg", "expected_category": "OtherUnknown", "expected_severity": "MEDIUM"},
]


def main() -> None:
    print("=== CampusFix AI — hackathon demo ===\n")
    # seed duplicates for the story
    duplicate_index.seed([
        {"incident_id": "INC-018", "description": "Water leakage near Block B computer room",
         "location": "Block B", "issue": "Water leakage"},
    ])

    for c in CASES:
        out = analyze_incident(description=c["description"], location=c["location"],
                               filename=c["filename"])
        dup = out.get("duplicate", {})
        flag = "HUMAN REVIEW" if out["needs_human_review"] else "AUTO TICKET"
        print(f"[{c['filename']}] {c['description'][:60]}")
        print(f"  -> {out['category']} ({out['confidence']:.0%}) | {out['severity']} | "
              f"{out['department']} | {flag}")
        print(f"     Risk: {out['risk']}")
        print(f"     Action: {out['action']}")
        if dup.get("is_duplicate") and dup.get("matches"):
            m = dup["matches"][0]
            print(f"     ⚠ Possible Duplicate: {m['incident_id']} ({m['similarity']:.0%})")
        print(f"     Why: {'; '.join(out['explanation'][:2])}\n")

    print("--- metrics on mini test-set ---")
    print(batch_evaluate(CASES))

    history = [
        {"category": "Plumbing", "severity": "HIGH", "location": "Block B",
         "description": "leak", "created_at": "2026-09-10T10:00:00"},
        {"category": "Plumbing", "severity": "MEDIUM", "location": "Block B",
         "description": "drip", "created_at": "2026-09-12T10:00:00"},
        {"category": "Electrical", "severity": "CRITICAL", "location": "Lab 304",
         "description": "wire", "created_at": "2026-09-15T10:00:00"},
    ] * 3
    print("\n--- trend insights ---")
    for ins in summarize_trends(history):
        print(f"  • {ins['headline']}")
    print("\n--- NL query: 'Show me all high-risk electrical incidents from this week' ---")
    print(query_incidents(history, "Show me all high-risk electrical incidents from this week"))


if __name__ == "__main__":
    main()
