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
