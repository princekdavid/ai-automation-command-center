from fastapi.testclient import TestClient

from aac.api import app
from aac.execution.artifacts import LocalEvidenceArtifactStore
from aac.execution.contracts import (
    ExecutionMode,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionTarget,
)
from aac.execution.history import SQLiteExecutionHistoryStore


def _seed_execution(store: SQLiteExecutionHistoryStore, request_id: str) -> None:
    request = ExecutionRequest(
        request_id,
        ExecutionMode.SINGLE,
        ExecutionTarget(["pytest:test"], "/tmp/project", "pytest"),
        ExecutionPolicy(),
    )
    store.save(request, ExecutionResult(request_id, ExecutionStatus.PASSED))


def test_execution_artifact_endpoints_list_and_download_scoped_artifacts(tmp_path, monkeypatch):
    history = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    _seed_execution(history, "run-artifacts")
    artifacts = LocalEvidenceArtifactStore(
        tmp_path / "artifacts",
        enabled=True,
        max_artifact_bytes=1024,
        max_total_bytes=4096,
    )
    saved = artifacts.save("run-artifacts", "junit", b"<testsuite/>", "application/xml")
    monkeypatch.setattr("aac.api.history_store", history)
    monkeypatch.setattr("aac.api.artifact_store", artifacts)
    client = TestClient(app)

    listing = client.get("/api/v1/executions/run-artifacts/artifacts")
    assert listing.status_code == 200
    assert listing.json()["count"] == 1
    assert listing.json()["artifacts"][0]["artifact_id"] == saved["artifact_id"]
    assert "storage_key" not in listing.json()["artifacts"][0]

    downloaded = client.get(
        f"/api/v1/executions/run-artifacts/artifacts/{saved['artifact_id']}"
    )
    assert downloaded.status_code == 200
    assert downloaded.content == b"<testsuite/>"
    assert downloaded.headers["content-disposition"] == 'attachment; filename="evidence.bin"'
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    assert downloaded.headers["cache-control"] == "no-store"


def test_execution_artifact_endpoints_do_not_cross_execution_boundary(tmp_path, monkeypatch):
    history = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    _seed_execution(history, "run-one")
    _seed_execution(history, "run-two")
    artifacts = LocalEvidenceArtifactStore(
        tmp_path / "artifacts",
        enabled=True,
        max_artifact_bytes=1024,
        max_total_bytes=4096,
    )
    saved = artifacts.save("run-one", "junit", b"<testsuite/>")
    monkeypatch.setattr("aac.api.history_store", history)
    monkeypatch.setattr("aac.api.artifact_store", artifacts)
    client = TestClient(app)

    response = client.get(
        f"/api/v1/executions/run-two/artifacts/{saved['artifact_id']}"
    )
    assert response.status_code == 404


def test_execution_artifact_endpoints_hide_unknown_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "aac.api.history_store",
        SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3"),
    )
    monkeypatch.setattr(
        "aac.api.artifact_store",
        LocalEvidenceArtifactStore(tmp_path / "artifacts", enabled=True),
    )

    response = TestClient(app).get("/api/v1/executions/missing/artifacts")

    assert response.status_code == 404


def test_status_for_completed_historical_run_includes_artifacts(tmp_path, monkeypatch):
    history = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    request = ExecutionRequest(
        "historic-run", ExecutionMode.SINGLE,
        ExecutionTarget(["pytest:test"], "/tmp/project", "pytest"),
    )
    history.save(request, ExecutionResult(
        "historic-run", ExecutionStatus.PASSED,
        metadata={"artifacts": [{"artifact_id": "report-id", "kind": "junit",
                                 "byte_size": 42, "sha256": "d" * 64,
                                 "created_at": "2026-10-11T10:00:00+00:00",
                                 "media_type": "application/xml"}]},
    ))
    monkeypatch.setattr("aac.api.history_store", history)
    response = TestClient(app).get("/api/v1/executions/historic-run/status")
    assert response.status_code == 200
    assert response.json()["metadata"]["artifacts"][0]["artifact_id"] == "report-id"


def test_download_returns_not_found_when_artifact_file_is_missing(tmp_path, monkeypatch):
    history = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    _seed_execution(history, "run-missing-file")
    artifacts = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=1024,
        max_total_bytes=4096,
    )
    saved = artifacts.save("run-missing-file", "junit", b"<testsuite/>")
    (tmp_path / "artifacts" / f"{saved['artifact_id']}.bin").unlink()
    monkeypatch.setattr("aac.api.history_store", history)
    monkeypatch.setattr("aac.api.artifact_store", artifacts)

    response = TestClient(app).get(
        f"/api/v1/executions/run-missing-file/artifacts/{saved['artifact_id']}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Evidence artifact not found"


def test_download_returns_not_found_after_retention_expiry(tmp_path, monkeypatch):
    history = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    _seed_execution(history, "run-expired")
    artifacts = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=1024,
        max_total_bytes=4096, retention_days=1,
    )
    saved = artifacts.save("run-expired", "junit", b"<testsuite/>")
    with artifacts._connect() as connection:
        connection.execute(
            "UPDATE artifacts SET expired = 1 WHERE artifact_id = ?",
            (saved["artifact_id"],),
        )
    monkeypatch.setattr("aac.api.history_store", history)
    monkeypatch.setattr("aac.api.artifact_store", artifacts)

    response = TestClient(app).get(
        f"/api/v1/executions/run-expired/artifacts/{saved['artifact_id']}"
    )

    assert response.status_code == 404


def test_download_returns_not_found_when_artifact_content_is_tampered(tmp_path, monkeypatch):
    history = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    _seed_execution(history, "run-tampered")
    artifacts = LocalEvidenceArtifactStore(
        tmp_path / "artifacts", enabled=True, max_artifact_bytes=1024,
        max_total_bytes=4096,
    )
    saved = artifacts.save("run-tampered", "junit", b"<testsuite/>")
    (tmp_path / "artifacts" / f"{saved['artifact_id']}.bin").write_bytes(
        b"<testsuite><tampered/></testsuite>"
    )
    monkeypatch.setattr("aac.api.history_store", history)
    monkeypatch.setattr("aac.api.artifact_store", artifacts)

    response = TestClient(app).get(
        f"/api/v1/executions/run-tampered/artifacts/{saved['artifact_id']}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Evidence artifact not found"

