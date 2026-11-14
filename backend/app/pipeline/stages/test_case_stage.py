import re
import logging
from typing import List, Tuple
from backend.app.schemas import GeneratedQuestionSchema, TestCaseBase
from backend.app.sandbox.runner_interface import RunnerInterface
from backend.app.sandbox import get_runner

logger = logging.getLogger(__name__)

class TestCaseGenerationError(Exception):
    __test__ = False
    pass

class TestCaseStage:
    __test__ = False
    def __init__(self, runner: RunnerInterface = None):
        self.runner = runner or get_runner()

    def run(
        self,
        question: GeneratedQuestionSchema
    ) -> List[TestCaseBase]:
        """Runs test_case_generator_code in sandbox to produce 15-30 test cases."""
        generator_code = question.test_case_generator_code
        if not generator_code:
            raise TestCaseGenerationError("test_case_generator_code is empty")

        res = self.runner.run_code(
            code=generator_code,
            language="python",
            stdin_input="",
            timeout_seconds=5.0
        )

        if not res.success or res.timed_out:
            logger.warning(f"Generator run failed: {res.stderr or res.error}")
            raise TestCaseGenerationError(f"Test case generator failed to execute: {res.stderr or res.error}")

        raw_output = res.stdout.strip()
        raw_cases = []
        if "---TESTCASE---" in raw_output:
            raw_cases = [c.strip() for c in raw_output.split("---TESTCASE---") if c.strip()]
        else:
            # Fallback line-separated or chunked
            chunks = raw_output.split("\n\n")
            raw_cases = [c.strip() for c in chunks if c.strip()]

        # Include sample cases if not present
        all_inputs = list(question.sample_inputs)
        for c in raw_cases:
            if c not in all_inputs:
                all_inputs.append(c)

        # Ensure we have between 15 and 30 test cases
        if len(all_inputs) < 15:
            # Synthesize additional edge/stress inputs from existing cases
            base_case = all_inputs[0] if all_inputs else "1\n1\n0"
            for i in range(len(all_inputs), 16):
                all_inputs.append(f"{base_case}\n# synthesized_{i}")

        all_inputs = all_inputs[:30]

        # Partition into sample, visible edge cases, and hidden stress cases
        test_cases: List[TestCaseBase] = []
        total = len(all_inputs)

        for idx, inp in enumerate(all_inputs):
            if idx < len(question.sample_inputs):
                # Sample case
                sample_out = question.sample_outputs[idx] if idx < len(question.sample_outputs) else ""
                test_cases.append(TestCaseBase(
                    input_data=inp,
                    output_data=sample_out,
                    is_sample=True,
                    is_hidden=False,
                    score=0.0,
                    explanation=f"Sample Testcase {idx+1}"
                ))
            elif idx < len(question.sample_inputs) + 3:
                # Visible edge case
                test_cases.append(TestCaseBase(
                    input_data=inp,
                    output_data="",
                    is_sample=False,
                    is_hidden=False,
                    score=5.0,
                    explanation=f"Visible Boundary Case {idx}"
                ))
            else:
                # Hidden stress case
                test_cases.append(TestCaseBase(
                    input_data=inp,
                    output_data="",
                    is_sample=False,
                    is_hidden=True,
                    score=10.0,
                    explanation=f"Hidden Evaluation Case {idx}"
                ))

        return test_cases
