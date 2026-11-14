import pytest
from backend.app.sandbox.subprocess_runner import SubprocessRunner
from backend.app.sandbox.mock_runner import MockRunner
from backend.app.sandbox.runner_interface import ExecutionResult

def test_subprocess_runner_python_execution():
    runner = SubprocessRunner()
    code = "import sys\nname = sys.stdin.read().strip()\nprint(f'Hello {name}')"
    res: ExecutionResult = runner.run_code(
        code=code,
        language="python",
        stdin_input="QuestForge",
        timeout_seconds=2.0
    )
    assert res.success is True
    assert res.exit_code == 0
    assert "Hello QuestForge" in res.stdout
    assert res.timed_out is False

def test_subprocess_runner_timeout():
    runner = SubprocessRunner()
    code = "import time\ntime.sleep(5)\nprint('Done')"
    res: ExecutionResult = runner.run_code(
        code=code,
        language="python",
        stdin_input="",
        timeout_seconds=0.5
    )
    assert res.success is False
    assert res.timed_out is True
    assert "Time limit exceeded" in res.error

def test_subprocess_runner_runtime_error():
    runner = SubprocessRunner()
    code = "x = 1 / 0"
    res: ExecutionResult = runner.run_code(
        code=code,
        language="python",
        stdin_input="",
        timeout_seconds=2.0
    )
    assert res.success is False
    assert res.exit_code != 0
    assert "ZeroDivisionError" in res.stderr

def test_mock_runner():
    runner = MockRunner()
    res = runner.run_code("print('test')", "python", "input")
    assert res.success is True
