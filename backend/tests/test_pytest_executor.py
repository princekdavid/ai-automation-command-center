from aac.execution.contracts import ExecutionPolicy, ExecutionTarget, ExecutionStatus
from aac.execution.pytest_executor import PytestExecutor
from aac.domain.models import DiscoveredTest


def test_executor_rejects_side_effects_by_default(tmp_path):
    test = DiscoveredTest("pytest:1", "test_ok", "tests/test_ok.py", "python", "pytest", "test_ok", metadata={"line": 1, "kind": "function"})
    result = PytestExecutor().execute("r1", ExecutionTarget([test.id], str(tmp_path), "pytest"), ExecutionPolicy(), [test])
    assert result.status is ExecutionStatus.REJECTED


def test_executor_rejects_unknown_test_id(tmp_path):
    result = PytestExecutor().execute("r1", ExecutionTarget(["pytest:missing"], str(tmp_path), "pytest"), ExecutionPolicy(allow_side_effects=True), [])
    assert result.status is ExecutionStatus.REJECTED
