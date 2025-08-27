from sqlalchemy import (
    SmallInteger,
    Identity,
    Integer,
    BigInteger,
)
from sqlalchemy.orm import mapped_column, Mapped


class SmallIntegerIdentifierMixin:
    id: Mapped[int] = mapped_column(
        SmallInteger, Identity(always=False), primary_key=True
    )


class IntegerIdentifierMixin:
    id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)


class BigIntegerIdentifierMixin:
    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=False), primary_key=True
    )
