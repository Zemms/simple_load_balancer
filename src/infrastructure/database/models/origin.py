from sqlalchemy import Column, Integer, String

from src.infrastructure.database.models.base import BaseBigIntegerIdentity


class OriginServer(BaseBigIntegerIdentity):
    __tablename__ = "origin_server"

    name: str = Column(String, nullable=False, unique=True)
    redirecting_ratio: int = Column(Integer, nullable=True)
