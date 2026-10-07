from aac.execution.contracts import (
    ExecutionMode,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    ExecutionTarget,
    TestOutcome,
    TestResult,
)


def test_execution_request_is_safe_by_default():
    request = ExecutionRequest(
        request_id="req-1",
        mode=ExecutionMode.SINGLE,
        target=ExecutionTarget(
            test_ids=["pytest:abc123"],
            project_path="/workspace/project",
            runner="pytest",
        ),
    )

    assert request.policy.allow_side_effects is False
    assert request.policy.timeout_seconds == 300
    assert request.target.runner == "pytest"


def test_execution_result_normalizes_test_outcomes():
    result = TestResult(test_id="pytest:abc123", outcome=TestOutcome.PASSED)

    assert result.outcome is TestOutcome.PASSED
    assert ExecutionStatus.ACCEPTED.value == "accepted"
