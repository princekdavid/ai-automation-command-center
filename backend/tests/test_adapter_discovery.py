from pathlib import Path

from aac.adapters.pytest_adapter import PytestAdapter
from aac.discovery.service import DiscoveryService
from aac.domain.models import FrameworkDNA


def test_pytest_adapter_discovers_functions(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies=['pytest', 'playwright']\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_login.py").write_text(
        "def test_valid_login():\n    assert True\n\nasync def test_async_login():\n    assert True\n",
        encoding="utf-8",
    )

    dna = DiscoveryService().discover(str(tmp_path))
    discovered = PytestAdapter().discover_tests(str(tmp_path), dna)

    assert [item.name for item in discovered] == ["test_valid_login", "test_async_login"]
    assert len({item.id for item in discovered}) == 2


def test_adapter_does_not_modify_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies=['pytest']\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text(
        "def test_sample():\n    assert True\n",
        encoding="utf-8",
    )

    dna = DiscoveryService().discover(str(tmp_path))
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))

    PytestAdapter().discover_tests(str(tmp_path), dna)

    after = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    assert before == after


def test_adapter_can_handle_only_pytest() -> None:
    dna = FrameworkDNA(
        project_path="/tmp/project",
        language="python",
        package_manager="pyproject",
        test_runner="pytest",
        ui_framework=None,
        api_framework=None,
        database_tools=[],
        test_paths=[],
        config_files=[],
        dependency_files=[],
        capabilities=[],
    )
    assert PytestAdapter().can_handle(dna) is True



def test_adapter_follows_basic_pytest_collection_rules(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\\ndependencies=['pytest']\\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_collection.py").write_text(
        "def test_module_function():\\n    def test_nested_helper():\\n        pass\\n"
        "class TestLogin:\\n    def test_method(self):\\n        pass\\n"
        "class Helper:\\n    def test_not_collected(self):\\n        pass\\n",
        encoding="utf-8",
    )

    dna = DiscoveryService().discover(str(tmp_path))
    discovered = PytestAdapter().discover_tests(str(tmp_path), dna)

    assert [(item.name, item.metadata["kind"]) for item in discovered] == [
        ("test_module_function", "function"),
        ("test_method", "method"),
    ]
