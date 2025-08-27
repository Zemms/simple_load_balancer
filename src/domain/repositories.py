import abc

from src.domain.schemas import CdnSettings


class CdnSettingsRepository(abc.ABC):
    @abc.abstractmethod
    async def create(self, settings: CdnSettings) -> CdnSettings:
        pass

    @abc.abstractmethod
    async def read(self) -> CdnSettings | None:
        pass

    @abc.abstractmethod
    async def update(self, settings: CdnSettings) -> None:
        pass


class CdnRequestCounterRepository(abc.ABC):
    @abc.abstractmethod
    async def increment(self) -> int:
        pass
