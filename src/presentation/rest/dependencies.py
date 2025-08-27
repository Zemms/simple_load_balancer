from fastapi import Depends
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services import BalancerService
from src.application.strategies import BalancingStrategy, NthRequestStrategy
from src.domain.repositories import CdnSettingsRepository, CdnRequestCounterRepository
from src.infrastructure.cache.config import RedisSettings
from src.infrastructure.cache.repository import (
    CachedCdnSettingsRepository,
    RedisCdnRequestCounterRepository,
)
from src.infrastructure.database.repositories.cdn import SqlAlchemyCdnSettingsRepository
from src.infrastructure.database.session import get_async_session

_redis_instance = None


def get_redis_client() -> aioredis.Redis:
    global _redis_instance

    if _redis_instance is None:
        _redis_instance = aioredis.Redis.from_url(
            url=RedisSettings().url, decode_responses=True
        )

    return _redis_instance


async def get_db_session() -> AsyncSession:
    async with get_async_session() as session:
        yield session


def get_settings_repo(
    session: AsyncSession = Depends(get_db_session),
) -> CdnSettingsRepository:
    return SqlAlchemyCdnSettingsRepository(session)


def get_cached_settings_repo(
    redis_client: aioredis.Redis = Depends(get_redis_client),
) -> CdnSettingsRepository:
    return CachedCdnSettingsRepository(redis_client)


def get_counter_repo(
    redis: aioredis.Redis = Depends(get_redis_client),
) -> CdnRequestCounterRepository:
    return RedisCdnRequestCounterRepository(redis)


def get_balancing_strategy(
    settings_repo: CdnSettingsRepository = Depends(get_settings_repo),
    counter_repo: CdnRequestCounterRepository = Depends(get_counter_repo),
) -> BalancingStrategy:
    return NthRequestStrategy(settings_repo, counter_repo)


def get_balancer_service(
    strategy: BalancingStrategy = Depends(get_balancing_strategy),
) -> BalancerService:
    return BalancerService(strategy)
