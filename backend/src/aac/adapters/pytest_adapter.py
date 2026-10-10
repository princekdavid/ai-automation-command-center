import ast
import hashlib
from pathlib import Path

from aac.adapters.base import FrameworkAdapter
from aac.domain.models import AdapterCapability, DiscoveredTest, FrameworkDNA


class PytestAdapter(FrameworkAdapter):
    """Read-only AST discovery for pytest-style module functions and Test* classes."""

    name = "pytest"

    def can_handle(self, dna: FrameworkDNA) -> bool:
        return dna.test_runner == "pytest"

    def capabilities(self) -> list[AdapterCapability]:
        return [
            AdapterCapability("TEST_DISCOVERY", "Test discovery", True, "AST-based read-only discovery"),
            AdapterCapability("TEST_EXECUTION", "Test execution", True, "Controlled local pytest execution with explicit authorization"),
            AdapterCapability("RESULT_COLLECTION", "Result collection", True, "JUnit XML results normalized into execution contracts"),
        ]

    def discover_tests(self, project_path: str, dna: FrameworkDNA) -> list[DiscoveredTest]:
        root = Path(project_path).expanduser().resolve()
        results: list[DiscoveredTest] = []
        seen_paths: set[Path] = set()

        for relative_dir in dna.test_paths:
            test_root = (root / relative_dir).resolve()
            # A discovered path must remain inside the selected project, including symlink resolution.
            if not test_root.is_relative_to(root) or not test_root.is_dir():
                continue
            for path in sorted(test_root.rglob("*.py")):
                resolved = path.resolve()
                if resolved in seen_paths or not resolved.is_relative_to(root):
                    continue
                relative_parts = path.relative_to(root).parts
                if any(
                    part.startswith(".")
                    or part in {"venv", ".venv", "__pycache__", "node_modules", "site-packages", "build", "dist"}
                    for part in relative_parts
                ):
                    continue
                seen_paths.add(resolved)
                results.extend(self._discover_file(root, path))

        return sorted(
            results,
            key=lambda item: (item.source_path, item.metadata.get("line", 0), item.name, item.id),
        )

    def _discover_file(self, root: Path, path: Path) -> list[DiscoveredTest]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, SyntaxError, UnicodeError):
            return []

        relative = str(path.relative_to(root))
        results: list[DiscoveredTest] = []

        # Pytest collects module-level test functions and test methods in Test* classes.
        # Inspect only direct module/class members: nested helper functions are not tests.
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                results.append(self._test_record(relative, node, path.stem, "function"))
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                for child in node.body:
                    if (
                        isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and child.name.startswith("test_")
                    ):
                        results.append(self._test_record(relative, child, node.name, "method"))

        return results

    def _test_record(self, relative: str, node, suite: str, kind: str) -> DiscoveredTest:
        stable_id = hashlib.sha1(
            f"pytest::{relative}::{suite}::{node.name}::{node.lineno}".encode()
        ).hexdigest()[:16]
        return DiscoveredTest(
            id=f"pytest:{stable_id}",
            name=node.name,
            source_path=relative,
            framework="python",
            runner="pytest",
            suite=suite,
            metadata={"line": node.lineno, "kind": kind},
        )
