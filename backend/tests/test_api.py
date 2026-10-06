from fastapi.testclient import TestClient

from aac.api import app


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_discovery_endpoint(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies = ['pytest']\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()

    response = TestClient(app).post(
        "/api/v1/discovery",
        json={"project_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "python"
    assert body["test_runner"] == "pytest"
    assert body["capabilities"][0]["id"] == "TEST_DISCOVERY"
