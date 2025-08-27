from sqlalchemy import Column, String, Integer

from src.infrastructure.database.models.base import BaseBigIntegerIdentity


class CdnServer(BaseBigIntegerIdentity):
    __tablename__ = "cdn_server"
    host_name: str = Column(String, nullable=False)
    default_redirecting_ratio: int = Column(Integer, nullable=False)
