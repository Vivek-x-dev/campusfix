# CampusFix AI

CampusFix is a reporting tool for campus maintenance and safety issues. Someone spots a problem — exposed wire, water leak, overflowing bin — takes a photo, adds a short description and location, and submits it. The backend runs it through classification, risk scoring, and duplicate detection, then stores it as a ticket that admin can triage.

It was built to replace informal reporting (WhatsApp groups, verbal complaints) with something facilities can actually track.

## What it does

- Report form with photo upload, description, and location
- Automatic classification (electrical, plumbing, waste, etc.) with confidence score
- Severity and department suggestion based on description + location context
- Duplicate check so the same leak doesn't create five tickets
- Dashboard for admin to view, filter, and update ticket status (Open → Assigned → In Progress → Resolved → Closed)
- Map, analytics, and AI analysis pages on the frontend
- Plain-language explanation for each decision, plus a human-review flag when confidence is low

## How the AI pipeline works

`image + text → vision → reasoning → duplicate check → ticket / review`

1. **Vision (`ai/vision.py`)** — guesses the category from the image bytes, filename, and description. Uses Gemini if a key is set, otherwise local heuristics. Also pulls a caption and OCR text when available.
2. **Reasoning (`ai/reasoning.py`)** — takes the category + location and decides severity, risk summary, suggested action, and department. Location matters here (water near an electrical lab scores higher than water in a garden).
3. **Duplicates (`ai/embeddings.py`)** — compares new reports against recent ones by text similarity and location. Uses sentence-transformers if installed, hash fallback otherwise.
4. **Confidence gate (`ai/inference.py`)** — low confidence or unknown category goes to human review instead of auto-ticketing.
5. **Trends (`ai/trends.py`)** — simple aggregation + natural-language query over stored incidents.

Schemas are defined once in `ai/schemas.py` and validated with Pydantic.

## Project layout

```
campusfix-ai/
├── frontend/           # React + Vite + Tailwind admin/report UI
│   └── src/
│       ├── pages/      # Landing, Dashboard, ReportIncident, AIAnalysis, CampusMap, Analytics, IncidentDetails
│       ├── components/ # Navbar, CanvasScene, ui/*
│       └── lib/api.ts  # backend client
├── backend/
│   └── app/
│       ├── main.py         # FastAPI entry
│       ├── routes/         # incidents.py (AI + tickets), admin.py, users.py
│       ├── models/         # Pydantic models, status list
│       ├── services/       # ai_service, duplicate_service, storage_service
│       └── incidents_store.json  # file-backed ticket store (used when Mongo isn't configured)
├── ai/
│   ├── vision.py, reasoning.py, embeddings.py, inference.py, trends.py, schemas.py
│   ├── demo.py             # one-command end-to-end demo
│   ├── evaluate*.py, verify_api.py, make_demo_report.py
│   └── tests/              # pytest suite
├── nginx/default.conf
├── docker-compose.yml
├── Jenkinsfile
└── README.md
```

Note: `docker-compose.yml`, `Jenkinsfile`, and `nginx/default.conf` are placeholders right now — local dev runs without Docker (see below).

## Getting started

Prerequisites: Python 3.11+, Node 18+, npm. MongoDB is optional. Gemini API key is optional.

### 1. Backend + AI (offline, no key needed)

Run from `campus-safety-assistant/campusfix-ai/`:

```bash
pip install -r backend/requirements.txt

# quick end-to-end check
python -m ai.demo

# start the API
uvicorn backend.app.main:app --reload
```

API will be at `http://127.0.0.1:8000`, docs at `http://127.0.0.1:8000/docs`.

### 2. Frontend

In a second terminal, from `campus-safety-assistant/campusfix-ai/frontend/`:

```bash
npm install
cp .env.example .env   # defaults to VITE_API_URL=http://127.0.0.1:8000
npm run dev
```

App runs at `http://localhost:3000`.

### 3. Enable live vision (optional)

Copy `.env.example` to `.env` in `campusfix-ai/` and set:

```
GEMINI_API_KEY=your-key-here
```

With a key, vision and reasoning call Gemini automatically. Without it, everything falls back to the offline engine. To force offline mode even with a key set:

```bash
CAMPUSFIX_OFFLINE=1 python -m ai.demo
```

Other optional env vars are listed in `.env.example` (`MONGO_URI`, `CLIP_MODEL`, `ST_MODEL`). If Mongo isn't set, tickets are kept in memory and persisted to `backend/app/incidents_store.json`.

## API reference

Base URL: `http://127.0.0.1:8000`

| Method | Endpoint | What it does |
| ------ | -------- | ------------ |
| POST | `/ai/analyze` | Analyze photo + description, returns category, severity, action, duplicates (form fields: `description`, `location`, `building`, `room`, `location_type`, `image`) |
| POST | `/ai/duplicate-check` | Check if a description/location is a duplicate (`{description, location}`) |
| POST | `/incidents` | Analyze and save in one call (used by Report page) |
| POST | `/incidents/save` | Save an already-computed analysis |
| GET | `/incidents` | List all tickets |
| GET | `/incidents/{id}` | Get one ticket |
| PATCH | `/incidents/{id}/status` | Update status, body: `{"status": "Assigned"}` |
| GET | `/ai/insights` | Trend summary over stored tickets |
| POST | `/ai/query` | Natural-language filter over tickets (`{question}`) |
| GET | `/health` | Health check |

Every response includes an `X-Inference-Time-Ms` header.

## Demo and evaluation scripts

```bash
# full story: classification, severity shift by location, duplicates, trends, NL query
python -m ai.demo

# tests
python -m pytest ai/tests -q

# verify the running API
python -m ai.verify_api

# image-based eval + HTML report (opens in browser)
python -m ai.evaluate_images
python -m ai.make_demo_report

# live Gemini eval on 22 photos (needs GEMINI_API_KEY, uses quota)
python -m ai.evaluate_live
```

Last measured on the 22-photo set: offline image eval 100% category accuracy, live Gemini run 100% category / ~95% severity (one borderline case scored CRITICAL instead of HIGH).

## Config

Backend `.env` (see `.env.example`):

```
GEMINI_API_KEY=       # enables live vision + reasoning
GEMINI_MODEL=gemini-3.6-flash
MONGO_URI=            # if unset, uses JSON file store
MONGO_DB=campusfix
```

Frontend `.env`:

```
VITE_API_URL=http://127.0.0.1:8000
```

## Current state

Works locally as described above. A few things to know before deploying:

- Ticket storage defaults to a local JSON file, not Mongo. Fine for demo, not for production.
- Auth is minimal (`routes/users.py` is a stub).
- Docker / Nginx / Jenkins files exist but are empty — deployment still needs to be wired up.
- Frontend uses mock data in a couple of places when the backend is unreachable (see `src/data/mockData.ts` and `src/lib/api.ts`).
