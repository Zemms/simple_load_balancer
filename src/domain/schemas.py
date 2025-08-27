from dataclasses import dataclass

from src.domain.enums import ResourceTypeEnum


@dataclass(slots=True)
class CdnSettings:
    host: str
    ratio: int


@dataclass(slots=True)
class TargetResource:
    type: ResourceTypeEnum
    url: str
