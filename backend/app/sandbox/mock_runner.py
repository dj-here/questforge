from backend.app.sandbox.runner_interface import RunnerInterface, ExecutionResult

class MockRunner(RunnerInterface):
    """Deterministic mock runner for unit tests."""
    def __init__(self, should_fail: bool = False, fail_stage: str = "", fail_with_timeout: bool = False):
        self.should_fail = should_fail
        self.fail_stage = fail_stage
        self.fail_with_timeout = fail_with_timeout

    def run_code(
        self,
        code: str,
        language: str = "python",
        stdin_input: str = "",
        timeout_seconds: float = 3.0,
        memory_limit_mb: int = 256
    ) -> ExecutionResult:
        if self.fail_with_timeout:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Timeout",
                execution_time_ms=timeout_seconds * 1000 + 50,
                timed_out=True,
                error="Time limit exceeded."
            )
        if self.should_fail:
            return ExecutionResult(
                success=False,
                exit_code=1,
                stdout="",
                stderr="Simulated runtime error or assertion failure",
                execution_time_ms=15.0,
                error="Simulated failure"
            )
        
        # Generator code simulation: if code contains ---TESTCASE---, output formatted test cases
        if "---TESTCASE---" in code or "generate" in code:
            mock_output = (
                "---TESTCASE---\n1\n5\n1 2 3 4 5\n"
                "---TESTCASE---\n1\n4\n2 -1 3 0\n"
                "---TESTCASE---\n1\n1\n42\n"
                "---TESTCASE---\n1\n2\n0 0\n"
                "---TESTCASE---\n1\n3\n-1000 0 1000\n"
            )
            for i in range(15):
                mock_output += f"---TESTCASE---\n1\n3\n{i} {i*2} {i*3}\n"
            return ExecutionResult(
                success=True,
                exit_code=0,
                stdout=mock_output,
                stderr="",
                execution_time_ms=45.0
            )

        # Reference / brute force simulation
        if "1 2 3 4 5" in stdin_input:
            return ExecutionResult(
                success=True,
                exit_code=0,
                stdout="1\n",
                stderr="",
                execution_time_ms=25.0
            )

        return ExecutionResult(
            success=True,
            exit_code=0,
            stdout="0\n",
            stderr="",
            execution_time_ms=25.0
        )
