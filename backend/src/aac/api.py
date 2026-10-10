from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from aac.discovery.service import DiscoveryService
from aac.discovery.test_service import TestDiscoveryService
from aac.execution.contracts import ExecutionMode, ExecutionPolicy, ExecutionRequest, ExecutionTarget
from aac.execution.service import ExecutionService

app = FastAPI(title="AI Automation Command Center", version="0.1.0")
discovery = DiscoveryService()
test_discovery = TestDiscoveryService(discovery=discovery)
execution_service = ExecutionService(discovery_service=discovery)

class DiscoverRequest(BaseModel):
    project_path: str

class ExecuteRequest(BaseModel):
    project_path: str
    runner: str
    test_ids: list[str] = Field(min_length=1)
    authorize_execution: bool = False
    timeout_seconds: int = Field(default=300, ge=1, le=3600)

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
    return {
        "request_id": result.request_id,
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


@app.post("/api/v1/adapters/capabilities")
def adapter_capabilities(request: DiscoverRequest) -> dict:
    try:
        capabilities = test_discovery.capabilities(request.project_path)
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"capabilities": [{"id": x.id, "name": x.name, "supported": x.supported, "description": x.description} for x in capabilities]}
