from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionMode(str, Enum):
    SINGLE = "single"
    SELECTION = "selection"


class ExecutionStatus(str, Enum):
    ACCEPTED = "accepted"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TestOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    XFAILED = "xfailed"
    XPASS = "xpassed"
    ERROR = "error"


@dataclass(frozen=True)
class ExecutionTarget:
    """Framework-neutral identity of tests selected for execution."""

    test_ids: list[str]
    project_path: str
    runner: str


@dataclass(frozen=True)
class ExecutionPolicy:
    """Safety and runtime constraints supplied by the caller."""

    allow_side_effects: bool = False
    timeout_seconds: int = 300
    environment: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionRequest:
    """Immutable request contract; no execution is implied by constructing it."""

    request_id: str
    mode: ExecutionMode
    target: ExecutionTarget
    policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceReference:
    """Pointer to an artifact produced by an execution engine."""

    kind: str
    location: str
    label: str | None = None


@dataclass(frozen=True)
class TestResult:
    """Normalized result for one discovered test."""

    test_id: str
    outcome: TestOutcome
    duration_seconds: float | None = None
    message: str | None = None
    evidence: list[EvidenceReference] = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionResult:
    """Framework-neutral execution result returned by a future runner."""

    request_id: str
    status: ExecutionStatus
    results: list[TestResult] = field(default_factory=list)
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
