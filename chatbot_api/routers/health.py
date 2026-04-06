from fastapi import APIRouter
from models.schemas import HealthResponse
from services.rag_chain import rag_service
from config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok" if rag_service.is_ready else "initialising",
        vector_store_loaded=rag_service.is_ready,
        doc_count=rag_service.doc_count,
        model=settings.llm_model,
    )