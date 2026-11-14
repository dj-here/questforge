import pytest
from backend.app.pipeline.stages.verification_stage import VerificationStage, VerificationResult
from backend.app.schemas import GeneratedQuestionSchema, ReferenceSolutionSchema, TestCaseBase
from backend.app.sandbox.mock_runner import MockRunner

@pytest.fixture
def question_and_cases():
    q = GeneratedQuestionSchema(
        title="Sample Problem",
        story="Description...",
        input_format="N...",
        output_format="Result...",
        constraints="1 <= N <= 100",
        sample_inputs=["1 2"],
        sample_outputs=["0"],
        explanation="Exp",
        tags=["math"],
        difficulty="Easy",
        time_limit=2.0,
        memory_limit=256,
        reference_solution=ReferenceSolutionSchema(
            python="import sys\nprint('0')"
        ),
        brute_force_solution="import sys\nprint('0')",
        test_case_generator_code="print('1 2')",
        editorial="Editorial"
    )
    cases = [
        TestCaseBase(input_data="1 2", output_data="0", is_sample=True, is_hidden=False),
        TestCaseBase(input_data="3 4", output_data="", is_sample=False, is_hidden=False),
        TestCaseBase(input_data="5 6", output_data="", is_sample=False, is_hidden=True)
    ]
    return q, cases

def test_verification_stage_success(question_and_cases):
    q, cases = question_and_cases
    runner = MockRunner()
    stage = VerificationStage(runner=runner)

    result: VerificationResult = stage.run(question=q, test_cases=cases)
    assert result.passed is True
    assert len(result.verified_test_cases) == 3
    assert result.verified_test_cases[0].output_data == "0"
    assert len(result.logs) >= 1

def test_verification_stage_fails_on_solution_crash(question_and_cases):
    q, cases = question_and_cases
    runner = MockRunner(should_fail=True)
    stage = VerificationStage(runner=runner)

    result: VerificationResult = stage.run(question=q, test_cases=cases)
    assert result.passed is False
    assert "Reference solution execution failed" in result.error or "Simulated" in result.error

def test_verification_stage_fails_on_timeout(question_and_cases):
    q, cases = question_and_cases
    runner = MockRunner(fail_with_timeout=True)
    stage = VerificationStage(runner=runner)

    result: VerificationResult = stage.run(question=q, test_cases=cases)
    assert result.passed is False
    assert "Time limit exceeded" in result.error
