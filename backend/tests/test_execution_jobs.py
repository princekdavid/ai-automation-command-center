from threading import Event
import time

from aac.execution.contracts import (
    ExecutionMode,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionTarget,
)
from aac.execution.jobs import ExecutionJobManager


class MemoryHistory:
    def __init__(self):
        self.records = {}

    def save(self, request, result):
        self.records[request.request_id] = result.status.value

    def get(self, request_id):
        return None


class WaitingService:
    def __init__(self):
        self.started = Event()

    def execute(self, request, cancel_event=None):
        self.started.set()
        if cancel_event.wait(timeout=2):
            return ExecutionResult(request.request_id, ExecutionStatus.CANCELLED, error="cancelled")
        return ExecutionResult(request.request_id, ExecutionStatus.PASSED)


def make_request(request_id="job-1", authorized=True):
    return ExecutionRequest(
        request_id,
        ExecutionMode.SINGLE,
        ExecutionTarget(["pytest:test"], "/tmp/project", "pytest"),
        ExecutionPolicy(allow_side_effects=authorized),
    )


def wait_for_status(manager, request_id, expected, timeout=2):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        snapshot = manager.get(request_id)
        if snapshot and snapshot["status"] == expected:
            return snapshot
        time.sleep(0.01)
    raise AssertionError(f"job did not reach {expected}: {manager.get(request_id)}")


def test_submit_records_lifecycle_and_completes():
    history = MemoryHistory()
    service = WaitingService()
    manager = ExecutionJobManager(service, history, max_workers=1)

    accepted = manager.submit(make_request())

    assert accepted.status is ExecutionStatus.ACCEPTED
    assert service.started.wait(timeout=1)
    finished = wait_for_status(manager, "job-1", "passed")
    assert finished["cancel_requested"] is False
    assert history.records["job-1"] == "passed"


def test_cancel_running_job_sets_signal_and_finishes_cancelled():
    history = MemoryHistory()
    service = WaitingService()
    manager = ExecutionJobManager(service, history, max_workers=1)

    manager.submit(make_request("job-cancel"))
    assert service.started.wait(timeout=1)

    snapshot = manager.cancel("job-cancel")

    assert snapshot is not None
    assert snapshot["cancel_requested"] is True
    finished = wait_for_status(manager, "job-cancel", "cancelled")
    assert finished["status"] == "cancelled"
    assert history.records["job-cancel"] == "cancelled"


def test_unauthorized_job_is_rejected_without_starting_worker():
    history = MemoryHistory()
    service = WaitingService()
    manager = ExecutionJobManager(service, history, max_workers=1)

    result = manager.submit(make_request("job-denied", authorized=False))

    assert result.status is ExecutionStatus.REJECTED
    assert not service.started.is_set()
    assert history.records["job-denied"] == "rejected"


def test_unknown_job_cannot_be_cancelled():
    manager = ExecutionJobManager(WaitingService(), MemoryHistory(), max_workers=1)
    assert manager.cancel("missing") is None
