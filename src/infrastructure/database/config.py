from pydantic import computed_field, PostgresDsn

from src.core.config import BaseSettings


class DatabaseSettings(BaseSettings):
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int

    DATABASE_POOL_SIZE: int = 100
    DATABASE_POOL_OVERFLOW: int = 25

    @computed_field(alias="DATABASE_URI")
    def database_uri(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme=f"postgresql+asyncpg",
            username=self.DATABASE_USER,
            password=self.DATABASE_PASSWORD,
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            path=f"{self.DATABASE_NAME}",
        )
