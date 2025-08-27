import abc
from functools import cached_property


class BaseCrudRepository[Entity](abc.ABC):

    @abc.abstractmethod
    async def create(self, data: Entity) -> int:
        pass

    @abc.abstractmethod
    async def read(self, **filters) -> Entity | None:
        pass

    @abc.abstractmethod
    async def update(self, id_: int | None, data: Entity) -> None:
        pass


class CdnRequestCounterRepository(abc.ABC):

    def __init__(self, server_name: str):
        self._server_name = server_name

    @cached_property
    def counter_key(self):
        return "counter: %s" % self._server_name

    @abc.abstractmethod
    async def increment(self) -> int:
        pass

    @abc.abstractmethod
    async def reset(self) -> None:
        pass
