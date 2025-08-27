from sqlalchemy import (
    MetaData,
)
from sqlalchemy.orm import DeclarativeBase

from src.infrastructure.database.models.mixins import (
    SmallIntegerIdentifierMixin,
    IntegerIdentifierMixin,
    BigIntegerIdentifierMixin,
)

metadata = MetaData(
    naming_convention={
        "all_column_names": lambda constraint, table: "_".join(
            [column.name for column in constraint.columns.values()]
        ),
        # Именование индексов
        "ix": "ix__%(table_name)s__%(all_column_names)s",
        # Именование уникальных индексов
        "uq": "uq__%(table_name)s__%(all_column_names)s",
        # Именование CHECK-constraint-ов
        "ck": "ck__%(table_name)s__%(constraint_name)s",
        # Именование внешних ключей
        "fk": "fk_%(table_name)s_%(all_column_names)s",
        # Именование первичных ключей
        "pk": "%(table_name)s_pkey",
    }
)


class Base(DeclarativeBase):
    metadata = metadata

    def to_dict(self, exclude: set[str] = None) -> dict:
        data = {}

        for column in self.__table__.columns.keys():
            if exclude and column in exclude:
                continue
            data[column] = getattr(self, column)

        return data


class BaseSmallIntegerIdentity(Base, SmallIntegerIdentifierMixin):
    """
    Базовый абстрактный класс модели для последовательности (int2)
    """

    __abstract__ = True


class BaseIntegerIdentity(Base, IntegerIdentifierMixin):
    """
    Базовый абстрактный класс модели для последовательности (int4)
    """

    __abstract__ = True


class BaseBigIntegerIdentity(Base, BigIntegerIdentifierMixin):
    """
    Базовый абстрактный класс модели для последовательности (int8)
    """

    __abstract__ = True
