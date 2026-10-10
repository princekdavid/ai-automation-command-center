from fastapi.testclient import TestClient

from aac.api import app
from aac.execution.history import SQLiteExecutionHistoryStore


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



def test_failure_analysis_endpoint_returns_deterministic_category() -> None:
    response = TestClient(app).post(
        "/api/v1/analysis/failures",
        json={
            "results": [
                {
                    "test_id": "pytest:failed",
                    "outcome": "failed",
                    "message": "Locator not found: #submit",
                },
                {
                    "test_id": "pytest:passed",
                    "outcome": "passed",
                    "message": None,
                },
            ]
        },
    )

    assert response.status_code == 200
    analyses = response.json()["analyses"]
    assert analyses[0]["category"] == "locator_not_found"
    assert analyses[0]["matched_rule"] == "locator not found"
    assert analyses[1]["category"] == "not_applicable"



def test_execution_history_api_persists_and_retrieves_summary(tmp_path, monkeypatch) -> None:
    store = SQLiteExecutionHistoryStore(tmp_path / "history.sqlite3")
    monkeypatch.setattr("aac.api.history_store", store)
    client = TestClient(app)

    created = client.post(
        "/api/v1/executions",
        json={
            "project_path": str(tmp_path),
            "runner": "pytest",
            "test_ids": ["pytest:missing"],
        },
    )

    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "rejected"
    assert body["history_saved"] is True

    listing = client.get("/api/v1/executions?limit=10")
    assert listing.status_code == 200
    assert listing.json()["count"] == 1
    assert listing.json()["executions"][0]["request_id"] == body["request_id"]

    detail = client.get(f"/api/v1/executions/{body['request_id']}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "rejected"
