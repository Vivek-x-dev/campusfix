"""Full API sweep — hits every endpoint incl. image upload, timing + error paths."""
import os
os.environ.setdefault("CAMPUSFIX_OFFLINE", "1")  # contract test: no quota burn
import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from backend.app.main import app

c = TestClient(app)
passed = failed = 0

def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print("PASS", name, extra)
    else:
        failed += 1
        print("FAIL", name, extra)

# 1. health + root
check("GET /health", c.get("/health").json() == {"ok": True})
check("GET /", "ai/analyze" in str(c.get("/").json()))

# 2. analyze (text only)
r = c.post("/ai/analyze", data={"description": "Exposed wire sparking near socket", "location": "Lab 304"})
j = r.json()
check("POST /ai/analyze text", r.status_code == 200 and j["category"] == "Electrical" and j["severity"] == "CRITICAL",
      str({k: j[k] for k in ("category", "severity", "department")}))
check("X-Inference-Time-Ms header", "X-Inference-Time-Ms" in r.headers, r.headers.get("X-Inference-Time-Ms", "?"))

# 3. analyze with image bytes (generated red square JPEG — no fixture files needed)
from PIL import Image
import io
buf = io.BytesIO()
Image.new("RGB", (200, 200), (180, 40, 40)).save(buf, format="JPEG")
r = c.post("/ai/analyze", data={"description": "Crack in wall with plaster damage", "location": "Room 203"},
           files={"image": ("infra_test.jpg", buf.getvalue(), "image/jpeg")})
j = r.json()
check("POST /ai/analyze + image", r.status_code == 200 and j["category"] == "Infrastructure", j["category"])

# 4. analyze empty report -> honest fallback, never crash
r = c.post("/ai/analyze", data={"description": "", "location": ""})
j = r.json()
check("POST /ai/analyze empty", r.status_code == 200 and j["needs_human_review"] is True, j["category"])

# 5. duplicate-check true + false
r = c.post("/ai/duplicate-check", json={"description": "Water leaking in computer room Block B", "location": "Block B"})
check("POST /ai/duplicate-check (near-dup)", r.json()["matches"][0]["incident_id"] == "INC-018",
      str(r.json()["matches"][0]))
r = c.post("/ai/duplicate-check", json={"description": "Mural painting peeling in auditorium lobby", "location": "Auditorium"})
check("POST /ai/duplicate-check (non-dup)", r.json()["is_duplicate"] is False)

# 6. incidents CRUD + auto duplicate flag
r = c.post("/incidents", data={"description": "Water leakage near Block B computer room, dripping from ceiling",
                               "location": "Block B"})
j = r.json()
check("POST /incidents (dup flagged)", j["incident"]["duplicate_of"] == "INC-018", str(j["incident"].get("duplicate_of")))
check("GET /incidents", c.get("/incidents").json()["count"] >= 3)

# 7. insights + NL query + override (human-in-the-loop)
check("GET /ai/insights", len(c.get("/ai/insights").json()["insights"]) > 0)
r = c.post("/ai/query", json={"question": "Show me all high-risk electrical incidents from this week"})
check("POST /ai/query NL", "filters" in r.json() and "results" in r.json(), str(r.json()["filters"]))
r = c.post("/admin/override", json={"incident_id": "INC-018", "category": "Plumbing", "note": "judge correction"})
check("POST /admin/override", r.json()["ok"] is True)
check("GET /admin/overrides", c.get("/admin/overrides").json()["count"] == 1)
check("GET /users/me", c.get("/users/me").status_code == 200)

print("---")
print(f"API SWEEP: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
