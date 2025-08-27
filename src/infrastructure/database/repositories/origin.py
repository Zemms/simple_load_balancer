from sqlalchemy import select, update

from src.domain.repositories import BaseCrudRepository
from src.domain.schemas import OriginServer as DomainOriginServer
from src.infrastructure.database.models.origin import OriginServer as OrmOriginServer
from src.infrastructure.database.repositories.base import BaseSqlAlchemyRepository


class SqlAlchemyOriginServerRepository(
    BaseCrudRepository[DomainOriginServer], BaseSqlAlchemyRepository
):
    _class = OrmOriginServer

    async def create(self, data: DomainOriginServer) -> int:
        orm_origin = self._class(
            name=data.name,
            redirecting_ratio=data.redirecting_ratio,
        )
        self.session.add(orm_origin)
        await self.session.commit()
        return orm_origin.id

    async def read(self, **filters) -> DomainOriginServer | None:
        stmt = select(self._class)

        if filters:
            stmt = stmt.filter_by(**filters)

        orm_settings: OrmOriginServer = await self.session.scalar(stmt)

        if not orm_settings:
            return None

        return DomainOriginServer(**orm_settings.to_dict(exclude={"id"}))

    async def update(self, id_: int | None, data: DomainOriginServer) -> None:
        stmt = update(self._class).values(
            name=data.name,
            redirecting_ratio=data.redirecting_ratio,
        )

        if id_ is not None:
            stmt = stmt.filter_by(id=id_)

        await self.session.execute(stmt)
        await self.session.commit()
