from abc import ABC, abstractmethod
from aac.domain.models import AdapterCapability, DiscoveredTest, FrameworkDNA

class FrameworkAdapter(ABC):
    name: str

    @abstractmethod
    def can_handle(self, dna: FrameworkDNA) -> bool:
        pass

    @abstractmethod
    def capabilities(self) -> list[AdapterCapability]:
        pass

    @abstractmethod
    def discover_tests(self, project_path: str, dna: FrameworkDNA) -> list[DiscoveredTest]:
        pass
