import pytest
from backend.app.pipeline.stages.quality_stage import QualityStage
from backend.app.pipeline.llm_client import LLMClient
from backend.app.schemas import GeneratedQuestionSchema, ReferenceSolutionSchema, CriticResultSchema

@pytest.fixture
def mock_question():
    return GeneratedQuestionSchema(
        title="Subarray Equilibrium Score",
        story="Find equilibrium score...",
        input_format="T lines...",
        output_format="min diff...",
        constraints="1 <= N <= 10^5",
        sample_inputs=["1\n5\n1 2 3 4 5"],
        sample_outputs=["1"],
        explanation="Sample case explanation",
        tags=["arrays"],
        difficulty="Medium",
        time_limit=2.0,
        memory_limit=256,
        reference_solution=ReferenceSolutionSchema(python="print(1)"),
        brute_force_solution="print(1)",
        test_case_generator_code="print('1')",
        editorial="Prefix sum"
    )

def test_quality_stage_critic_pass(mock_question):
    client = LLMClient()
    client.mock_mode = True
    stage = QualityStage(llm_client=client)

    result: CriticResultSchema = stage.run(question=mock_question, min_score=7.0)
    assert result.overall_score >= 7.0
    assert result.passed is True
    assert result.scores.clarity >= 1.0
    assert result.scores.originality >= 1.0
    assert result.scores.difficulty_match >= 1.0
    assert result.scores.unambiguity >= 1.0

def test_quality_stage_enforces_strict_threshold(mock_question):
    client = LLMClient()
    client.mock_mode = True
    stage = QualityStage(llm_client=client)

    # Set threshold higher than mock's ~8.95
    result: CriticResultSchema = stage.run(question=mock_question, min_score=9.8)
    assert result.passed is False
    assert "Score below threshold" in result.critique
