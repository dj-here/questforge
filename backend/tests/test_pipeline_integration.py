import pytest
from backend.app.pipeline.runner import PipelineRunner
from backend.app.pipeline.llm_client import LLMClient
from backend.app.sandbox.mock_runner import MockRunner
from backend.app.models import Question, QuestionStatus, TestCase, VerificationLog, AuditTrail

def test_full_pipeline_run_and_persist(db_session):
    llm = LLMClient()
    llm.mock_mode = True
    runner_sandbox = MockRunner()

    pipeline = PipelineRunner(llm_client=llm, runner=runner_sandbox)

    question: Question = pipeline.run_pipeline_for_question(
        topic="Dynamic Programming",
        difficulty="Medium",
        question_type="coding",
        subtopic="Subsequences",
        languages=["python", "java", "cpp"],
        db=db_session,
        max_attempts=2
    )

    assert question is not None
    assert question.id.startswith("q_")
    assert question.status == QuestionStatus.REVIEW_READY.value
    assert question.critic_score is not None
    assert len(question.test_cases) >= 15
    assert len(question.verification_logs) >= 1

    # Verify audit trail
    audits = db_session.query(AuditTrail).filter(AuditTrail.question_id == question.id).all()
    assert len(audits) >= 1
    assert audits[0].action == "question_generated_and_verified"
