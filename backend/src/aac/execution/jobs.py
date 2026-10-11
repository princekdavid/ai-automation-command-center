"""In-process background execution lifecycle with cooperative cancellation.

Jobs are intentionally process-local: a backend restart loses active jobs. SQLite
keeps normalized status/history, but is not a durable queue or multi-worker broker.
"""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event, RLock
from typing import Any

from aac.execution.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus
from aac.execution.history import SQLiteExecutionHistoryStore
from aac.execution.service import ExecutionService


_TERMINAL = {
    ExecutionStatus.PASSED,
    ExecutionStatus.FAILED,
    ExecutionStatus.ERROR,
    ExecutionStatus.CANCELLED,
    ExecutionStatus.REJECTED,
}


class ExecutionJobManager:
    """Bounded in-process job manager; never merges, deploys, or mutates repositories."""

    def __init__(
        self,
        service: ExecutionService,
        history: SQLiteExecutionHistoryStore,
        max_workers: int = 2,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self._service = service
        self._history = history
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="aac-execution")
        self._lock = RLock()
        self._jobs: dict[str, dict[str, Any]] = {}

    def submit(self, request: ExecutionRequest) -> ExecutionResult:
        if not request.policy.allow_side_effects:
            rejected = ExecutionResult(
                request.request_id,
                ExecutionStatus.REJECTED,
                error="Explicit execution authorization is required",
            )
            self._history.save(request, rejected)
            return rejected

        accepted = ExecutionResult(request.request_id, ExecutionStatus.ACCEPTED)
        cancel_event = Event()
        with self._lock:
            if request.request_id in self._jobs:
                raise ValueError("Duplicate execution request ID")
            self._jobs[request.request_id] = {
                "request": request,
                "result": accepted,
                "cancel_event": cancel_event,
                "cancel_requested": False,
                "future": None,
            }
            self._history.save(request, accepted)
            future = self._pool.submit(self._run, request.request_id)
            self._jobs[request.request_id]["future"] = future
        return accepted

    def _run(self, request_id: str) -> None:
        with self._lock:
            job = self._jobs[request_id]
            request = job["request"]
            cancel_event: Event = job["cancel_event"]
            if cancel_event.is_set():
                result = ExecutionResult(
                    request_id, ExecutionStatus.CANCELLED,
                    error="Execution cancelled before it started",
                )
                job["result"] = result
                self._history.save(request, result)
                return
            running = ExecutionResult(request_id, ExecutionStatus.RUNNING)
            job["result"] = running
            self._history.save(request, running)

        try:
            result = self._service.execute(request, cancel_event=cancel_event)
        except Exception:
            # Avoid persisting arbitrary exception text which may contain secrets.
            result = ExecutionResult(
                request_id,
                ExecutionStatus.ERROR,
                error="Execution failed unexpectedly; inspect backend logs on the trusted host",
            )

        with self._lock:
            job = self._jobs[request_id]
            if job["cancel_event"].is_set() and result.status not in _TERMINAL:
                result = ExecutionResult(request_id, ExecutionStatus.CANCELLED, error="Execution cancelled")
            job["result"] = result
            self._history.save(request, result)

    def get(self, request_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(request_id)
            if job is None:
                return None
            return {
                "request_id": request_id,
                "status": job["result"].status.value,
                "cancel_requested": job["cancel_requested"],
                "started_at": job["result"].started_at,
                "completed_at": job["result"].completed_at,
                "error": job["result"].error,
                "results": [
                    {
                        "test_id": item.test_id,
                        "outcome": item.outcome.value,
                        "duration_seconds": item.duration_seconds,
                        "message": item.message,
                    }
                    for item in job["result"].results
                ],
            }

    def cancel(self, request_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(request_id)
            if job is None:
                return None
            result: ExecutionResult = job["result"]
            if result.status in _TERMINAL:
                return self.get(request_id)
            job["cancel_requested"] = True
            job["cancel_event"].set()
            future: Future | None = job["future"]
            if future is not None and future.cancel():
                cancelled = ExecutionResult(
                    request_id,
                    ExecutionStatus.CANCELLED,
                    error="Execution cancelled before it started",
                )
                job["result"] = cancelled
                self._history.save(job["request"], cancelled)
            return self.get(request_id)
