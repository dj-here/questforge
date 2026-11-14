import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import GenerationJob, Question, JobStatus
from backend.app.schemas import GeneratedQuestionSchema
from backend.app.pipeline.stages.spec_stage import SpecStage
from backend.app.pipeline.stages.generate_stage import GenerateStage
from backend.app.pipeline.stages.test_case_stage import TestCaseStage
from backend.app.pipeline.stages.verification_stage import VerificationStage, VerificationResult
from backend.app.pipeline.stages.quality_stage import QualityStage
from backend.app.pipeline.stages.dedup_stage import DedupStage
from backend.app.pipeline.stages.persist_stage import PersistStage
from backend.app.pipeline.llm_client import LLMClient
from backend.app.sandbox import get_runner
from backend.app.sandbox.runner_interface import RunnerInterface

logger = logging.getLogger(__name__)

class PipelineRunner:
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        runner: Optional[RunnerInterface] = None
    ):
        self.llm = llm_client or LLMClient()
        self.runner = runner or get_runner()
        
        # Instantiate stages
        self.spec_stage = SpecStage()
        self.generate_stage = GenerateStage(llm_client=self.llm)
        self.test_case_stage = TestCaseStage(runner=self.runner)
        self.verification_stage = VerificationStage(runner=self.runner)
        self.quality_stage = QualityStage(llm_client=self.llm)
        self.dedup_stage = DedupStage(llm_client=self.llm)
        self.persist_stage = PersistStage()

    def _update_job_stage(
        self,
        db: Session,
        job: GenerationJob,
        stage_name: str,
        progress: float,
        details: Optional[Dict[str, Any]] = None
    ):
        job.current_stage = stage_name
        job.progress = progress
        history = list(job.stage_history or [])
        history.append({
            "stage": stage_name,
            "progress": progress,
            "details": details or {}
        })
        job.stage_history = history
        db.commit()

    def run_pipeline_for_question(
        self,
        topic: str,
        difficulty: str,
        question_type: str = "coding",
        subtopic: Optional[str] = None,
        languages: Optional[List[str]] = None,
        db: Optional[Session] = None,
        job: Optional[GenerationJob] = None,
        max_attempts: int = 3,
        auto_publish: bool = False
    ) -> Question:
        """Executes the full 7-stage question generation pipeline."""
        attempt = 0
        last_error = ""

        while attempt < max_attempts:
            attempt += 1
            logger.info(f"Pipeline execution attempt {attempt}/{max_attempts} for topic='{topic}', diff='{difficulty}'")

            try:
                # Stage 1: Spec stage
                if job and db:
                    self._update_job_stage(db, job, "spec_stage", 15.0, {"attempt": attempt})
                spec = self.spec_stage.run(
                    topic=topic,
                    difficulty=difficulty,
                    question_type=question_type,
                    subtopic=subtopic,
                    languages=languages,
                    db=db
                )

                # Stage 2: Generate stage
                if job and db:
                    self._update_job_stage(db, job, "generate_stage", 30.0, {"attempt": attempt})
                generated: GeneratedQuestionSchema = self.generate_stage.run(
                    spec=spec,
                    topic=topic,
                    difficulty=difficulty,
                    subtopic=subtopic,
                    languages=languages
                )

                # Stage 3: Test Case stage
                if job and db:
                    self._update_job_stage(db, job, "test_case_stage", 50.0, {"attempt": attempt})
                test_cases = self.test_case_stage.run(question=generated)

                # Stage 4: Verification stage (Differential execution testing)
                if job and db:
                    self._update_job_stage(db, job, "verification_stage", 70.0, {"attempt": attempt})
                verif_res: VerificationResult = self.verification_stage.run(
                    question=generated,
                    test_cases=test_cases,
                    attempt_number=attempt
                )

                if not verif_res.passed:
                    logger.warning(f"Verification failed on attempt {attempt}: {verif_res.error}")
                    last_error = f"Verification failed: {verif_res.error}"
                    continue

                # Stage 5: Quality Critic stage
                if job and db:
                    self._update_job_stage(db, job, "quality_stage", 85.0, {"attempt": attempt})
                critic_res = self.quality_stage.run(question=generated)

                if not critic_res.passed:
                    logger.warning(f"Critic score rejected on attempt {attempt}: {critic_res.critique}")
                    last_error = f"Critic rejected (Score {critic_res.overall_score}): {critic_res.critique}"
                    continue

                # Stage 6: Dedup stage
                if job and db:
                    self._update_job_stage(db, job, "dedup_stage", 92.0, {"attempt": attempt})
                dedup_res = self.dedup_stage.run(question=generated, db=db)

                if dedup_res.is_duplicate:
                    logger.warning(
                        f"Dedup rejected on attempt {attempt}: similarity {dedup_res.max_similarity} "
                        f"with {dedup_res.matched_question_id}"
                    )
                    last_error = f"Dedup rejected: Near duplicate of {dedup_res.matched_question_title}"
                    continue

                # Stage 7: Persist stage
                if job and db:
                    self._update_job_stage(db, job, "persist_stage", 98.0, {"attempt": attempt})
                saved_q = self.persist_stage.run(
                    db=db,
                    job_id=job.id if job else None,
                    topic=topic,
                    difficulty=difficulty,
                    question_type=question_type,
                    generated=generated,
                    test_cases=verif_res.verified_test_cases,
                    verification_logs=verif_res.logs,
                    critic_result=critic_res,
                    embedding=dedup_res.embedding,
                    prompt_snapshot=spec,
                    raw_llm_response=generated.model_dump_json(),
                    auto_approved=auto_publish
                )

                if job and db:
                    self._update_job_stage(db, job, "completed", 100.0, {"question_id": saved_q.id})

                return saved_q

            except Exception as e:
                logger.exception(f"Exception during pipeline attempt {attempt}: {e}")
                last_error = str(e)

        raise RuntimeError(f"Pipeline failed after {max_attempts} attempts. Last error: {last_error}")

    def run_job(self, db: Session, job_id: str):
        """Processes a full generation job (generating `count` questions)."""
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error(f"GenerationJob {job_id} not found")
            return

        job.status = JobStatus.PROCESSING.value
        job.progress = 5.0
        db.commit()

        try:
            questions_created = []
            for i in range(job.count):
                q = self.run_pipeline_for_question(
                    topic=job.topic,
                    difficulty=job.difficulty,
                    question_type=job.question_type,
                    subtopic=job.subtopic,
                    languages=job.languages,
                    db=db,
                    job=job,
                    max_attempts=settings.MAX_REGENERATE_ATTEMPTS,
                    auto_publish=job.auto_publish
                )
                questions_created.append(q)

            job.status = JobStatus.COMPLETED.value
            job.progress = 100.0
            job.current_stage = "finished"
            db.commit()
            return questions_created

        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}")
            job.status = JobStatus.FAILED.value
            job.error_message = str(e)
            db.commit()
            raise
