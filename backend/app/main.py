"""
FastAPI application entry point.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.jobs import router as jobs_router
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI L&D Translation Platform",
    description="BFSI compliance training video translation — Hindi, Tamil, and 9 more Indian languages",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "mock_mode": {
            "sarvam": settings.mock_sarvam,
            "claude": settings.mock_claude,
        }
    }


@app.get("/api/languages")
def list_languages():
    from app.models.job import Language, LANGUAGE_NAMES
    return [
        {"code": lang.value, "name": LANGUAGE_NAMES[lang]}
        for lang in Language
    ]
