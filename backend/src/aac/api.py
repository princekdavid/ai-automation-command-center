import os
import sqlite3
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from aac.discovery.service import DiscoveryService
from aac.discovery.test_service import TestDiscoveryService
from aac.execution.contracts import ExecutionMode, ExecutionPolicy, ExecutionRequest, ExecutionTarget
from aac.execution.service import ExecutionService
from aac.analysis.failure_classifier import classify_failure
from aac.execution.history import SQLiteExecutionHistoryStore

app = FastAPI(title="AI Automation Command Center", version="0.1.0")
# Local Vite development origins only by default. Deployments must configure explicit trusted origins.
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "AAC_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
discovery = DiscoveryService()
test_discovery = TestDiscoveryService(discovery=discovery)
execution_service = ExecutionService(discovery_service=discovery)
history_store = SQLiteExecutionHistoryStore()

class DiscoverRequest(BaseModel):
    project_path: str

class ExecuteRequest(BaseModel):
    project_path: str
    runner: str
    test_ids: list[str] = Field(min_length=1)
    authorize_execution: bool = False
    timeout_seconds: int = Field(default=300, ge=1, le=3600)

class FailureInput(BaseModel):
    test_id: str
    outcome: Literal["passed", "failed", "error", "skipped", "xfailed", "xpassed"]
    message: str | None = None

class FailureAnalysisRequest(BaseModel):
    results: list[FailureInput] = Field(min_length=1)

def _test_to_dict(item) -> dict:
    return {"id": item.id, "name": item.name, "source_path": item.source_path, "framework": item.framework, "runner": item.runner, "suite": item.suite, "tags": item.tags, "metadata": item.metadata}

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/api/v1/discovery")
def discover(request: DiscoverRequest) -> dict:
    try:
        dna = discovery.discover(request.project_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "project_path": dna.project_path, "language": dna.language, "package_manager": dna.package_manager,
        "test_runner": dna.test_runner, "ui_framework": dna.ui_framework, "api_framework": dna.api_framework,
        "database_tools": dna.database_tools, "test_paths": dna.test_paths, "config_files": dna.config_files,
        "dependency_files": dna.dependency_files,
        "capabilities": [{"id": x.id, "name": x.name, "supported": x.supported, "evidence": x.evidence} for x in dna.capabilities],
    }

@app.post("/api/v1/tests/discovery")
def discover_tests(request: DiscoverRequest) -> dict:
    try:
        tests = test_discovery.discover_tests(request.project_path)
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"count": len(tests), "tests": [_test_to_dict(x) for x in tests]}

@app.post("/api/v1/executions")
def execute(request: ExecuteRequest) -> dict:
    execution = ExecutionRequest(
        request_id=__import__("uuid").uuid4().hex,
        mode=ExecutionMode.SINGLE if len(request.test_ids) == 1 else ExecutionMode.SELECTION,
        target=ExecutionTarget(
            test_ids=request.test_ids,
            project_path=request.project_path,
            runner=request.runner,
        ),
        policy=ExecutionPolicy(
            allow_side_effects=request.authorize_execution,
            timeout_seconds=request.timeout_seconds,
        ),
    )
    try:
        result = execution_service.execute(execution)
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    history_saved = True
    try:
        history_store.save(execution, result)
    except (OSError, sqlite3.Error):
        # The execution result is still returned if local history storage is unavailable.
        history_saved = False
    return {
        "request_id": result.request_id,
        "history_saved": history_saved,
        "status": result.status.value,
        "results": [
            {
                "test_id": item.test_id,
                "outcome": item.outcome.value,
                "duration_seconds": item.duration_seconds,
                "message": item.message,
                "evidence": [
                    {"kind": ref.kind, "location": ref.location, "label": ref.label}
                    for ref in item.evidence
                ],
            }
            for item in result.results
        ],
        "started_at": result.started_at,
        "completed_at": result.completed_at,
        "error": result.error,
        "metadata": result.metadata,
    }


@app.get("/api/v1/executions")
def list_executions(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    try:
        executions = history_store.list_recent(limit)
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503, detail="Execution history is unavailable") from exc
    return {"count": len(executions), "executions": executions}


@app.get("/api/v1/executions/{request_id}")
def get_execution(request_id: str) -> dict:
    try:
        execution = history_store.get(request_id)
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503, detail="Execution history is unavailable") from exc
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution history record not found")
    return execution


@app.post("/api/v1/analysis/failures")
def analyze_failures(request: FailureAnalysisRequest) -> dict:
    analyses = [
        classify_failure(item.test_id, item.outcome, item.message)
        for item in request.results
    ]
    return {
        "analyses": [
            {
                "test_id": item.test_id,
                "category": item.category.value,
                "summary": item.summary,
                "matched_rule": item.matched_rule,
            }
            for item in analyses
        ]
    }


@app.post("/api/v1/adapters/capabilities")
def adapter_capabilities(request: DiscoverRequest) -> dict:
    try:
        capabilities = test_discovery.capabilities(request.project_path)
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"capabilities": [{"id": x.id, "name": x.name, "supported": x.supported, "description": x.description} for x in capabilities]}
