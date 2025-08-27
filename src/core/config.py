from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict

from src import APPLICATION_DIR


class BaseSettings(PydanticBaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False, env_file=APPLICATION_DIR / ".env", extra="ignore"
    )
