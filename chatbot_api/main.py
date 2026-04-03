"""
AgriPredict Chatbot — FastAPI service
Run: uvicorn main:app --host 0.0.0.0 --port 8001 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import chat, health
from services.rag_chain import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load vector store on startup."""
    await rag_service.initialize()
    yield


app = FastAPI(
    title="AgriPredict Chatbot API",
    description="RAG-powered chatbot for Gujarat agriculture admissions",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://gajera06.pythonanywhere.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
