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


def test_test_discovery_endpoint(tmp_path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies = ['pytest']\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_login.py").write_text(
        "def test_login():\n    assert True\n",
        encoding="utf-8",
    )

    response = TestClient(app).post(
        "/api/v1/tests/discovery",
        json={"project_path": str(tmp_path)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["tests"][0]["name"] == "test_login"



def test_execution_endpoint_requires_explicit_authorization(tmp_path):
    response = TestClient(app).post(
        "/api/v1/executions",
        json={
            "project_path": str(tmp_path),
            "runner": "pytest",
            "test_ids": ["pytest:missing"],
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert "authorization" in response.json()["error"].lower()



def test_local_frontend_origin_is_allowed_by_cors() -> None:
    response = TestClient(app).options(
        "/api/v1/tests/discovery",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
