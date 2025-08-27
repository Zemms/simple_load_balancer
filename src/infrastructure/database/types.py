from typing import TypeVar

from src.infrastructure.database.models.base import (
    Base,
)

# Any SQAlchemy model
BaseSqaModel = TypeVar("BaseSqaModel", bound=Base)
