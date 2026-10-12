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



def test_history_persists_safe_artifact_references_and_updates_existing_rows(tmp_path) -> None:
    store = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    request = ExecutionRequest(
        request_id="run-with-artifact",
        mode=ExecutionMode.SINGLE,
        target=ExecutionTarget(["test-1"], "/workspace/project", "pytest"),
    )
    result = ExecutionResult(
        request_id="run-with-artifact",
        status=ExecutionStatus.PASSED,
        metadata={
            "artifacts": [{
                "artifact_id": "opaque-artifact-id",
                "kind": "junit",
                "byte_size": 123,
                "sha256": "b" * 64,
                "created_at": "2026-10-11T10:00:00+00:00",
                "media_type": "application/xml",
                "storage_key": "/private/path/results.xml",
                "execution_id": "run-with-artifact",
            }]
        },
    )

    store.save(request, result)
    record = store.get("run-with-artifact")

    assert record is not None
    assert record["artifacts"] == [{
        "artifact_id": "opaque-artifact-id",
        "kind": "junit",
        "byte_size": 123,
        "sha256": "b" * 64,
        "created_at": "2026-10-11T10:00:00+00:00",
        "media_type": "application/xml",
    }]
    assert "/private/path" not in json.dumps(record)
    assert store.list_recent()[0]["artifacts"] == record["artifacts"]

    store.save(request, ExecutionResult("run-with-artifact", ExecutionStatus.FAILED))
    updated = store.get("run-with-artifact")
    assert updated is not None
    assert updated["artifacts"] == []


def test_history_migrates_existing_schema_with_no_artifact_column(tmp_path) -> None:
    import sqlite3

    database = tmp_path / "legacy-history.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """CREATE TABLE execution_history (
                request_id TEXT PRIMARY KEY,
                project_path TEXT NOT NULL,
                runner TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                results_json TEXT NOT NULL
            )"""
        )
        connection.execute(
            """INSERT INTO execution_history
            (request_id, project_path, runner, status, created_at, results_json)
            VALUES ('legacy-run', '/workspace/project', 'pytest', 'passed',
                    '2026-10-10T10:00:00+00:00', '[]')"""
        )

    store = SQLiteExecutionHistoryStore(database)

    record = store.get("legacy-run")

    assert record is not None
    assert record["artifacts"] == []

def test_history_expires_old_records_on_read(tmp_path) -> None:
    from datetime import datetime, timedelta, timezone

    store = SQLiteExecutionHistoryStore(
        tmp_path / "history.sqlite3", retention_days=1, max_records=10,
    )
    for request_id in ("old-run", "new-run"):
        request = ExecutionRequest(
            request_id=request_id,
            mode=ExecutionMode.SINGLE,
            target=ExecutionTarget([], "/workspace/project", "pytest"),
        )
        store.save(request, ExecutionResult(request_id, ExecutionStatus.REJECTED))

    old_timestamp = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    with store._connection() as connection:
        connection.execute(
            "UPDATE execution_history SET created_at = ? WHERE request_id = ?",
            (old_timestamp, "old-run"),
        )

    records = store.list_recent()

    assert [record["request_id"] for record in records] == ["new-run"]
    assert store.get("old-run") is None


def test_history_keeps_only_newest_configured_record_count(tmp_path) -> None:
    store = SQLiteExecutionHistoryStore(
        tmp_path / "history.sqlite3", retention_days=30, max_records=2,
    )
    for request_id in ("run-1", "run-2", "run-3"):
        request = ExecutionRequest(
            request_id=request_id,
            mode=ExecutionMode.SINGLE,
            target=ExecutionTarget([], "/workspace/project", "pytest"),
        )
        store.save(request, ExecutionResult(request_id, ExecutionStatus.REJECTED))

    records = store.list_recent()

    assert len(records) == 2
    assert store.get("run-1") is None
