"""Local SQLite history for normalized execution summaries.

Raw stdout/stderr and raw per-test failure messages are intentionally not persisted.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aac.analysis.failure_classifier import classify_failure
from aac.execution.contracts import ExecutionRequest, ExecutionResult


class SQLiteExecutionHistoryStore:
    """Persist compact, local-only execution summaries without raw logs."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        configured = database_path or os.getenv("AAC_RUN_DB_PATH")
        self.database_path = Path(configured).expanduser() if configured else (
            Path.home() / ".ai-automation-command-center" / "history.sqlite3"
        )

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
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
                results_json TEXT NOT NULL
            )
            """
        )
        return connection

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

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO execution_history
                    (request_id, project_path, runner, status, created_at,
                     started_at, completed_at, results_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(request_id) DO UPDATE SET
                    project_path=excluded.project_path,
                    runner=excluded.runner,
                    status=excluded.status,
                    created_at=excluded.created_at,
                    started_at=excluded.started_at,
                    completed_at=excluded.completed_at,
                    results_json=excluded.results_json
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
                ),
            )

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT request_id, project_path, runner, status, created_at,
                       started_at, completed_at, results_json
                FROM execution_history
                ORDER BY created_at DESC, request_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def get(self, request_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT request_id, project_path, runner, status, created_at,
                       started_at, completed_at, results_json
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
        }
