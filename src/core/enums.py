from enum import Enum
from typing import Any


class AutoStrEnum(str, Enum):
    @staticmethod
    def _generate_next_value_(
            name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return name
