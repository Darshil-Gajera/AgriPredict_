"""
services/rag_chain.py — RAG chain service (Gemini-native, no FAISS/HuggingFace).

Architecture:
  user message
    → query embedding via Gemini text-embedding-004
    → cosine similarity search over in-memory chunk corpus
    → smart context builder (cutoff filter by merit/category/reservation)
    → bilingual prompt (en / gu) → Gemini 1.5 Flash
    → structured ChatResponse
"""

import math
import logging
import asyncio
from pathlib import Path
from typing import Optional

import google.generativeai as genai

from config import get_settings
from models.schemas import ChatMessage, SourceDocument
from services.ingest import (
    Chunk,
    BUILTIN_CUTOFFS,
    build_corpus,
    load_corpus,
    _cutoff_chunks_from_builtin,
    _faq_chunks_from_builtin,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Prompts ───────────────────────────────────────────────────────────────────

_SYSTEM_EN = """You are AgriBot, the friendly official admission assistant for AgriPredict
(https://gajera06.pythonanywhere.com) — a platform helping students navigate
Gujarat agriculture university admissions for JAU, AAU, NAU and SDAU.

You help with:
• Merit score calculation (Theory 60% + GUJCET 40% + bonus marks)
• College cutoffs and eligibility based on merit and reservation category
• Scholarship details (MYSY, NSP, INSPIRE, ONGC, State Post-Matric)
• Admission process, required documents, important dates
• University-wise course information

Rules:
- Answer ONLY from the context provided below. If info is not in context, say "I don't have that information — please check gajera06.pythonanywhere.com or the official GSEB portal."
- Be concise, warm, and use simple language for Class 12 students.
- When listing cutoffs, always show them as a neat table or bullet list.
- When a student's merit and category are provided, highlight which colleges they qualify for.
- Never guess or fabricate cutoff numbers.

{user_context_section}

--- CONTEXT FROM KNOWLEDGE BASE ---
{context}
--- END CONTEXT ---

Chat History:
{chat_history}

Student Question: {question}

Answer (in English):"""

_SYSTEM_GU = """તમે AgriBot છો, AgriPredict (https://gajera06.pythonanywhere.com) ના
સત્તાવાર admission assistant. ગુજરાત Agriculture Universities (JAU, AAU, NAU, SDAU) ના
પ્રવેશ અંગે વિદ્યાર્થીઓને મદદ કરો.

તમે મદદ કરો:
• Merit score ગણતરી (Theory 60% + GUJCET 40% + bonus marks)
• College cutoffs અને eligibility
• Scholarship (MYSY, NSP, INSPIRE, ONGC)
• Admission process, documents, dates

નિયમો:
- ફક્ત નીચે આપેલ context ના આધારે જ જવાબ આપો.
- સ્પષ્ટ, સરળ ભાષામાં જવાબ આપો.
- Cutoff numbers ક્યારેય ઉchatptestate ન કરો.

{user_context_section}

--- KNOWLEDGE BASE ---
{context}
--- END ---

Chat History:
{chat_history}

Student Question: {question}

Answer (ગુજરાતી માં):"""

INTENT_MAP = {
    "merit": ["merit", "score", "marks", "calculate", "gujcet", "theory", "formula",
               "ગણતરી", "merit score", "bonus", "percentage", "%"],
    "college": ["college", "cutoff", "eligible", "eligibility", "university", "seat",
                 "jau", "aau", "nau", "sdau", "horticulture", "forestry", "agri", "biotechnology",
                 "engineering", "food technology", "community science", "which college"],
    "scholarship": ["scholarship", "mysy", "nsp", "inspire", "ongc", "financial", "fee",
                     "money", "income", "waiver", "stipend", "post matric", "શિષ્યવૃત્તિ"],
    "admission": ["process", "document", "form", "registration", "date", "deadline",
                   "certificate", "upload", "round", "token fee", "report", "steps"],
}


def _detect_intent(message: str) -> str:
    m = message.lower()
    for intent, keywords in INTENT_MAP.items():
        if any(kw in m for kw in keywords):
            return intent
    return "general"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _format_history(history: list[ChatMessage]) -> str:
    if not history:
        return "No previous conversation."
    lines = []
    for msg in history[-6:]:
        prefix = "Student" if msg.role == "user" else "AgriBot"
        lines.append(f"{prefix}: {msg.content}")
    return "\n".join(lines)


def _build_user_context_section(merit, category, student_category) -> str:
    if not any([merit, category, student_category]):
        return ""
    cat_names = {
        "1": "Category 1 — Agriculture / Horticulture / Forestry / Biotechnology",
        "2": "Category 2 — Agricultural Engineering / Food Technology / Agri IT",
        "3": "Category 3 — Community Science / Food Nutrition",
    }
    parts = []
    if merit:
        parts.append(f"Merit Score: **{merit}%**")
    if category:
        parts.append(f"Admission Category: {cat_names.get(str(category), category)}")
    if student_category:
        parts.append(f"Reservation: **{student_category}**")

    # Add eligible colleges based on the data
    eligible = []
    if merit and category:
        cat = str(category)
        res = student_category or "GENERAL"
        for c in BUILTIN_CUTOFFS.get(cat, []):
            cutoff = c.get(res, c.get("GENERAL"))
            if cutoff and isinstance(cutoff, (int, float)) and merit >= cutoff:
                eligible.append(f"  ✓ {c['name']} ({c['course']}) — cutoff: {cutoff}%")

    section = "--- STUDENT CONTEXT ---\n" + "\n".join(parts)
    if eligible:
        section += f"\n\nEligible colleges for this student ({len(eligible)} found):\n" + "\n".join(eligible[:10])
    elif merit and category:
        section += "\n\n(No colleges found for this merit/category combination from built-in data)"
    section += "\n--- END STUDENT CONTEXT ---"
    return section


def _docs_to_sources(chunks_with_scores: list[tuple[Chunk, float]]) -> list[SourceDocument]:
    seen = set()
    sources = []
    for chunk, score in chunks_with_scores:
        src = chunk.source
        if src not in seen:
            seen.add(src)
            sources.append(SourceDocument(
                source=src,
                content_preview=chunk.content[:120].strip(),
                score=round(score, 3),
            ))
    return sources


class RAGService:
    def __init__(self):
        self._corpus: list[Chunk] = []
        self._llm_model = None
        self._ready = False
        self._initializing = False

    async def initialize(self):
        if self._ready or self._initializing:
            return
        self._initializing = True
        logger.info("Initialising RAG service...")

        try:
            genai.configure(api_key=settings.google_api_key)

            cache_path = settings.vector_cache_path
            if Path(cache_path).exists():
                self._corpus = load_corpus(cache_path)
            else:
                logger.warning("No vector cache found — building from scratch (this may take 1–2 min)...")
                loop = asyncio.get_event_loop()
                self._corpus = await loop.run_in_executor(
                    None,
                    lambda: build_corpus(
                        cutoff_dir=settings.cutoff_data_dir,
                        faq_dir=settings.faq_data_dir,
                        pdf_dir=settings.pdf_data_dir,
                        api_key=settings.google_api_key,
                        embedding_model=settings.embedding_model,
                        cache_path=cache_path,
                    ),
                )

            # Filter to chunks that have embeddings
            embedded = [c for c in self._corpus if c.embedding]
            logger.info(f"Corpus: {len(self._corpus)} chunks, {len(embedded)} with embeddings.")

            self._llm_model = genai.GenerativeModel(settings.llm_model)
            self._ready = True
            logger.info("RAG service ready.")
        except Exception as e:
            logger.error(f"Failed to initialise RAG service: {e}", exc_info=True)
            self._initializing = False
            raise

    async def rebuild_index(self):
        self._ready = False
        loop = asyncio.get_event_loop()
        self._corpus = await loop.run_in_executor(
            None,
            lambda: build_corpus(
                cutoff_dir=settings.cutoff_data_dir,
                faq_dir=settings.faq_data_dir,
                pdf_dir=settings.pdf_data_dir,
                api_key=settings.google_api_key,
                embedding_model=settings.embedding_model,
                cache_path=settings.vector_cache_path,
            ),
        )
        self._ready = True
        logger.info(f"Index rebuilt — {len(self._corpus)} chunks.")

    def _retrieve(self, query_embedding: list[float], k: int) -> list[tuple[Chunk, float]]:
        """Cosine similarity search over in-memory corpus."""
        scores = []
        for chunk in self._corpus:
            if not chunk.embedding:
                continue
            score = _cosine(query_embedding, chunk.embedding)
            scores.append((chunk, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        # Filter by threshold and return top-k
        return [(c, s) for c, s in scores[:k] if s >= settings.similarity_threshold]

    async def answer(
        self,
        message: str,
        language: str = "en",
        history: list[ChatMessage] = None,
        user_merit: Optional[float] = None,
        user_category: Optional[str] = None,
        student_category: Optional[str] = None,
    ) -> dict:
        if not self._ready:
            return {
                "answer": "AgriBot is still starting up, please try again in a few seconds.",
                "language": language,
                "sources": [],
                "intent": "general",
            }

        history = history or []
        intent = _detect_intent(message)

        # 1. Embed the query
        try:
            embed_result = genai.embed_content(
                model=settings.embedding_model,
                content=message,
                task_type="retrieval_query",
            )
            query_embedding = embed_result["embedding"]
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            query_embedding = None

        # 2. Retrieve relevant chunks
        if query_embedding:
            top_chunks = self._retrieve(query_embedding, k=settings.max_retrieved_docs)
        else:
            # Fallback: use first few FAQ chunks if embedding fails
            top_chunks = [(c, 0.5) for c in self._corpus[:settings.max_retrieved_docs]]

        context = "\n\n---\n\n".join(c.content for c, _ in top_chunks) if top_chunks else "No relevant context found."

        # 3. Build prompt
        user_context_section = _build_user_context_section(user_merit, user_category, student_category)
        chat_history = _format_history(history)
        template = _SYSTEM_GU if language == "gu" else _SYSTEM_EN
        filled_prompt = template.format(
            user_context_section=user_context_section,
            context=context,
            chat_history=chat_history,
            question=message,
        )

        # 4. Generate response
        try:
            response = self._llm_model.generate_content(
                filled_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=settings.llm_temperature,
                    max_output_tokens=1024,
                ),
            )
            answer_text = response.text.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer_text = "Sorry, I encountered an error generating a response. Please try again."

        return {
            "answer": answer_text,
            "language": language,
            "sources": _docs_to_sources(top_chunks),
            "intent": intent,
        }

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def doc_count(self) -> int:
        return len(self._corpus)


rag_service = RAGService()