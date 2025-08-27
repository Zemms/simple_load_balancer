from dataclasses import dataclass

from src.domain.enums import ResourceTypeEnum


@dataclass(slots=True)
class CdnServer:
    host_name: str
    default_redirecting_ratio: int


@dataclass(slots=True)
class OriginServer:
    name: str
    redirecting_ratio: int | None = None


@dataclass(slots=True)
class TargetResource:
    type: ResourceTypeEnum
    url: str
