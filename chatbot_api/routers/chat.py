import os
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse, IngestRequest
from services.rag_chain import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()

INGEST_SECRET = os.getenv("INGEST_SECRET", "change-me-in-production")


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint. Accepts message + optional history + optional
    merit context passed from the Django merit calculator.
    """
    try:
        result = await rag_service.answer(
            message=request.message,
            language=request.language,
            history=request.history,
            user_merit=request.user_merit,
            user_category=request.user_category,
            student_category=request.student_category,
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chatbot error. Please try again.")


@router.post("/rebuild-index")
async def rebuild_index(body: IngestRequest):
    """Admin: re-ingest all source documents and rebuild FAISS index."""
    if body.secret != INGEST_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret.")
    try:
        await rag_service.rebuild_index()
        return {"status": "ok", "doc_count": rag_service.doc_count}
    except Exception as e:
        logger.error(f"Rebuild error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
