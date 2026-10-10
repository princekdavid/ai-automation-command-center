"""Execution orchestration for framework-neutral test runs."""

from aac.adapters.registry import AdapterRegistry
from aac.domain.models import DiscoveredTest
from aac.execution.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus
from aac.execution.pytest_executor import PytestExecutor


class ExecutionService:
    """Validate capability and authorization before invoking a framework executor."""

    def __init__(self, discovery_service, registry=None, executors=None) -> None:
        self.discovery = discovery_service
        self.registry = registry or AdapterRegistry()
        self.executors = executors or {"pytest": PytestExecutor()}

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if not request.policy.allow_side_effects:
            return ExecutionResult(
                request.request_id,
                ExecutionStatus.REJECTED,
                error="Explicit execution authorization is required",
            )

        # Reject unsupported runners before discovery/adapter resolution. This keeps
        # unsupported requests deterministic and prevents an unhandled LookupError.
        executor = self.executors.get(request.target.runner)
        if executor is None:
            return ExecutionResult(
                request.request_id,
                ExecutionStatus.REJECTED,
                error=f"No executor registered for runner: {request.target.runner}",
            )

        dna = self.discovery.discover(request.target.project_path)
        try:
            adapter = self.registry.resolve(dna)
        except LookupError as exc:
            return ExecutionResult(
                request.request_id,
                ExecutionStatus.REJECTED,
                error=f"Test execution is unsupported: {exc}",
            )

        capabilities = {item.id: item for item in adapter.capabilities()}
        execution_capability = capabilities.get("TEST_EXECUTION")
        if execution_capability is None or not execution_capability.supported:
            return ExecutionResult(
                request.request_id,
                ExecutionStatus.REJECTED,
                error=f"Test execution is unsupported by adapter: {adapter.name}",
            )

        discovered: list[DiscoveredTest] = adapter.discover_tests(
            request.target.project_path, dna
        )
        return executor.execute(
            request.request_id,
            request.target,
            request.policy,
            discovered,
        )
