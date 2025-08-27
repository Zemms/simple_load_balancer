from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis import asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.database.models.base import Base
from src.infrastructure.database.session import get_async_session, get_async_engine
from .presentation.rest.api import root_router
from .presentation.rest.dependencies import get_redis_client


async def _check_db_connection():
    try:
        async with get_async_session() as session:
            await session.execute(text("SELECT 1"))
    except SQLAlchemyError as ex:
        print("db connection error: %s" % ex)
        raise


async def _check_redis_connection():
    try:
        await get_redis_client().ping()
    except aioredis.RedisError as ex:
        print(f"redis connection error: %s" % ex)
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Проверяем базовые подключения
    await _check_db_connection()
    await _check_redis_connection()

    # Создаем таблицы в БД
    async with get_async_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Закрываем соединение с redis
    await get_redis_client().close()


def create_application() -> FastAPI:
    application = FastAPI(
        title="Video Traffic Balancer",
        description="Сервис для балансировки трафика видео.",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.include_router(root_router)
    return application


fastapi_instance = create_application()
