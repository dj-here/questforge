import subprocess
import time
import tempfile
import os
import logging
from backend.app.sandbox.runner_interface import RunnerInterface, ExecutionResult

logger = logging.getLogger(__name__)

class DockerRunner(RunnerInterface):
    """Production Docker sandbox code runner with extreme isolation."""
    def __init__(self, image: str = "python:3.12-slim"):
        self.image = image

    def run_code(
        self,
        code: str,
        language: str = "python",
        stdin_input: str = "",
        timeout_seconds: float = 3.0,
        memory_limit_mb: int = 256
    ) -> ExecutionResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_name = "solution.py"
            if language.lower() == "python":
                file_name = "solution.py"
                cmd = ["python", f"/workspace/{file_name}"]
            elif language.lower() in ("cpp", "c++"):
                file_name = "solution.cpp"
                cmd = ["sh", "-c", f"g++ -O3 /workspace/{file_name} -o /tmp/sol && /tmp/sol"]
            elif language.lower() == "java":
                file_name = "Solution.java"
                cmd = ["sh", "-c", f"javac /workspace/{file_name} -d /tmp && java -cp /tmp Solution"]
            else:
                return ExecutionResult(
                    success=False,
                    exit_code=1,
                    stdout="",
                    stderr=f"Unsupported language: {language}",
                    execution_time_ms=0,
                    error=f"Unsupported language: {language}"
                )

            code_path = os.path.join(tmpdir, file_name)
            with open(code_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Docker isolation command
            docker_cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", f"{memory_limit_mb}m",
                "--cpus", "1.0",
                "--pids-limit", "64",
                "--read-only",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                "-v", f"{tmpdir}:/workspace:ro",
                "-i",
                self.image
            ] + cmd

            start_time = time.perf_counter()
            try:
                proc = subprocess.run(
                    docker_cmd,
                    input=stdin_input,
                    capture_output=True,
                    text=True,
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
                    stdout=e.stdout.decode("utf-8", errors="replace") if e.stdout else "",
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
