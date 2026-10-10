import json

from aac.execution.contracts import (
    ExecutionMode,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionTarget,
    EvidenceReference,
    TestOutcome,
    TestResult,
)
from aac.execution.history import SQLiteExecutionHistoryStore


def test_history_persists_normalized_summary_without_raw_failure_message(tmp_path) -> None:
    store = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    request = ExecutionRequest(
        request_id="run-1",
        mode=ExecutionMode.SINGLE,
        target=ExecutionTarget(["test-1"], "/workspace/project", "pytest"),
    )
    result = ExecutionResult(
        request_id="run-1",
        status=ExecutionStatus.FAILED,
        results=[
            TestResult(
                test_id="test-1",
                outcome=TestOutcome.FAILED,
                duration_seconds=0.25,
                message="AssertionError: password=super-secret-value",
                evidence=[EvidenceReference("junit", "/tmp/results.xml", "JUnit report")],
            )
        ],
        started_at="2026-10-11T10:00:00+00:00",
        completed_at="2026-10-11T10:00:01+00:00",
        error="raw stderr should not be persisted",
    )

    store.save(request, result)
    record = store.get("run-1")

    assert record is not None
    assert record["status"] == "failed"
    assert record["results"][0]["outcome"] == "failed"
    assert record["results"][0]["failure_category"] == "assertion_failure"
    assert record["results"][0]["evidence_count"] == 1
    serialized = json.dumps(record)
    assert "super-secret-value" not in serialized
    assert "raw stderr" not in serialized
    assert "message" not in record["results"][0]


def test_history_lists_recent_runs_with_limit(tmp_path) -> None:
    store = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    for request_id in ("run-1", "run-2"):
        request = ExecutionRequest(
            request_id=request_id,
            mode=ExecutionMode.SINGLE,
            target=ExecutionTarget([], "/workspace/project", "pytest"),
        )
        result = ExecutionResult(request_id, ExecutionStatus.REJECTED)
        store.save(request, result)

    records = store.list_recent(limit=1)

    assert len(records) == 1
    assert records[0]["request_id"] in {"run-1", "run-2"}
