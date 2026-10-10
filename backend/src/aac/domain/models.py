from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Capability:
    id: str
    name: str
    supported: bool
    evidence: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class AdapterCapability:
    id: str
    name: str
    supported: bool
    description: str

@dataclass(frozen=True)
class FrameworkDNA:
    project_path: str
    language: str | None
    package_manager: str | None
    test_runner: str | None
    ui_framework: str | None
    api_framework: str | None
    database_tools: list[str]
    test_paths: list[str]
    config_files: list[str]
    dependency_files: list[str]
    capabilities: list[Capability]
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class DiscoveredTest:
    id: str
    name: str
    source_path: str
    framework: str
    runner: str | None
    suite: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
