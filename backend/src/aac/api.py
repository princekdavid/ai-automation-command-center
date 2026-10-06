from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from aac.discovery.service import DiscoveryService

app = FastAPI(title="AI Automation Command Center", version="0.1.0")
discovery = DiscoveryService()


class DiscoverRequest(BaseModel):
    project_path: str


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
        "project_path": dna.project_path,
        "language": dna.language,
        "package_manager": dna.package_manager,
        "test_runner": dna.test_runner,
        "ui_framework": dna.ui_framework,
        "api_framework": dna.api_framework,
        "database_tools": dna.database_tools,
        "test_paths": dna.test_paths,
        "config_files": dna.config_files,
        "dependency_files": dna.dependency_files,
        "capabilities": [
            {"id": item.id, "name": item.name, "supported": item.supported, "evidence": item.evidence}
            for item in dna.capabilities
        ],
    }
