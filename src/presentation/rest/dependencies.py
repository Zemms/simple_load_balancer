from functools import lru_cache

from fastapi import Depends, Query
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services import BalancerService
from src.application.strategies import BalancingStrategy, NthRequestStrategy
from src.core.utils import extract_server_name_from_url
from src.domain.repositories import (
    CdnRequestCounterRepository,
    BaseCrudRepository,
)
from src.domain.schemas import CdnServer, OriginServer
from src.infrastructure.cache.config import RedisSettings
from src.infrastructure.cache.repository import (
    RedisCdnRequestCounterRepository,
    CachedCdnServerRepository,
    CachedOriginServerRepository,
)
from src.infrastructure.database.repositories.cdn import SqlAlchemyCdnServerRepository
from src.infrastructure.database.repositories.origin import (
    SqlAlchemyOriginServerRepository,
)
from src.infrastructure.database.session import get_async_session


# Базовые зависимости - клиент Redis и сессия алхимии
@lru_cache
def get_redis_client() -> aioredis.Redis:
    pool = aioredis.ConnectionPool.from_url(
        url=RedisSettings().url, max_connections=100, decode_responses=True
    )

    return aioredis.Redis(connection_pool=pool)


async def get_db_session() -> AsyncSession:
    async with get_async_session() as session:
        yield session


# Зависимости слоя данных для сущности сервера CDN
def get_cdn_persistent_repo(
    session: AsyncSession = Depends(get_db_session),
) -> BaseCrudRepository:
    return SqlAlchemyCdnServerRepository(session)


def get_cached_cdn_repo(
    persistent_repo: BaseCrudRepository[CdnServer] = Depends(get_cdn_persistent_repo),
    redis_client: aioredis.Redis = Depends(get_redis_client),
) -> BaseCrudRepository[CdnServer]:
    return CachedCdnServerRepository(
        persistent_repository=persistent_repo, cache_client=redis_client
    )


# Зависимости слоя данных для сущностей серверов Origin
def extract_server_name(
    video_url: str = Query(...),
) -> str:
    """
    Достаёт из URL значение сервера (если оно существует в заранее известном формате)
    """
    return extract_server_name_from_url(video_url)


def get_origin_persistent_repo(
    session: AsyncSession = Depends(get_db_session),
) -> BaseCrudRepository:
    return SqlAlchemyOriginServerRepository(session)


def get_cached_origin_repo(
    persistent_repo: BaseCrudRepository[OriginServer] = Depends(
        get_origin_persistent_repo
    ),
    redis_client: aioredis.Redis = Depends(get_redis_client),
    server_name: str = Depends(extract_server_name),
) -> BaseCrudRepository[OriginServer]:
    return CachedOriginServerRepository(
        persistent_repository=persistent_repo,
        cache_client=redis_client,
        server_name=server_name,
    )


# Зависимость слоя данных для работы со счётчиком обращений
def get_counter_repo(
    redis: aioredis.Redis = Depends(get_redis_client),
    server_name: str = Depends(extract_server_name),
) -> CdnRequestCounterRepository:
    return RedisCdnRequestCounterRepository(server_name=server_name, client=redis)


# Зависимости слоя сервиса (стратегия балансировки и сервис балансировки)
def get_balancing_strategy(
    cdn_repo: BaseCrudRepository[CdnServer] = Depends(get_cached_cdn_repo),
    origin_repo: BaseCrudRepository[OriginServer] = Depends(get_cached_origin_repo),
    counter_repo: CdnRequestCounterRepository = Depends(get_counter_repo),
) -> BalancingStrategy:
    return NthRequestStrategy(
        cdn_repo=cdn_repo, origin_repo=origin_repo, counter_repo=counter_repo
    )


def get_balancer_service(
    strategy: BalancingStrategy = Depends(get_balancing_strategy),
) -> BalancerService:
    return BalancerService(strategy)
