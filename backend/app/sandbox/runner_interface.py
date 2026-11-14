from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional

class ExecutionResult(BaseModel):
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    memory_used_kb: Optional[float] = None
    timed_out: bool = False
    error: Optional[str] = None

class RunnerInterface(ABC):
    @abstractmethod
    def run_code(
        self,
        code: str,
        language: str = "python",
        stdin_input: str = "",
        timeout_seconds: float = 3.0,
        memory_limit_mb: int = 256
    ) -> ExecutionResult:
        """Run code inside the isolated environment and return execution results."""
        pass
