import logging
from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse, IngestRequest
from services.rag_chain import rag_service
from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Accepts message + optional conversation history + optional merit context
    passed from the Django merit calculator on the main site.
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
        raise HTTPException(status_code=500, detail="Chatbot error — please try again.")


@router.post("/rebuild-index")
async def rebuild_index(body: IngestRequest):
    """
    Admin endpoint: delete vector cache and re-embed everything.
    POST /chat/rebuild-index  { "secret": "your-ingest-secret" }
    """
    if body.secret != settings.ingest_secret:
        raise HTTPException(status_code=403, detail="Invalid secret.")
    try:
        await rag_service.rebuild_index()
        return {"status": "ok", "doc_count": rag_service.doc_count}
    except Exception as e:
        logger.error(f"Rebuild error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))