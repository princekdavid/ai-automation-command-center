from abc import ABC, abstractmethod

from aac.domain.models import DiscoveredTest, FrameworkDNA


class FrameworkAdapter(ABC):
    """Framework-neutral contract implemented by framework-specific adapters."""

    name: str

    @abstractmethod
    def can_handle(self, dna: FrameworkDNA) -> bool:
        """Return whether this adapter can handle the discovered framework."""

    @abstractmethod
    def discover_tests(self, project_path: str, dna: FrameworkDNA) -> list[DiscoveredTest]:
        """Discover tests without executing or mutating the project."""
