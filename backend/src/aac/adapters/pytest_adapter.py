import ast
import hashlib
from pathlib import Path

from aac.adapters.base import FrameworkAdapter
from aac.domain.models import DiscoveredTest, FrameworkDNA


class PytestAdapter(FrameworkAdapter):
    """Read-only pytest test discovery using Python AST."""

    name = "pytest"

    def can_handle(self, dna: FrameworkDNA) -> bool:
        return dna.test_runner == "pytest"

    def discover_tests(self, project_path: str, dna: FrameworkDNA) -> list[DiscoveredTest]:
        root = Path(project_path).expanduser().resolve()
        results: list[DiscoveredTest] = []

        for relative_dir in dna.test_paths:
            test_root = root / relative_dir
            if not test_root.is_dir():
                continue

            for path in sorted(test_root.rglob("*.py")):
                results.extend(self._discover_file(root, path))

        return results

    def _discover_file(self, root: Path, path: Path) -> list[DiscoveredTest]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, SyntaxError):
            return []

        relative = str(path.relative_to(root))
        results: list[DiscoveredTest] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                stable_id = hashlib.sha1(
                    f"pytest::{relative}::{node.name}".encode()
                ).hexdigest()[:16]
                results.append(
                    DiscoveredTest(
                        id=f"pytest:{stable_id}",
                        name=node.name,
                        source_path=relative,
                        framework="python",
                        runner="pytest",
                        suite=path.stem,
                        metadata={"line": node.lineno},
                    )
                )

        return sorted(
            results,
            key=lambda item: (item.source_path, item.metadata.get("line", 0), item.name),
        )
