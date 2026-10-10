from aac.adapters.base import FrameworkAdapter
from aac.adapters.pytest_adapter import PytestAdapter
from aac.domain.models import FrameworkDNA


class AdapterRegistry:
    def __init__(self, adapters: list[FrameworkAdapter] | None = None) -> None:
        self._adapters = adapters or [PytestAdapter()]

    def resolve(self, dna: FrameworkDNA) -> FrameworkAdapter:
        for adapter in self._adapters:
            if adapter.can_handle(dna):
                return adapter
        raise LookupError(f"No framework adapter available for runner: {dna.test_runner}")
