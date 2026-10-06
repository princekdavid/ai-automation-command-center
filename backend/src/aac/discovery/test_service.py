from aac.adapters.registry import AdapterRegistry
from aac.discovery.service import DiscoveryService
from aac.domain.models import DiscoveredTest


class TestDiscoveryService:
    """Orchestrates test discovery without executing tests."""

    def __init__(
        self,
        discovery: DiscoveryService | None = None,
        registry: AdapterRegistry | None = None,
    ) -> None:
        self.discovery = discovery or DiscoveryService()
        self.registry = registry or AdapterRegistry()

    def discover_tests(self, project_path: str) -> list[DiscoveredTest]:
        dna = self.discovery.discover(project_path)
        adapter = self.registry.resolve(dna)
        return adapter.discover_tests(project_path, dna)
