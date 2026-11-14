from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database import get_db
from backend.app.models import Question, GenerationJob, QuestionStatus
from backend.app.config import settings

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "sandbox_type": settings.SANDBOX_TYPE,
        "hackerrank_dry_run": settings.HACKERRANK_DRY_RUN
    }

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    total_questions = db.query(Question).count()
    published_questions = db.query(Question).filter(Question.status == QuestionStatus.PUBLISHED.value).count()
    approved_questions = db.query(Question).filter(Question.status == QuestionStatus.APPROVED.value).count()
    review_ready_questions = db.query(Question).filter(Question.status == QuestionStatus.REVIEW_READY.value).count()
    rejected_questions = db.query(Question).filter(Question.status == QuestionStatus.REJECTED.value).count()
    total_jobs = db.query(GenerationJob).count()

    return {
        "questions_total": total_questions,
        "questions_published": published_questions,
        "questions_approved": approved_questions,
        "questions_review_ready": review_ready_questions,
        "questions_rejected": rejected_questions,
        "generation_jobs_total": total_jobs
    }
