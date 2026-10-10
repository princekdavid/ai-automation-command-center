from pathlib import Path
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from aac.execution.contracts import ExecutionPolicy, ExecutionResult, ExecutionStatus, ExecutionTarget, TestOutcome, TestResult
from aac.domain.models import DiscoveredTest

class PytestExecutor:
    """Controlled pytest executor; execution requires explicit side-effect permission."""
    runner = "pytest"

    def execute(self, request_id: str, target: ExecutionTarget, policy: ExecutionPolicy, discovered_tests: list[DiscoveredTest]) -> ExecutionResult:
        root = Path(target.project_path).expanduser().resolve()
        if not root.is_dir(): return ExecutionResult(request_id, ExecutionStatus.REJECTED, error="Project path does not exist")
        if target.runner != self.runner or not target.test_ids: return ExecutionResult(request_id, ExecutionStatus.REJECTED, error="Unsupported or empty pytest target")
        if not policy.allow_side_effects: return ExecutionResult(request_id, ExecutionStatus.REJECTED, error="Explicit side-effect authorization is required for test execution")
        by_id = {item.id: item for item in discovered_tests}
        selected = [by_id.get(item) for item in target.test_ids]
        if any(item is None for item in selected): return ExecutionResult(request_id, ExecutionStatus.REJECTED, error="One or more test IDs were not discovered for this project")
        nodeids = [f"{item.source_path}::{item.suite}::{item.name}" if item.metadata.get("kind") == "method" else f"{item.source_path}::{item.name}" for item in selected if item]
        started = time.time()
        with tempfile.TemporaryDirectory(prefix="aac-pytest-") as temp_dir:
            report = Path(temp_dir) / "results.xml"
            command = ["pytest", "-q", f"--junitxml={report}"] + nodeids
            try: completed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=policy.timeout_seconds, check=False)
            except subprocess.TimeoutExpired: return ExecutionResult(request_id, ExecutionStatus.ERROR, started_at=str(started), completed_at=str(time.time()), error="pytest execution timed out")
            except OSError as exc: return ExecutionResult(request_id, ExecutionStatus.ERROR, started_at=str(started), completed_at=str(time.time()), error=f"Unable to start pytest: {exc}")
            results = self._parse_junit(report, selected)
            status = ExecutionStatus.PASSED if completed.returncode == 0 else ExecutionStatus.FAILED
            return ExecutionResult(request_id, status, results, str(started), str(time.time()), None if completed.returncode == 0 else (completed.stderr or completed.stdout)[-4000:])

    def _parse_junit(self, report: Path, selected: list[DiscoveredTest | None]) -> list[TestResult]:
        if not report.exists(): return [TestResult(item.id, TestOutcome.ERROR, message="JUnit report was not produced") for item in selected if item]
        try: root = ET.parse(report).getroot()
        except ET.ParseError: return [TestResult(item.id, TestOutcome.ERROR, message="JUnit report could not be parsed") for item in selected if item]
        cases = list(root.iter("testcase")); results=[]
        for item in selected:
            if not item: continue
            node_name = f"{item.suite}::{item.name}" if item.metadata.get("kind") == "method" else item.name
            case = next((c for c in cases if c.attrib.get("name") == node_name), None)
            if case is None: outcome, message = TestOutcome.ERROR, "Test result was not found in report"
            elif case.find("failure") is not None or case.find("error") is not None:
                node = case.find("failure")
                if node is None:
                    node = case.find("error")
                message = None
                if node is not None:
                    message = node.text or node.attrib.get("message") or node.attrib.get("type")
                outcome = TestOutcome.FAILED
            elif case.find("skipped") is not None: outcome, message = TestOutcome.SKIPPED, None
            else: outcome, message = TestOutcome.PASSED, None
            results.append(TestResult(item.id, outcome, float(case.attrib["time"]) if case is not None and "time" in case.attrib else None, message))
        return results
