import uuid
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models import Question, TestCase, VerificationLog, AuditTrail, QuestionStatus
from backend.app.schemas import GeneratedQuestionSchema, TestCaseBase, CriticResultSchema
from backend.app.pipeline.stages.verification_stage import StageVerificationLog

class PersistStage:
    def run(
        self,
        db: Session,
        job_id: Optional[str],
        topic: str,
        difficulty: str,
        question_type: str,
        generated: GeneratedQuestionSchema,
        test_cases: List[TestCaseBase],
        verification_logs: List[StageVerificationLog],
        critic_result: CriticResultSchema,
        embedding: List[float],
        prompt_snapshot: str = "",
        raw_llm_response: str = "",
        actor: str = "pipeline",
        auto_approved: bool = False
    ) -> Question:
        question_id = f"q_{uuid.uuid4().hex[:12]}"
        
        status = QuestionStatus.REVIEW_READY.value
        if auto_approved:
            status = QuestionStatus.APPROVED.value

        ref_solution_dict = {
            "python": generated.reference_solution.python,
            "java": generated.reference_solution.java or "",
            "cpp": generated.reference_solution.cpp or ""
        }

        question = Question(
            id=question_id,
            job_id=job_id,
            title=generated.title,
            topic=topic,
            subtopic=generated.tags[0] if generated.tags else None,
            difficulty=difficulty,
            question_type=question_type,
            story=generated.story,
            input_format=generated.input_format,
            output_format=generated.output_format,
            constraints=generated.constraints,
            sample_inputs=generated.sample_inputs,
            sample_outputs=generated.sample_outputs,
            explanation=generated.explanation,
            tags=generated.tags,
            time_limit=generated.time_limit,
            memory_limit=generated.memory_limit,
            reference_solution=ref_solution_dict,
            brute_force_solution=generated.brute_force_solution,
            test_case_generator_code=generated.test_case_generator_code,
            editorial=generated.editorial,
            status=status,
            critic_score=critic_result.overall_score,
            critic_feedback=critic_result.model_dump(),
            embedding=embedding
        )
        db.add(question)
        db.flush()

        # Add Test Cases
        for tc in test_cases:
            tc_model = TestCase(
                question_id=question_id,
                input_data=tc.input_data,
                output_data=tc.output_data,
                is_sample=tc.is_sample,
                is_hidden=tc.is_hidden,
                score=tc.score,
                explanation=tc.explanation
            )
            db.add(tc_model)

        # Add Verification Logs
        for vlog in verification_logs:
            v_model = VerificationLog(
                question_id=question_id,
                attempt_number=vlog.attempt_number,
                stage=vlog.stage,
                passed=vlog.passed,
                stdout=vlog.stdout,
                stderr=vlog.stderr,
                execution_time_ms=vlog.execution_time_ms,
                memory_used_kb=vlog.memory_used_kb,
                error_message=vlog.error_message
            )
            db.add(v_model)

        # Add Audit Trail
        audit = AuditTrail(
            question_id=question_id,
            action="question_generated_and_verified",
            actor=actor,
            prompt_snapshot=prompt_snapshot,
            raw_llm_response=raw_llm_response,
            metadata_json={
                "critic_score": critic_result.overall_score,
                "critic_passed": critic_result.passed,
                "test_case_count": len(test_cases),
                "auto_approved": auto_approved
            }
        )
        db.add(audit)

        db.commit()
        db.refresh(question)
        return question
