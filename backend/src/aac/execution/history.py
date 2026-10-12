"""Local SQLite history for normalized execution summaries.

Raw stdout/stderr and raw per-test failure messages are intentionally not persisted.
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from aac.analysis.failure_classifier import classify_failure
from aac.execution.contracts import ExecutionRequest, ExecutionResult


class SQLiteExecutionHistoryStore:
    """Persist compact, local-only execution summaries without raw logs."""

    def __init__(
        self,
        database_path: str | Path | None = None,
        *,
        retention_days: int | None = None,
        max_records: int | None = None,
    ) -> None:
        configured = database_path or os.getenv("AAC_RUN_DB_PATH")
        self._uses_default_directory = configured is None
        self.database_path = Path(configured).expanduser() if configured else (
            Path.home() / ".ai-automation-command-center" / "history.sqlite3"
        )
        self.retention_days = int(
            os.getenv("AAC_HISTORY_RETENTION_DAYS", "30")
            if retention_days is None else retention_days
        )
        self.max_records = int(
            os.getenv("AAC_HISTORY_MAX_RECORDS", "500")
            if max_records is None else max_records
        )
        if self.retention_days < 1 or self.max_records < 1:
            raise ValueError("history retention days and max records must be positive")

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.database_path.parent.is_symlink() or self.database_path.is_symlink():
            raise RuntimeError("history directory and database must not be symlinks")
        if self._uses_default_directory:
            try:
                os.chmod(self.database_path.parent, 0o700)
            except OSError:
                # Some platforms/filesystems do not support POSIX permission bits.
                pass
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            os.chmod(self.database_path, 0o600)
        except OSError:
            # Preserve local usability on filesystems without POSIX mode support.
            pass
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_history (
                request_id TEXT PRIMARY KEY,
                project_path TEXT NOT NULL,
                runner TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                results_json TEXT NOT NULL,
                artifact_refs_json TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(execution_history)")}
        if "artifact_refs_json" not in columns:
            connection.execute("ALTER TABLE execution_history ADD COLUMN artifact_refs_json TEXT NOT NULL DEFAULT '[]'")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def save(self, request: ExecutionRequest, result: ExecutionResult) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        summaries: list[dict[str, Any]] = []
        for item in result.results:
            analysis = classify_failure(item.test_id, item.outcome.value, item.message)
            summaries.append(
                {
                    "test_id": item.test_id,
                    "outcome": item.outcome.value,
                    "duration_seconds": item.duration_seconds,
                    "failure_category": analysis.category.value,
                    "failure_summary": analysis.summary,
                    "matched_rule": analysis.matched_rule,
                    "evidence_count": len(item.evidence),
                }
            )

        allowed_artifact_fields = ("artifact_id", "kind", "byte_size", "sha256", "created_at", "media_type")
        artifact_refs = [
            {key: artifact[key] for key in allowed_artifact_fields if key in artifact}
            for artifact in result.metadata.get("artifacts", [])
            if isinstance(artifact, dict) and isinstance(artifact.get("artifact_id"), str)
        ]

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO execution_history
                    (request_id, project_path, runner, status, created_at,
                     started_at, completed_at, results_json, artifact_refs_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    project_path=excluded.project_path,
                    runner=excluded.runner,
                    status=excluded.status,
                    created_at=excluded.created_at,
                    started_at=excluded.started_at,
                    completed_at=excluded.completed_at,
                    results_json=excluded.results_json,
                    artifact_refs_json=excluded.artifact_refs_json
                """,
                (
                    result.request_id,
                    request.target.project_path,
                    request.target.runner,
                    result.status.value,
                    created_at,
                    result.started_at,
                    result.completed_at,
                    json.dumps(summaries, separators=(",", ":"), ensure_ascii=False),
                    json.dumps(artifact_refs, separators=(",", ":"), ensure_ascii=False),
                ),
            )
            self._prune(connection)

    def _prune(self, connection: sqlite3.Connection) -> None:
        """Bound local history by age and count; retain newest records first."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat()
        connection.execute(
            "DELETE FROM execution_history WHERE created_at < ?",
            (cutoff,),
        )
        connection.execute(
            """DELETE FROM execution_history
               WHERE request_id NOT IN (
                   SELECT request_id FROM execution_history
                   ORDER BY created_at DESC, request_id DESC LIMIT ?
               )""",
            (self.max_records,),
        )

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        with self._connection() as connection:
            self._prune(connection)
            rows = connection.execute(
                """
                SELECT request_id, project_path, runner, status, created_at,
                       started_at, completed_at, results_json, artifact_refs_json
                FROM execution_history
                ORDER BY created_at DESC, request_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def get(self, request_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            self._prune(connection)
            row = connection.execute(
                """
                SELECT request_id, project_path, runner, status, created_at,
                       started_at, completed_at, results_json, artifact_refs_json
                FROM execution_history
                WHERE request_id = ?
                """,
                (request_id,),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "request_id": row["request_id"],
            "project_path": row["project_path"],
            "runner": row["runner"],
            "status": row["status"],
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "results": json.loads(row["results_json"]),
            "artifacts": json.loads(row["artifact_refs_json"]),
        }
