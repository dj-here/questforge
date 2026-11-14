import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.database import get_db
from backend.app.models import Question, QuestionStatus, TestCase, AuditTrail, User
from backend.app.schemas import QuestionResponse, QuestionUpdate
from backend.app.auth import require_reviewer
from backend.app.integrations.hackerrank.exporter import ChallengePackageExporter
from backend.app.pipeline.runner import PipelineRunner
from backend.app.config import settings

router = APIRouter(prefix="/questions", tags=["questions"])

@router.get("", response_model=List[QuestionResponse])
def list_questions(
    topic: Optional[str] = Query(None, description="Filter by topic"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    status: Optional[str] = Query(None, description="Filter by status (draft, review_ready, approved, rejected, published)"),
    search: Optional[str] = Query(None, description="Search in title or description"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    query = db.query(Question)
    if topic:
        query = query.filter(Question.topic.ilike(f"%{topic}%"))
    if difficulty:
        query = query.filter(Question.difficulty.ilike(difficulty))
    if status:
        query = query.filter(Question.status == status)
    if search:
        query = query.filter(Question.title.ilike(f"%{search}%") | Question.story.ilike(f"%{search}%"))

    questions = query.order_by(Question.created_at.desc()).offset(offset).limit(limit).all()
    return questions

@router.get("/{id}", response_model=QuestionResponse)
def get_question(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    question = db.query(Question).filter(Question.id == id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.patch("/{id}", response_model=QuestionResponse)
def update_question(
    id: str,
    update_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    question = db.query(Question).filter(Question.id == id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    data = update_data.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(question, field, value)

    # Log audit entry
    audit = AuditTrail(
        question_id=question.id,
        action="question_manually_edited",
        actor=current_user.email,
        metadata_json={"modified_fields": list(data.keys())}
    )
    db.add(audit)
    db.commit()
    db.refresh(question)
    return question

@router.post("/{id}/approve", response_model=QuestionResponse)
def approve_question(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    question = db.query(Question).filter(Question.id == id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.status = QuestionStatus.APPROVED.value
    audit = AuditTrail(
        question_id=question.id,
        action="question_approved",
        actor=current_user.email
    )
    db.add(audit)
    db.commit()
    db.refresh(question)
    return question

@router.post("/{id}/reject", response_model=QuestionResponse)
def reject_question(
    id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    question = db.query(Question).filter(Question.id == id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.status = QuestionStatus.REJECTED.value
    audit = AuditTrail(
        question_id=question.id,
        action="question_rejected",
        actor=current_user.email,
        metadata_json={"reason": reason or "Rejected during human review queue"}
    )
    db.add(audit)
    db.commit()
    db.refresh(question)
    return question

@router.post("/{id}/regenerate", response_model=QuestionResponse)
def regenerate_question(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    old_q = db.query(Question).filter(Question.id == id).first()
    if not old_q:
        raise HTTPException(status_code=404, detail="Question not found")

    # Run pipeline to generate a fresh replacement question with same parameters
    runner = PipelineRunner()
    new_q = runner.run_pipeline_for_question(
        topic=old_q.topic,
        difficulty=old_q.difficulty,
        question_type=old_q.question_type,
        subtopic=old_q.subtopic,
        languages=list(old_q.reference_solution.keys()) if isinstance(old_q.reference_solution, dict) else ["python"],
        db=db,
        max_attempts=settings.MAX_REGENERATE_ATTEMPTS
    )

    old_q.status = QuestionStatus.REJECTED.value
    audit = AuditTrail(
        question_id=old_q.id,
        action="question_regenerated",
        actor=current_user.email,
        metadata_json={"replaced_by": new_q.id}
    )
    db.add(audit)
    db.commit()
    db.refresh(new_q)
    return new_q

@router.get("/{id}/export")
def export_question_package(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    question = db.query(Question).filter(Question.id == id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    zip_bytes = ChallengePackageExporter.export_zip(question, question.test_cases)
    filename = f"hackerrank_challenge_{question.id}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
