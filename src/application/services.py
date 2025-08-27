from src.domain.schemas import TargetResource

from .strategies import BalancingStrategy


class BalancerService:
    def __init__(self, strategy: BalancingStrategy):
        self._strategy = strategy

    async def get_redirect_address(self, source_address: str) -> TargetResource:
        return await self._strategy.get_target_resource(source_address)
