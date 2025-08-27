from typing import Generic, Type, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.types import BaseSqaModel


class BaseSqlAlchemyRepository(Generic[BaseSqaModel]):
    _class: Type[BaseSqaModel]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def flush(self, objects: Sequence[BaseSqaModel] | None = None) -> None:
        await self._session.flush(objects)
