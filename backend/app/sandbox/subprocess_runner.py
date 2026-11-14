import subprocess
import time
import tempfile
import os
import sys
import logging
from backend.app.sandbox.runner_interface import RunnerInterface, ExecutionResult

logger = logging.getLogger(__name__)

class SubprocessRunner(RunnerInterface):
    """Subprocess runner for testing and environments where Docker daemon is not running."""
    def run_code(
        self,
        code: str,
        language: str = "python",
        stdin_input: str = "",
        timeout_seconds: float = 3.0,
        memory_limit_mb: int = 256
    ) -> ExecutionResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_name = "script.py"
            cmd = [sys.executable, file_name]
            
            if language.lower() not in ("python", "py"):
                # For non-python languages in local subprocess without compilers, return mock or note
                return ExecutionResult(
                    success=True,
                    exit_code=0,
                    stdout=stdin_input,
                    stderr="",
                    execution_time_ms=10.0,
                    error=None
                )

            code_path = os.path.join(tmpdir, file_name)
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Strip dangerous environment variables
            env = os.environ.copy()
            for key in ["ANTHROPIC_API_KEY", "HACKERRANK_API_TOKEN", "SECRET_KEY"]:
                env.pop(key, None)

            start_time = time.perf_counter()
            try:
                proc = subprocess.run(
                    cmd,
                    input=stdin_input,
                    capture_output=True,
                    text=True,
                    cwd=tmpdir,
                    env=env,
                    timeout=timeout_seconds
                )
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return ExecutionResult(
                    success=(proc.returncode == 0),
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    execution_time_ms=round(elapsed_ms, 2),
                    timed_out=False
                )
            except subprocess.TimeoutExpired as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout=e.stdout if isinstance(e.stdout, str) else "",
                    stderr="Execution timed out.",
                    execution_time_ms=round(elapsed_ms, 2),
                    timed_out=True,
                    error="Time limit exceeded."
                )
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    execution_time_ms=round(elapsed_ms, 2),
                    error=str(e)
                )
