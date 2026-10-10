from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from aac.discovery.service import DiscoveryService
from aac.discovery.test_service import TestDiscoveryService

app = FastAPI(title="AI Automation Command Center", version="0.1.0")
discovery = DiscoveryService()
test_discovery = TestDiscoveryService(discovery=discovery)

class DiscoverRequest(BaseModel):
    project_path: str

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

@app.post("/api/v1/adapters/capabilities")
def adapter_capabilities(request: DiscoverRequest) -> dict:
    try:
        capabilities = test_discovery.capabilities(request.project_path)
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"capabilities": [{"id": x.id, "name": x.name, "supported": x.supported, "description": x.description} for x in capabilities]}
