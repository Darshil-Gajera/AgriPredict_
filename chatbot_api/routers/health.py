from fastapi import APIRouter
from models.schemas import HealthResponse
from services.rag_chain import rag_service

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok" if rag_service.is_ready else "initialising",
        vector_store_loaded=rag_service.is_ready,
        doc_count=rag_service.doc_count,
    )
