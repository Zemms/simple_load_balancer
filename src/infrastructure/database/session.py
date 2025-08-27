import contextlib
import logging
from asyncio import shield
from functools import lru_cache

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine, async_sessionmaker, AsyncSession,
)

from src.infrastructure.database.config import DatabaseSettings

session_logger = logging.getLogger(__name__)


@lru_cache
def get_async_engine() -> AsyncEngine:
    settings = DatabaseSettings()

    async_engine = create_async_engine(
        url=str(settings.database_uri),
        pool_pre_ping=True,
        pool_size=settings.DATABASE_POOL_SIZE,
        pool_recycle=300,
        pool_timeout=30,
        max_overflow=settings.DATABASE_POOL_OVERFLOW,
    )

    return async_engine


@lru_cache
def get_async_session_maker():
    return async_sessionmaker(
        bind=get_async_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


@contextlib.asynccontextmanager
async def get_async_session():
    async with get_async_session_maker()() as session:
        try:
            yield session

        # Специфичные БД ошибки
        except SQLAlchemyError:
            await session.rollback()
            session_logger.exception('session rollback due to DB exception')
            raise

        # Остальные исключения
        except Exception:
            await session.rollback()
            session_logger.exception('session rollback due to unhandled exception')
            raise

        # Безопасно закрываем сессию
        finally:
            if session:
                session_logger.info("closing session")
                await shield(session.close())
