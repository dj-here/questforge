import logging
from backend.app.workers.celery_app import celery_app
from backend.app.database import SessionLocal
from backend.app.pipeline.runner import PipelineRunner
from backend.app.models import Question, QuestionStatus
from backend.app.integrations.hackerrank import HackerRankClient
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.generate_questions")
def generate_questions_task(self, job_id: str):
    logger.info(f"Starting async question generation task for job_id={job_id}")
    db = SessionLocal()
    try:
        runner = PipelineRunner()
        runner.run_job(db=db, job_id=job_id)
        logger.info(f"Successfully completed job_id={job_id}")
    except Exception as e:
        logger.exception(f"Error in generate_questions_task for job_id={job_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task(bind=True, name="tasks.publish_question")
def publish_question_task(self, question_id: str, test_id: str = None, dry_run: bool = None):
    logger.info(f"Publishing question {question_id} to HackerRank")
    db = SessionLocal()
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise ValueError(f"Question {question_id} not found")

        client = HackerRankClient(dry_run=dry_run)
        res = client.create_question(question=question, test_cases=question.test_cases, test_id=test_id)

        question.remote_hackerrank_id = str(res.get("id"))
        question.hackerrank_url = res.get("url")
        question.status = QuestionStatus.PUBLISHED.value
        question.published_at = datetime.now(timezone.utc)
        db.commit()
        return res
    finally:
        db.close()
