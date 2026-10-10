import os
from pathlib import Path

from aac.domain.models import Capability, FrameworkDNA


class DiscoveryService:
    """Perform conservative, read-only discovery of a local automation project."""

    DEPENDENCY_FILES = {
        "pyproject.toml": ("python", "pyproject"),
        "requirements.txt": ("python", "pip"),
        "package.json": ("javascript", "npm"),
        "pom.xml": ("java", "maven"),
        "build.gradle": ("java", "gradle"),
        "build.gradle.kts": ("kotlin", "gradle"),
    }
    EXCLUDED_DIRS = {
        ".git", ".venv", "venv", "env", "__pycache__", "node_modules",
        "site-packages", ".tox", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "build", "dist", "coverage", ".next", ".turbo",
    }
    MAX_INSPECTED_FILE_BYTES = 2_000_000
    MAX_DISCOVERED_PATHS = 100

    def discover(self, project_path: str) -> FrameworkDNA:
        root = Path(project_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")

        dependency_files = sorted(
            path.name for path in root.iterdir()
            if path.is_file() and not path.is_symlink() and path.name in self.DEPENDENCY_FILES
        )
        language = self._detect_language(dependency_files)
        package_manager = self._detect_package_manager(dependency_files)
        test_runner = self._detect_test_runner(root, language)
        ui_framework = self._detect_ui_framework(root, language)
        api_framework = self._detect_api_framework(root, language)
        test_paths = self._find_test_paths(root)
        config_files = self._find_config_files(root)

        capabilities = [
            Capability("TEST_DISCOVERY", "Test discovery", bool(test_paths), test_paths),
            Capability("UI_AUTOMATION", "UI automation", ui_framework is not None, [ui_framework] if ui_framework else []),
            Capability("API_TESTING", "API testing", api_framework is not None, [api_framework] if api_framework else []),
        ]
        return FrameworkDNA(
            project_path=str(root), language=language, package_manager=package_manager,
            test_runner=test_runner, ui_framework=ui_framework, api_framework=api_framework,
            database_tools=[], test_paths=test_paths, config_files=config_files,
            dependency_files=dependency_files, capabilities=capabilities,
        )

    def _detect_language(self, files: list[str]) -> str | None:
        languages = {self.DEPENDENCY_FILES[name][0] for name in files}
        if len(languages) == 1:
            return next(iter(languages))
        if "python" in languages:
            return "python"
        return "multi-language" if languages else None

    def _detect_package_manager(self, files: list[str]) -> str | None:
        return self.DEPENDENCY_FILES[files[0]][1] if files else None

    def _detect_test_runner(self, root: Path, language: str | None) -> str | None:
        candidates = {
            "python": (("pytest", "pytest"), ("unittest", "unittest")),
            "javascript": (("playwright", "playwright"), ("cypress", "cypress")),
            "typescript": (("playwright", "playwright"), ("cypress", "cypress")),
            "java": (("testng", "testng"), ("junit", "junit")),
            "kotlin": (("testng", "testng"), ("junit", "junit")),
        }
        return self._first_named_match(root, candidates.get(language, ()))

    def _detect_ui_framework(self, root: Path, language: str | None) -> str | None:
        names = {
            "python": ("playwright", "selenium"),
            "javascript": ("playwright", "cypress", "selenium"),
            "typescript": ("playwright", "cypress", "selenium"),
            "java": ("playwright", "selenium"),
            "kotlin": ("playwright", "selenium"),
        }
        return self._first_match(root, names.get(language, ()))

    def _detect_api_framework(self, root: Path, language: str | None) -> str | None:
        names = {"python": ("requests", "httpx"), "javascript": ("axios",), "typescript": ("axios",)}
        return self._first_match(root, names.get(language, ()))

    def _iter_project_paths(self, root: Path):
        """Yield bounded, in-project paths while pruning generated and symlinked directories."""
        root = root.resolve()

        def onerror(_error: OSError) -> None:
            # Permission-denied or concurrently removed directories are skipped, not fatal.
            return None

        for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False, onerror=onerror):
            current_path = Path(current)
            safe_dirs = []
            for name in sorted(dirnames):
                candidate = current_path / name
                if name in self.EXCLUDED_DIRS or name.startswith(".") or candidate.is_symlink():
                    continue
                try:
                    if candidate.resolve().is_relative_to(root) and candidate.is_dir():
                        safe_dirs.append(name)
                except OSError:
                    continue
            dirnames[:] = safe_dirs

            try:
                if not current_path.resolve().is_relative_to(root):
                    dirnames[:] = []
                    continue
            except OSError:
                dirnames[:] = []
                continue

            for name in sorted(filenames):
                path = current_path / name
                try:
                    if path.is_symlink() or not path.resolve().is_relative_to(root):
                        continue
                except OSError:
                    continue
                yield path

            for name in safe_dirs:
                yield current_path / name

    def _find_test_paths(self, root: Path) -> list[str]:
        found = [
            str(path.relative_to(root))
            for path in self._iter_project_paths(root)
            if path.is_dir() and path.name in {"tests", "test", "__tests__"}
        ]
        return sorted(set(found))[: self.MAX_DISCOVERED_PATHS]

    def _find_config_files(self, root: Path) -> list[str]:
        known = {
            "pytest.ini", "tox.ini", "setup.cfg", "playwright.config.ts",
            "playwright.config.js", "cypress.config.ts", "cypress.config.js",
        }
        found = [
            str(path.relative_to(root))
            for path in self._iter_project_paths(root)
            if path.is_file() and path.name in known
        ]
        return sorted(set(found))[: self.MAX_DISCOVERED_PATHS]

    def _first_named_match(self, root: Path, candidates: tuple[tuple[str, str], ...]) -> str | None:
        for needle, result in candidates:
            if self._contains(root, needle):
                return result
        return None

    def _first_match(self, root: Path, needles: tuple[str, ...]) -> str | None:
        for needle in needles:
            if self._contains(root, needle):
                return needle
        return None

    def _contains(self, root: Path, needle: str) -> bool:
        for path in self._iter_project_paths(root):
            try:
                if not path.is_file() or path.stat().st_size > self.MAX_INSPECTED_FILE_BYTES:
                    continue
                content = path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            if needle.lower() in content:
                return True
        return False
