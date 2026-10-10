from pathlib import Path

from aac.discovery.service import DiscoveryService
from aac.discovery.test_service import TestDiscoveryService
from aac.execution.contracts import (
    ExecutionMode,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    ExecutionTarget,
)
from aac.execution.service import ExecutionService


def test_execution_service_requires_explicit_authorization(tmp_path: Path):
    request = ExecutionRequest(
        "req-1",
        ExecutionMode.SINGLE,
        ExecutionTarget(["pytest:missing"], str(tmp_path), "pytest"),
    )

    result = ExecutionService(DiscoveryService()).execute(request)

    assert result.status is ExecutionStatus.REJECTED
    assert "authorization" in (result.error or "").lower()


def test_execution_service_rejects_unsupported_runner(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok(): pass\n")

    request = ExecutionRequest(
        "req-2",
        ExecutionMode.SINGLE,
        ExecutionTarget(["pytest:missing"], str(tmp_path), "unknown"),
        ExecutionPolicy(allow_side_effects=True),
    )

    result = ExecutionService(DiscoveryService()).execute(request)

    assert result.status is ExecutionStatus.REJECTED
