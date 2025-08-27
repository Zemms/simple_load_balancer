from sqlalchemy import select, update

from src.domain.repositories import BaseCrudRepository
from src.domain.schemas import CdnServer as DomainCdnServer
from src.infrastructure.database.models.cdn import CdnServer
from src.infrastructure.database.repositories.base import BaseSqlAlchemyRepository


class SqlAlchemyCdnServerRepository(
    BaseCrudRepository[DomainCdnServer], BaseSqlAlchemyRepository
):
    _class = CdnServer

    async def create(self, data: DomainCdnServer):
        self.session.add(
            self._class(
                host_name=data.host_name,
                default_redirecting_ratio=data.default_redirecting_ratio,
            )
        )
        await self.commit()

    async def read(self, **filters) -> DomainCdnServer | None:
        stmt = select(self._class)

        if filters:
            stmt = stmt.filter_by(**filters)

        orm_settings: CdnServer = await self.session.scalar(stmt)

        if not orm_settings:
            return None

        return DomainCdnServer(**orm_settings.to_dict(exclude={"id"}))

    async def update(self, id_: int | None, data: DomainCdnServer) -> None:
        stmt = update(self._class).values(
            host_name=data.host_name,
            default_redirecting_ratio=data.default_redirecting_ratio,
        )

        if id_ is not None:
            stmt = stmt.filter_by(id=id_)

        await self.session.execute(stmt)
        await self.commit()
