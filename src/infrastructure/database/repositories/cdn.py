from sqlalchemy import select, update

from src.domain.repositories import CdnSettingsRepository
from src.domain.schemas import CdnSettings as DomainCdnSettings
from src.infrastructure.database.models.settings import CdnSettings as SqlCdnSettings
from src.infrastructure.database.repositories.base import BaseSqlAlchemyRepository


class SqlAlchemyCdnSettingsRepository(CdnSettingsRepository, BaseSqlAlchemyRepository):
    _class = SqlCdnSettings

    async def create(self, settings: DomainCdnSettings):
        self.session.add(self._class(host=settings.host, ratio=settings.ratio))
        await self.session.commit()

    async def read(self) -> DomainCdnSettings | None:
        orm_settings: SqlCdnSettings = await self.session.scalar(select(self._class))

        if not orm_settings:
            return None

        return DomainCdnSettings(**orm_settings.to_dict(exclude={"id"}))

    async def update(self, settings: DomainCdnSettings) -> None:
        await self.session.execute(
            update(self._class).values(host=settings.host, ratio=settings.ratio)
        )
        await self.session.commit()
