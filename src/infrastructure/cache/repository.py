import json
from dataclasses import asdict

from redis import asyncio as aioredis

from src.domain.repositories import CdnRequestCounterRepository, CdnSettingsRepository
from src.domain.schemas import CdnSettings as DomainCdnSettings

COUNTER_KEY: str = "cdn_request_counter"
CACHE_KEY = "CDN_SETTINGS"
CACHE_TTL_SECONDS = 60


class RedisCdnRequestCounterRepository(CdnRequestCounterRepository):
    def __init__(self, client: aioredis.Redis):
        self._client = client

    # implement
    async def increment(self) -> int:
        return await self._client.incr(COUNTER_KEY)


# TODO: вероятно, с кешированием результатов можно сделать что-то более красивое и универсальное,
#   пока на скорую руку так
class CachedCdnSettingsRepository(CdnSettingsRepository):

    def __init__(
        self,
        persistent_repository: CdnSettingsRepository,
        cache_client: aioredis.Redis,
    ) -> None:
        self._cache_client = cache_client
        self._persistent_repository = persistent_repository

    async def create(self, domain: DomainCdnSettings) -> None:
        await self._persistent_repository.create(domain)

    async def read(self) -> DomainCdnSettings | None:
        cache_healthy: bool = True

        # Пытаемся забрать из кеша
        try:
            cached_settings = await self._cache_client.get(CACHE_KEY)

            if cached_settings is not None:
                return DomainCdnSettings(**json.loads(cached_settings))

        except aioredis.RedisError:
            cache_healthy = False

        # Получаем из базы (если кеш пуст или отвалился)
        orm_settings = await self._persistent_repository.read()

        # Кладём в кеш, если что-то нашли и кеш живой
        if orm_settings is not None and cache_healthy:
            try:
                await self._cache_client.set(
                    CACHE_KEY, json.dumps(asdict(orm_settings))
                )
            except aioredis.RedisError:
                pass

        return orm_settings

    async def update(self, settings: DomainCdnSettings) -> None:
        await self._persistent_repository.update(settings)
        await self._cache_client.set(CACHE_KEY, json.dumps(asdict(settings)))
