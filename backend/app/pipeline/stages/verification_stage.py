import logging
import time
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel
from backend.app.schemas import GeneratedQuestionSchema, TestCaseBase
from backend.app.sandbox.runner_interface import RunnerInterface
from backend.app.sandbox import get_runner

logger = logging.getLogger(__name__)

class StageVerificationLog(BaseModel):
    attempt_number: int
    stage: str
    passed: bool
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0
    memory_used_kb: float = 0.0
    error_message: str = ""

class VerificationResult(BaseModel):
    passed: bool
    verified_test_cases: List[TestCaseBase] = []
    logs: List[StageVerificationLog] = []
    error: str = ""

def normalize_output(s: str) -> str:
    """Normalize outputs by trimming trailing whitespace and line endings."""
    lines = [line.rstrip() for line in s.strip().splitlines()]
    return "\n".join(lines)

class VerificationStage:
    def __init__(self, runner: RunnerInterface = None):
        self.runner = runner or get_runner()

    def run(
        self,
        question: GeneratedQuestionSchema,
        test_cases: List[TestCaseBase],
        attempt_number: int = 1
    ) -> VerificationResult:
        logs: List[StageVerificationLog] = []
        verified_cases: List[TestCaseBase] = []
        ref_python = question.reference_solution.python
        brute_code = question.brute_force_solution

        # Step 1: Run reference solution on all test cases
        for idx, tc in enumerate(test_cases):
            res = self.runner.run_code(
                code=ref_python,
                language="python",
                stdin_input=tc.input_data,
                timeout_seconds=question.time_limit
            )

            if not res.success or res.timed_out:
                err_msg = res.error or res.stderr or "Reference solution execution failed."
                log = StageVerificationLog(
                    attempt_number=attempt_number,
                    stage="reference_solution",
                    passed=False,
                    stdout=res.stdout,
                    stderr=res.stderr,
                    execution_time_ms=res.execution_time_ms,
                    error_message=f"Failed on testcase {idx+1}: {err_msg}"
                )
                logs.append(log)
                return VerificationResult(
                    passed=False,
                    verified_test_cases=[],
                    logs=logs,
                    error=log.error_message
                )

            produced_output = normalize_output(res.stdout)
            
            # If sample case with expected output, compare
            if tc.is_sample and tc.output_data:
                expected_out = normalize_output(tc.output_data)
                if produced_output != expected_out:
                    log = StageVerificationLog(
                        attempt_number=attempt_number,
                        stage="reference_solution",
                        passed=False,
                        stdout=res.stdout,
                        stderr=f"Mismatch on sample {idx+1}. Expected: '{expected_out}', Got: '{produced_output}'",
                        execution_time_ms=res.execution_time_ms,
                        error_message="Reference output does not match sample output."
                    )
                    logs.append(log)
                    return VerificationResult(
                        passed=False,
                        verified_test_cases=[],
                        logs=logs,
                        error=log.error_message
                    )

            # Assign verified output to test case
            updated_tc = tc.model_copy(update={"output_data": produced_output})
            verified_cases.append(updated_tc)

            # Record sample log entry for first case
            if idx == 0:
                logs.append(StageVerificationLog(
                    attempt_number=attempt_number,
                    stage="reference_solution",
                    passed=True,
                    stdout=res.stdout[:200],
                    stderr="",
                    execution_time_ms=res.execution_time_ms,
                    error_message=""
                ))

        # Step 2: Run brute-force on small/sample test cases (first 5)
        small_cases_count = min(5, len(verified_cases))
        if brute_code:
            for idx in range(small_cases_count):
                tc = verified_cases[idx]
                res_brute = self.runner.run_code(
                    code=brute_code,
                    language="python",
                    stdin_input=tc.input_data,
                    timeout_seconds=question.time_limit * 2.0
                )

                if not res_brute.success or res_brute.timed_out:
                    # Brute force failure or timeout
                    log = StageVerificationLog(
                        attempt_number=attempt_number,
                        stage="brute_force",
                        passed=False,
                        stdout=res_brute.stdout,
                        stderr=res_brute.stderr,
                        execution_time_ms=res_brute.execution_time_ms,
                        error_message=f"Brute force failed on test case {idx+1}: {res_brute.error or res_brute.stderr}"
                    )
                    logs.append(log)
                    return VerificationResult(
                        passed=False,
                        verified_test_cases=[],
                        logs=logs,
                        error=log.error_message
                    )

                brute_out = normalize_output(res_brute.stdout)
                ref_out = normalize_output(tc.output_data)
                if brute_out != ref_out:
                    log = StageVerificationLog(
                        attempt_number=attempt_number,
                        stage="brute_force",
                        passed=False,
                        stdout=res_brute.stdout,
                        stderr=f"Differential testing mismatch on case {idx+1}.\nRef: {ref_out}\nBrute: {brute_out}",
                        execution_time_ms=res_brute.execution_time_ms,
                        error_message="Differential testing mismatch between reference and brute-force solution."
                    )
                    logs.append(log)
                    return VerificationResult(
                        passed=False,
                        verified_test_cases=[],
                        logs=logs,
                        error=log.error_message
                    )

            logs.append(StageVerificationLog(
                attempt_number=attempt_number,
                stage="brute_force",
                passed=True,
                stdout="All small cases verified against brute-force.",
                stderr="",
                execution_time_ms=50.0,
                error_message=""
            ))

        return VerificationResult(
            passed=True,
            verified_test_cases=verified_cases,
            logs=logs,
            error=""
        )
