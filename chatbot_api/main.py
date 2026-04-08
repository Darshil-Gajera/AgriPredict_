"""
AgriPredict Chatbot — FastAPI service
======================================
Local dev:
    uvicorn main:app --host 0.0.0.0 --port 8001 --reload

PythonAnywhere (WSGI):
    In your WSGI config file set:
        import sys
        sys.path.insert(0, '/home/<username>/chatbot')
        from main import app as application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat, health
from services.rag_chain import rag_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the RAG service on startup (loads/builds vector cache)."""
    await rag_service.initialize()
    yield


app = FastAPI(
    title="AgriPredict Chatbot API",
    description=(
        "RAG-powered bilingual chatbot (English + Gujarati) for Gujarat "
        "agriculture university admissions — JAU, AAU, NAU, SDAU."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — allow requests from the main Django site ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.get("/")
async def root():
    return {
        "service": "AgriPredict Chatbot API",
        "version": "2.0.0",
        "status": "ok" if rag_service.is_ready else "initialising",
        "docs": "/docs",
    }