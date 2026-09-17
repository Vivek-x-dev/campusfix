# CampusFix AI — Smart Campus Incident & Safety Assistant

CampusFix AI transforms ad-hoc campus hazard reporting (often scattered across WhatsApp chats or verbal complaints) into an automated, visual triage pipeline. 

Students and staff snap a photo of an issue—ranging from exposed wires to structural leaks—and the platform's vision engine classifies the hazard, assigns priority, detects duplicates, and logs an actionable ticket directly to facility operations.

---

## Key Features

- **Snap-to-Report:** Mobile-first interface supporting direct camera capture.
- **Multimodal Visual Triage:** Auto-extracts hazard category, issue description, severity tier, and immediate mitigation actions.
- **Duplicate Suppression:** Proximity and visual similarity checks prevent duplicate tickets for the same issue within a 24-hour window.
- **Operations Control Center:** Real-time administrative triage table with instant status transitions (`Open` → `Assigned` → `In Progress` → `Resolved` → `Closed`).
- **Containerized Stack:** Unified orchestration with Docker Compose, Nginx reverse proxy, and CI/CD via Jenkins.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React (Vite / SPA), Tailwind CSS, Lucide Icons |
| **Backend** | FastAPI (Python 3.11), Uvicorn, Pydantic |
| **Database** | MongoDB (Motor async driver) |
| **AI Vision** | Google Gemini Multimodal Vision API |
| **Storage** | Cloudinary / AWS S3 (Incident photo assets) |
| **Reverse Proxy** | Nginx |
| **DevOps** | Docker, Docker Compose, Jenkins Pipeline |

---

## Project Structure

```text
campusfix-ai/
├── frontend/             # React SPA (Client capture + Admin UI)
├── backend/              # FastAPI application
│   └── app/
│       ├── routes/       # API endpoints (incidents, admin, users)
│       ├── models/       # Pydantic schemas & MongoDB models
│       ├── services/     # AI analysis, deduplication, storage logic
│       └── database/     # MongoDB connection setup
├── ai/                   # Vision prompts, preprocessing & inference scripts
├── nginx/                # Reverse proxy routing rules
├── docker-compose.yml    # Multi-container local/prod environment
├── Jenkinsfile           # Automated CI/CD pipeline
└── README.md