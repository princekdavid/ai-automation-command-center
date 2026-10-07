import ast
import hashlib
from pathlib import Path
from aac.adapters.base import FrameworkAdapter
from aac.domain.models import AdapterCapability, DiscoveredTest, FrameworkDNA

class PytestAdapter(FrameworkAdapter):
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
        results = []
        for relative_dir in dna.test_paths:
            test_root = root / relative_dir
            if not test_root.is_dir():
                continue
            for path in sorted(test_root.rglob("*.py")):
                if any(part.startswith(".") or part in {".venv", "venv", "__pycache__"} for part in path.relative_to(root).parts):
                    continue
                results.extend(self._discover_file(root, path))
        return results

    def _discover_file(self, root: Path, path: Path) -> list[DiscoveredTest]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, SyntaxError):
            return []
        relative = str(path.relative_to(root))
        results = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                        results.append(self._test_record(relative, child, node.name, "method"))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                results.append(self._test_record(relative, node, path.stem, "function"))
        return sorted(results, key=lambda item: (item.source_path, item.metadata.get("line", 0), item.name))

    def _test_record(self, relative: str, node, suite: str, kind: str) -> DiscoveredTest:
        stable_id = hashlib.sha1(f"pytest::{relative}::{suite}::{node.name}::{node.lineno}".encode()).hexdigest()[:16]
        return DiscoveredTest(
            id=f"pytest:{stable_id}", name=node.name, source_path=relative,
            framework="python", runner="pytest", suite=suite,
            metadata={"line": node.lineno, "kind": kind},
        )
