import math
import logging
from typing import List, Optional, Tuple
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.models import Question
from backend.app.schemas import GeneratedQuestionSchema
from backend.app.pipeline.llm_client import LLMClient
from backend.app.config import settings

logger = logging.getLogger(__name__)

class DedupResult(BaseModel):
    is_duplicate: bool
    max_similarity: float
    matched_question_id: Optional[str] = None
    matched_question_title: Optional[str] = None
    embedding: List[float] = []

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class DedupStage:
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()

    def run(
        self,
        question: GeneratedQuestionSchema,
        db: Session,
        threshold: float = None
    ) -> DedupResult:
        sim_threshold = threshold or settings.DEDUP_SIMILARITY_THRESHOLD
        combined_text = f"{question.title}\n{question.story}\n{question.input_format}\n{question.constraints}"
        embedding = self.llm.get_embedding(combined_text)

        # Query existing questions with embeddings
        existing_questions = db.query(Question).filter(Question.embedding.isnot(None)).all()

        max_sim = 0.0
        best_match_id = None
        best_match_title = None

        for eq in existing_questions:
            if not eq.embedding:
                continue
            sim = cosine_similarity(embedding, eq.embedding)
            if sim > max_sim:
                max_sim = sim
                best_match_id = eq.id
                best_match_title = eq.title

        is_dup = max_sim >= sim_threshold
        if is_dup:
            logger.warning(
                f"Near-duplicate question detected! Similarity {max_sim:.3f} >= {sim_threshold:.3f} "
                f"matches Question {best_match_id}: '{best_match_title}'"
            )

        return DedupResult(
            is_duplicate=is_dup,
            max_similarity=round(max_sim, 4),
            matched_question_id=best_match_id,
            matched_question_title=best_match_title,
            embedding=embedding
        )
