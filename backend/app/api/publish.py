from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.database import get_db
from backend.app.models import Question, QuestionStatus, AuditTrail, User
from backend.app.schemas import PublishRequest, BulkPublishRequest, PublishResponse, PublishResultItem
from backend.app.auth import require_reviewer
from backend.app.integrations.hackerrank import HackerRankClient, HackerRankAPIError

router = APIRouter(tags=["publish"])

@router.post("/questions/{id}/publish", response_model=PublishResultItem)
def publish_question(
    id: str,
    req: PublishRequest = PublishRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    question = db.query(Question).filter(Question.id == id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if question.status not in (QuestionStatus.APPROVED.value, QuestionStatus.REVIEW_READY.value):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish question in '{question.status}' state. Must be approved or review_ready."
        )

    client = HackerRankClient(dry_run=req.dry_run)
    try:
        res = client.create_question(
            question=question,
            test_cases=question.test_cases,
            test_id=req.test_id
        )

        remote_id = str(res.get("id"))
        url = res.get("url")

        question.remote_hackerrank_id = remote_id
        question.hackerrank_url = url
        question.status = QuestionStatus.PUBLISHED.value
        question.published_at = datetime.now(timezone.utc)

        audit = AuditTrail(
            question_id=question.id,
            action="published_to_hackerrank",
            actor=current_user.email,
            metadata_json={
                "remote_id": remote_id,
                "url": url,
                "dry_run": req.dry_run
            }
        )
        db.add(audit)
        db.commit()
        db.refresh(question)

        return PublishResultItem(
            question_id=question.id,
            success=True,
            remote_id=remote_id,
            url=url,
            error=None
        )
    except HackerRankAPIError as e:
        db.rollback()
        return PublishResultItem(
            question_id=question.id,
            success=False,
            remote_id=None,
            url=None,
            error=str(e)
        )

@router.post("/publish/bulk", response_model=PublishResponse)
def bulk_publish(
    req: BulkPublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    results: List[PublishResultItem] = []
    published_count = 0
    failed_count = 0

    client = HackerRankClient(dry_run=req.dry_run)

    for qid in req.question_ids:
        question = db.query(Question).filter(Question.id == qid).first()
        if not question:
            results.append(PublishResultItem(
                question_id=qid,
                success=False,
                error="Question not found"
            ))
            failed_count += 1
            continue

        try:
            res = client.create_question(
                question=question,
                test_cases=question.test_cases,
                test_id=req.test_id
            )
            remote_id = str(res.get("id"))
            url = res.get("url")

            question.remote_hackerrank_id = remote_id
            question.hackerrank_url = url
            question.status = QuestionStatus.PUBLISHED.value
            question.published_at = datetime.now(timezone.utc)

            audit = AuditTrail(
                question_id=question.id,
                action="bulk_published_to_hackerrank",
                actor=current_user.email,
                metadata_json={"remote_id": remote_id, "url": url}
            )
            db.add(audit)
            db.commit()

            results.append(PublishResultItem(
                question_id=qid,
                success=True,
                remote_id=remote_id,
                url=url
            ))
            published_count += 1
        except Exception as e:
            db.rollback()
            results.append(PublishResultItem(
                question_id=qid,
                success=False,
                error=str(e)
            ))
            failed_count += 1

    return PublishResponse(
        results=results,
        total=len(req.question_ids),
        published=published_count,
        failed=failed_count
    )
