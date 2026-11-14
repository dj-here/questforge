import pytest
from backend.app.pipeline.stages.test_case_stage import TestCaseStage, TestCaseGenerationError
from backend.app.schemas import GeneratedQuestionSchema, ReferenceSolutionSchema
from backend.app.sandbox.mock_runner import MockRunner

@pytest.fixture
def sample_question():
    return GeneratedQuestionSchema(
        title="Subarray Equilibrium Score",
        story="Find equilibrium score...",
        input_format="T lines...",
        output_format="min diff...",
        constraints="1 <= N <= 10^5",
        sample_inputs=["1\n5\n1 2 3 4 5", "1\n4\n2 -1 3 0"],
        sample_outputs=["1", "0"],
        explanation="Sample case explanation",
        tags=["arrays"],
        difficulty="Medium",
        time_limit=2.0,
        memory_limit=256,
        reference_solution=ReferenceSolutionSchema(
            python="import sys\ndef solve(): print('0')\nif __name__=='__main__': solve()"
        ),
        brute_force_solution="import sys\ndef solve(): print('0')\nif __name__=='__main__': solve()",
        test_case_generator_code="print('---TESTCASE---\\n1\\n1\\n1')",
        editorial="Prefix sum solution"
    )

def test_test_case_stage_generates_cases(sample_question):
    runner = MockRunner()
    stage = TestCaseStage(runner=runner)

    test_cases = stage.run(sample_question)

    # Must produce 15-30 test cases
    assert 15 <= len(test_cases) <= 30

    # First cases should be sample cases
    assert test_cases[0].is_sample is True
    assert test_cases[0].is_hidden is False
    assert test_cases[0].score == 0.0

    # Middle cases should be visible boundary cases
    assert test_cases[2].is_sample is False
    assert test_cases[2].is_hidden is False

    # Later cases should be hidden stress cases with positive scores
    assert test_cases[-1].is_hidden is True
    assert test_cases[-1].score > 0.0

def test_test_case_stage_handles_runner_failure(sample_question):
    runner = MockRunner(should_fail=True)
    stage = TestCaseStage(runner=runner)

    with pytest.raises(TestCaseGenerationError):
        stage.run(sample_question)
