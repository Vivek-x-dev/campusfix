"""CampusFix FastAPI entry — wires AI pipeline to HTTP (API checklist)."""
from __future__ import annotations
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .routes import incidents, admin, users

app = FastAPI(title="CampusFix AI", version="1.0.0",
              description="Snap-to-report campus safety triage: vision + risk + dedup.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def _timing(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    resp.headers["X-Inference-Time-Ms"] = f"{(time.perf_counter()-t0)*1000:.1f}"
    return resp


@app.get("/")
async def root():
    return {"service": "CampusFix AI", "docs": "/docs",
            "endpoints": ["POST /ai/analyze", "POST /ai/duplicate-check",
                          "POST /incidents", "GET /ai/insights", "POST /ai/query"]}


@app.get("/health")
async def health():
    return {"ok": True}


app.include_router(incidents.router, tags=["incidents"])
app.include_router(admin.router, tags=["admin"])
app.include_router(users.router, tags=["users"])
