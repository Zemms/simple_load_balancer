from sqlalchemy import Column, Integer, String

from src.infrastructure.database.models.base import BaseBigIntegerIdentity


class CdnSettings(BaseBigIntegerIdentity):
    __tablename__ = "cdn_settings"
    host: str = Column(String, nullable=False)
    ratio: int = Column(Integer, nullable=False)
