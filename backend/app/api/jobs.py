import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import GenerationJob, JobStatus, User
from backend.app.schemas import GenerationJobCreate, GenerationJobResponse
from backend.app.auth import require_reviewer
from backend.app.pipeline.runner import PipelineRunner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generation-jobs", tags=["generation-jobs"])

def run_job_background(job_id: str):
    from backend.app.database import SessionLocal
    db = SessionLocal()
    try:
        runner = PipelineRunner()
        runner.run_job(db=db, job_id=job_id)
    except Exception as e:
        logger.exception(f"Background job execution failed for {job_id}: {e}")
    finally:
        db.close()

@router.post("", response_model=GenerationJobResponse, status_code=201)
def create_generation_job(
    job_in: GenerationJobCreate,
    background_tasks: BackgroundTasks,
    sync: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = GenerationJob(
        id=job_id,
        topic=job_in.topic,
        subtopic=job_in.subtopic,
        difficulty=job_in.difficulty,
        question_type=job_in.question_type,
        languages=job_in.languages,
        count=job_in.count,
        auto_publish=job_in.auto_publish,
        status=JobStatus.PENDING.value,
        progress=0.0,
        current_stage="queued",
        stage_history=[]
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if sync:
        # Run synchronously (useful for integration tests and CLI scripting)
        runner = PipelineRunner()
        runner.run_job(db=db, job_id=job.id)
        db.refresh(job)
    else:
        # Check Celery dispatch or fallback to FastAPI background tasks (skip heavy background exec during unit tests)
        import os
        is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("SERVERLESS") == "true"
        if is_serverless and os.environ.get("TESTING") != "True":
            # In Vercel serverless without Celery daemon, run synchronously so generation completes before Lambda freeze
            runner = PipelineRunner()
            runner.run_job(db=db, job_id=job.id)
            db.refresh(job)
        elif os.environ.get("TESTING") != "True":
            try:
                from backend.app.workers.tasks import generate_questions_task
                generate_questions_task.delay(job_id=job.id)
            except Exception:
                # Fallback to local background tasks if Celery/Redis is unreachable
                background_tasks.add_task(run_job_background, job.id)

    return job

@router.get("", response_model=List[GenerationJobResponse])
def list_generation_jobs(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    jobs = db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).offset(offset).limit(limit).all()
    return jobs

@router.get("/{id}", response_model=GenerationJobResponse)
def get_generation_job(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer)
):
    job = db.query(GenerationJob).filter(GenerationJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return job
