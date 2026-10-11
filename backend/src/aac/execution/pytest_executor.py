from pathlib import Path
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
from threading import Event

from aac.execution.contracts import (
    ExecutionPolicy,
    ExecutionResult,
    ExecutionStatus,
    ExecutionTarget,
    TestOutcome,
    TestResult,
)
from aac.domain.models import DiscoveredTest
from aac.execution.artifacts import ArtifactStoreError, LocalEvidenceArtifactStore


class PytestExecutor:
    """Controlled local pytest executor with timeout and cooperative cancellation."""

    runner = "pytest"

    def __init__(self, artifact_store: LocalEvidenceArtifactStore | None = None) -> None:
        self.artifact_store = artifact_store or LocalEvidenceArtifactStore()

    def execute(
        self,
        request_id: str,
        target: ExecutionTarget,
        policy: ExecutionPolicy,
        discovered_tests: list[DiscoveredTest],
        cancel_event: Event | None = None,
    ) -> ExecutionResult:
        root = Path(target.project_path).expanduser().resolve()
        if not root.is_dir():
            return ExecutionResult(request_id, ExecutionStatus.REJECTED, error="Project path does not exist")
        if target.runner != self.runner or not target.test_ids:
            return ExecutionResult(request_id, ExecutionStatus.REJECTED, error="Unsupported or empty pytest target")
        if not policy.allow_side_effects:
            return ExecutionResult(request_id, ExecutionStatus.REJECTED, error="Explicit side-effect authorization is required for test execution")
        by_id = {item.id: item for item in discovered_tests}
        selected = [by_id.get(item) for item in target.test_ids]
        if any(item is None for item in selected):
            return ExecutionResult(request_id, ExecutionStatus.REJECTED, error="One or more test IDs were not discovered for this project")
        if cancel_event is not None and cancel_event.is_set():
            return ExecutionResult(request_id, ExecutionStatus.CANCELLED, error="Execution cancelled before pytest started")

        nodeids = [
            f"{item.source_path}::{item.suite}::{item.name}"
            if item.metadata.get("kind") == "method"
            else f"{item.source_path}::{item.name}"
            for item in selected if item
        ]
        started = time.time()
        deadline = time.monotonic() + policy.timeout_seconds
        with tempfile.TemporaryDirectory(prefix="aac-pytest-") as temp_dir:
            report = Path(temp_dir) / "results.xml"
            command = ["pytest", "-q", f"--junitxml={report}", *nodeids]
            # Redirect to temporary files rather than PIPEs so a noisy test cannot
            # block on a full OS pipe buffer while the manager polls process state.
            with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
                try:
                    process = subprocess.Popen(
                        command,
                        cwd=root,
                        stdout=stdout_file,
                        stderr=stderr_file,
                    )
                except OSError:
                    return ExecutionResult(
                        request_id, ExecutionStatus.ERROR,
                        started_at=str(started), completed_at=str(time.time()),
                        error="Unable to start pytest; verify Python and pytest are installed in the backend environment",
                    )

                cancelled = False
                timed_out = False
                while process.poll() is None:
                    if cancel_event is not None and cancel_event.is_set():
                        cancelled = True
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                        break
                    if time.monotonic() >= deadline:
                        timed_out = True
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                        break
                    time.sleep(0.05)

                process.wait()
                completed_at = str(time.time())

                def tail(handle) -> str:
                    handle.seek(0, 2)
                    end = handle.tell()
                    handle.seek(max(0, end - 4000))
                    return handle.read().decode("utf-8", errors="replace")

                stdout_tail = tail(stdout_file)
                stderr_tail = tail(stderr_file)
                if cancelled:
                    return ExecutionResult(
                        request_id, ExecutionStatus.CANCELLED,
                        started_at=str(started), completed_at=completed_at,
                        error="pytest execution cancelled by request",
                    )
                if timed_out:
                    return ExecutionResult(
                        request_id, ExecutionStatus.ERROR,
                        started_at=str(started), completed_at=completed_at,
                        error="pytest execution timed out",
                    )

                results = self._parse_junit(report, selected)
                status = ExecutionStatus.PASSED if process.returncode == 0 else ExecutionStatus.FAILED
                error = None if process.returncode == 0 else (stderr_tail or stdout_tail)[-4000:]
                metadata = {}
                if report.is_file():
                    try:
                        artifact = self.artifact_store.save(
                            request_id, "junit", report.read_bytes(), "application/xml"
                        )
                        metadata["artifacts"] = [artifact]
                    except (ArtifactStoreError, OSError, ValueError):
                        # Evidence retention is best-effort and must not change the
                        # test outcome or expose artifact-store internals to callers.
                        metadata["artifact_persistence"] = "unavailable"
                return ExecutionResult(
                    request_id, status, results, str(started), completed_at, error, metadata
                )

    def _parse_junit(self, report: Path, selected: list[DiscoveredTest | None]) -> list[TestResult]:
        if not report.exists():
            return [TestResult(item.id, TestOutcome.ERROR, message="JUnit report was not produced") for item in selected if item]
        try:
            root = ET.parse(report).getroot()
        except ET.ParseError:
            return [TestResult(item.id, TestOutcome.ERROR, message="JUnit report could not be parsed") for item in selected if item]
        cases = list(root.iter("testcase"))
        results = []
        for item in selected:
            if not item:
                continue
            case = next(
                (
                    candidate for candidate in cases
                    if candidate.attrib.get("name") == item.name
                    and Path(item.source_path).stem in candidate.attrib.get("classname", "").split(".")
                    and (
                        item.metadata.get("kind") != "method"
                        or candidate.attrib.get("classname", "").split(".")[-1] == item.suite
                    )
                ),
                None,
            )
            if case is None:
                outcome, message = TestOutcome.ERROR, "Test result was not found in report"
            elif case.find("failure") is not None or case.find("error") is not None:
                node = case.find("failure")
                if node is None:
                    node = case.find("error")
                message = None if node is None else (
                    node.text or node.attrib.get("message") or node.attrib.get("type")
                )
                outcome = TestOutcome.FAILED
            elif case.find("skipped") is not None:
                outcome, message = TestOutcome.SKIPPED, None
            else:
                outcome, message = TestOutcome.PASSED, None
            duration = float(case.attrib["time"]) if case is not None and "time" in case.attrib else None
            results.append(TestResult(item.id, outcome, duration, message))
        return results
