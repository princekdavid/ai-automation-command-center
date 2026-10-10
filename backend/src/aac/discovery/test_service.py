from aac.adapters.registry import AdapterRegistry
from aac.discovery.service import DiscoveryService
from aac.domain.models import AdapterCapability, DiscoveredTest

class TestDiscoveryService:
    def __init__(self, discovery=None, registry=None) -> None:
        self.discovery = discovery or DiscoveryService()
        self.registry = registry or AdapterRegistry()

    def discover_tests(self, project_path: str) -> list[DiscoveredTest]:
        dna = self.discovery.discover(project_path)
        return self.registry.resolve(dna).discover_tests(project_path, dna)

    def capabilities(self, project_path: str) -> list[AdapterCapability]:
        dna = self.discovery.discover(project_path)
        return self.registry.resolve(dna).capabilities()
