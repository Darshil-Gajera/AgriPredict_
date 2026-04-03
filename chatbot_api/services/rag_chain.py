"""
RAG chain service.

Architecture:
  user message
    → intent classifier
    → context injector (merit score, student category if provided)
    → retriever (FAISS similarity search)
    → prompt builder (bilingual: en / gu)
    → Gemini 1.5 Flash
    → structured response
"""

import logging
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from config import get_settings
from models.schemas import ChatMessage, SourceDocument
from services.ingest import build_vector_store, load_vector_store

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_EN = """You are AgriBot, the official admission assistant for AgriPredict — a platform
that helps students navigate Gujarat agriculture university admissions (JAU, AAU, NAU, SDAU).

You help with:
- Merit score calculation (theory marks + GUJCET formula)
- College eligibility and cutoff information
- Scholarship details and eligibility
- Admission process, dates, and required documents

Rules:
- Answer ONLY based on the provided context documents. If you don't know, say so clearly.
- Be concise, friendly, and use simple language suitable for Class 12 students.
- If the user has provided their merit score or category, use it to personalise your answer.
- Always mention the source college code or year when citing cutoff data.
- For scholarship eligibility, always mention income limits and domicile requirements.

User context:
{user_context}

Context from documents:
{context}

Chat history:
{chat_history}

Question: {question}

Answer:"""

SYSTEM_PROMPT_GU = """તમે AgriBot છો, AgriPredict નો સત્તાવાર પ્રવેશ સહાયક — એક એવું platform જે
વિદ્યાર્થીઓને ગુજરાત કૃષિ યુનિવર્સિટી (JAU, AAU, NAU, SDAU) ના પ્રવેશ
navigate કરવામાં મદદ કરે છે.

તમે આ બાબતોમાં મદદ કરો છો:
- Merit score ગણતરી (Theory marks + GUJCET formula)
- College eligibility અને cutoff માહિતી
- Scholarship વિગતો અને eligibility
- પ્રવેશ પ્રક્રિયા, તારીખો અને જરૂરી દસ્તાવેજો

નિયમો:
- ફક્ત આપેલ context documents ના આધારે જ જવાબ આપો.
- સ્પષ્ટ અને સરળ ભાષામાં જવાબ આપો.
- Cutoff data ટાંકતી વખતે college code અથવા year ઉલ્લેખ કરો.

User context:
{user_context}

Documents context:
{context}

Chat history:
{chat_history}

પ્રશ્ન: {question}

જવાબ:"""

INTENT_KEYWORDS = {
    "merit": ["merit", "score", "marks", "calculate", "gujcet", "theory", "ગણતરી", "merit score"],
    "college": ["college", "cutoff", "admission", "seat", "eligible", "university", "jau", "aau", "nau", "sdau"],
    "scholarship": ["scholarship", "financial", "money", "fee", "mysy", "nsp", "inspire", "ongc", "શિષ્યવૃત્તિ"],
    "admission": ["process", "date", "document", "form", "registration", "procedure", "certificate", "upload"],
}


def _detect_intent(message: str) -> str:
    msg_lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return intent
    return "general"


def _build_user_context(merit, category, student_category) -> str:
    if not any([merit, category, student_category]):
        return "No user context provided."
    parts = []
    cat_names = {"1": "Core Agriculture", "2": "Technical Agriculture", "3": "Home & Community Science"}
    if merit:
        parts.append(f"Merit score: {merit}")
    if category:
        parts.append(f"Category: {cat_names.get(str(category), category)}")
    if student_category:
        parts.append(f"Reservation: {student_category}")
    return " | ".join(parts)


def _format_history(history: list) -> str:
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history[-6:]:
        prefix = "Human" if msg.role == "user" else "Assistant"
        lines.append(f"{prefix}: {msg.content}")
    return "\n".join(lines)


def _docs_to_sources(docs: list[Document]) -> list[SourceDocument]:
    seen = set()
    sources = []
    for doc in docs:
        src = doc.metadata.get("source", doc.metadata.get("filename", "document"))
        if src not in seen:
            seen.add(src)
            sources.append(SourceDocument(
                source=src,
                page=doc.metadata.get("page"),
                content_preview=doc.page_content[:120].strip(),
            ))
    return sources


class RAGService:
    def __init__(self):
        self._vector_store: Optional[FAISS] = None
        self._llm = None
        self._ready = False
        self._doc_count = 0

    async def initialize(self):
        logger.info("Initialising RAG service...")

        embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
        store_path = Path(settings.vector_store_path)

        if store_path.exists() and any(store_path.iterdir()):
            self._vector_store = load_vector_store(str(store_path))
        else:
            logger.warning("No vector store found — building from scratch.")
            self._vector_store = build_vector_store()

        self._llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            google_api_key=settings.google_api_key,
            convert_system_message_to_human=True,
        )

        self._doc_count = self._vector_store.index.ntotal
        self._ready = True
        logger.info(f"RAG service ready — {self._doc_count} vectors indexed.")

    async def rebuild_index(self):
        self._ready = False
        self._vector_store = build_vector_store()
        self._doc_count = self._vector_store.index.ntotal
        self._ready = True
        logger.info(f"Index rebuilt — {self._doc_count} vectors.")

    async def answer(
        self,
        message: str,
        language: str = "en",
        history: list = None,
        user_merit: Optional[float] = None,
        user_category: Optional[str] = None,
        student_category: Optional[str] = None,
    ) -> dict:
        if not self._ready:
            return {
                "answer": "Chatbot is still initialising, please try again shortly.",
                "language": language,
                "sources": [],
                "intent": "general",
            }

        history = history or []
        intent = _detect_intent(message)
        user_context = _build_user_context(user_merit, user_category, student_category)
        chat_history = _format_history(history)

        # Retrieve top-k relevant chunks
        retriever = self._vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.max_retrieved_docs},
        )
        relevant_docs = retriever.invoke(message)
        context = "\n\n---\n\n".join(d.page_content for d in relevant_docs)

        # Build filled prompt
        template = SYSTEM_PROMPT_GU if language == "gu" else SYSTEM_PROMPT_EN
        prompt = PromptTemplate(
            input_variables=["user_context", "context", "chat_history", "question"],
            template=template,
        )
        filled = prompt.format(
            user_context=user_context,
            context=context,
            chat_history=chat_history,
            question=message,
        )

        response = await self._llm.ainvoke(filled)
        answer_text = response.content if hasattr(response, "content") else str(response)

        return {
            "answer": answer_text.strip(),
            "language": language,
            "sources": _docs_to_sources(relevant_docs),
            "intent": intent,
        }

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def doc_count(self) -> int:
        return self._doc_count


rag_service = RAGService()
