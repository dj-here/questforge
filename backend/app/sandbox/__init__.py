import os
from backend.app.config import settings
from backend.app.sandbox.runner_interface import RunnerInterface, ExecutionResult
from backend.app.sandbox.docker_runner import DockerRunner
from backend.app.sandbox.subprocess_runner import SubprocessRunner
from backend.app.sandbox.mock_runner import MockRunner

def get_runner(runner_type: str = None) -> RunnerInterface:
    rtype = runner_type or os.environ.get("SANDBOX_TYPE") or settings.SANDBOX_TYPE
    if rtype == "docker":
        return DockerRunner()
    elif rtype == "mock":
        return MockRunner()
    else:
        return SubprocessRunner()
