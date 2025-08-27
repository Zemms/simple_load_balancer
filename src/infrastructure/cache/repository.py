import json
from dataclasses import asdict

from redis import asyncio as aioredis

from src.domain.repositories import CdnRequestCounterRepository, BaseCrudRepository
from src.domain.schemas import (
    CdnServer as DomainCdnServer,
    OriginServer as DomainOriginServer,
)


class RedisCdnRequestCounterRepository(CdnRequestCounterRepository):
    def __init__(self, server_name: str, client: aioredis.Redis):
        super().__init__(server_name)
        self._client = client

    async def increment(self) -> int:
        return await self._client.incr(self.counter_key)

    async def reset(self) -> None:
        return await self._client.delete(self.counter_key)


# TODO: тут прям совсем сырой дублирующийся код, по идее можно обобщить, но на это нужно время :)
class CachedCdnServerRepository(BaseCrudRepository[DomainCdnServer]):

    def __init__(
        self,
        persistent_repository: BaseCrudRepository[DomainCdnServer],
        cache_client: aioredis.Redis,
    ) -> None:
        self._cache_client = cache_client
        self._persistent_repository = persistent_repository

    async def create(self, data: DomainCdnServer) -> int:
        return await self._persistent_repository.create(data)

    async def update(self, id_: int, data: DomainCdnServer) -> None:
        await self._persistent_repository.update(id_=id_, data=data)
        await self._cache_client.set("CDN_SERVER", json.dumps(asdict(data)))

    async def read(self, **filters) -> DomainCdnServer | None:
        cache_healthy: bool = True

        # Пытаемся забрать из кеша
        try:
            cached_settings = await self._cache_client.get("CDN_SERVER")

            if cached_settings is not None:
                return DomainCdnServer(**json.loads(cached_settings))

        except aioredis.RedisError:
            cache_healthy = False

        # Получаем из базы (если кеш пуст или отвалился)
        orm_settings = await self._persistent_repository.read(**filters)

        # Кладём в кеш, если что-то нашли и кеш живой
        if orm_settings is not None and cache_healthy:
            try:
                await self._cache_client.set(
                    "CDN_SERVER", json.dumps(asdict(orm_settings))
                )
            except aioredis.RedisError:
                pass

        return orm_settings


class CachedOriginServerRepository(BaseCrudRepository[DomainOriginServer]):

    def __init__(
        self,
        persistent_repository: BaseCrudRepository[DomainOriginServer],
        server_name: str,
        cache_client: aioredis.Redis,
    ) -> None:
        self._server_name = server_name
        self._cache_client = cache_client
        self._persistent_repository = persistent_repository

    @property
    def server_name(self) -> str:
        return "server: %s" % self._server_name

    async def create(self, data: DomainOriginServer) -> None:
        await self._persistent_repository.create(data)

    async def update(self, id_: int, data: DomainOriginServer) -> None:
        await self._persistent_repository.update(id_, data)
        await self._cache_client.set(self.server_name, json.dumps(asdict(data)))

    async def read(self, **filters) -> DomainOriginServer | None:
        cache_healthy: bool = True

        # Пытаемся забрать из кеша
        try:
            cached_settings = await self._cache_client.get(self.server_name)

            if cached_settings is not None:
                return DomainOriginServer(**json.loads(cached_settings))

        except aioredis.RedisError:
            cache_healthy = False

        # Получаем из базы (если кеш пуст или отвалился)
        orm_settings = await self._persistent_repository.read(**filters)

        # Кладём в кеш, если что-то нашли и кеш живой
        if orm_settings is not None and cache_healthy:
            try:
                await self._cache_client.set(
                    self.server_name, json.dumps(asdict(orm_settings))
                )
            except aioredis.RedisError:
                pass

        return orm_settings
