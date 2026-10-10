from aac.execution.contracts import ExecutionPolicy, ExecutionTarget, ExecutionStatus
from aac.execution.pytest_executor import PytestExecutor
from aac.domain.models import DiscoveredTest


def test_executor_rejects_side_effects_by_default(tmp_path):
    test = DiscoveredTest("pytest:1", "test_ok", "tests/test_ok.py", "python", "pytest", "test_ok", metadata={"line": 1, "kind": "function"})
    result = PytestExecutor().execute("r1", ExecutionTarget([test.id], str(tmp_path), "pytest"), ExecutionPolicy(), [test])
    assert result.status is ExecutionStatus.REJECTED


def test_executor_rejects_unknown_test_id(tmp_path):
    result = PytestExecutor().execute("r1", ExecutionTarget(["pytest:missing"], str(tmp_path), "pytest"), ExecutionPolicy(allow_side_effects=True), [])
    assert result.status is ExecutionStatus.REJECTED



def test_junit_failure_message_is_preserved_when_failure_element_has_no_text(tmp_path):
    from aac.execution.contracts import TestOutcome
    from aac.domain.models import DiscoveredTest

    report = tmp_path / "results.xml"
    report.write_text(
        '<testsuite><testcase classname="test_ok" name="test_ok">'
        '<failure message="assertion failed" type="AssertionError" />'
        '</testcase></testsuite>',
        encoding="utf-8",
    )
    test = DiscoveredTest(
        "pytest:1", "test_ok", "tests/test_ok.py", "python", "pytest", "test_ok",
        metadata={"line": 1, "kind": "function"},
    )

    result = PytestExecutor()._parse_junit(report, [test])

    assert result[0].outcome is TestOutcome.FAILED
    assert result[0].message == "assertion failed"
