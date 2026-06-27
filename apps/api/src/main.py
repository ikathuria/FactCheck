"""FactCheck FastAPI application entry point.

Run locally:
    cd apps/api && uvicorn src.main:app --reload
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load env from apps/api/.env or repo root, whichever exists
for _env in (Path(__file__).parents[1] / ".env", Path(__file__).parents[3] / ".env"):
    if _env.exists():
        load_dotenv(_env)
        break

app = FastAPI(
    title="FactCheck API",
    description="Domain-agnostic fact-checking — 5-agent LangGraph pipeline.",
    version="0.1.0",
)

# CORS — comma-separated origins from ALLOWED_ORIGINS, default to localhost dev
_origins = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe — used for Render keep-alive and smoke testing."""
    return {"status": "ok"}
