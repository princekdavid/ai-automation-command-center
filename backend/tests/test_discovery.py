from pathlib import Path

from aac.discovery.service import DiscoveryService


def create_project(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies = ['pytest', 'playwright', 'httpx']\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    return tmp_path


def test_discovery_detects_python_pytest_and_ui(tmp_path: Path) -> None:
    dna = DiscoveryService().discover(str(create_project(tmp_path)))

    assert dna.language == "python"
    assert dna.package_manager == "pyproject"
    assert dna.test_runner == "pytest"
    assert dna.ui_framework == "playwright"
    assert dna.api_framework == "httpx"
    assert "tests" in dna.test_paths
    assert "pytest.ini" in dna.config_files


def test_discovery_is_read_only(tmp_path: Path) -> None:
    project = create_project(tmp_path)
    before = sorted(p.relative_to(project) for p in project.rglob("*"))

    DiscoveryService().discover(str(project))

    after = sorted(p.relative_to(project) for p in project.rglob("*"))
    assert before == after



def test_discovery_skips_generated_directories(tmp_path: Path) -> None:
    project = create_project(tmp_path)
    generated_tests = project / "node_modules" / "fake-package" / "tests"
    generated_tests.mkdir(parents=True)
    (generated_tests / "package.json").write_text(
        '{"dependencies": {"playwright": "1.0"}}',
        encoding="utf-8",
    )
    generated_config = project / ".venv" / "pytest.ini"
    generated_config.parent.mkdir(parents=True)
    generated_config.write_text("[pytest]", encoding="utf-8")

    dna = DiscoveryService().discover(str(project))

    assert "node_modules/fake-package/tests" not in dna.test_paths
    assert ".venv/pytest.ini" not in dna.config_files


def test_discovery_does_not_follow_symlinks_outside_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        "[project]\\ndependencies = ['pytest']\\n",
        encoding="utf-8",
    )
    external = tmp_path / "external"
    (external / "tests").mkdir(parents=True)
    (external / "tests" / "test_external.py").write_text(
        "def test_external(): pass\\n",
        encoding="utf-8",
    )
    try:
        (project / "linked-tests").symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("Directory symlinks are not supported on this platform")

    dna = DiscoveryService().discover(str(project))

    assert not any(path.startswith("linked-tests") for path in dna.test_paths)
    assert not any("external" in path for path in dna.config_files)



def test_framework_detection_ignores_generated_dependency_copies(tmp_path: Path) -> None:
    project = tmp_path
    (project / "pyproject.toml").write_text(
        "[project]\\ndependencies = ['pytest']\\n",
        encoding="utf-8",
    )
    (project / "tests").mkdir()
    copied_package = project / "node_modules" / "vendor"
    copied_package.mkdir(parents=True)
    (copied_package / "bundle.js").write_text("const playwright = true;", encoding="utf-8")

    dna = DiscoveryService().discover(str(project))

    assert dna.test_runner == "pytest"
    assert dna.ui_framework is None
