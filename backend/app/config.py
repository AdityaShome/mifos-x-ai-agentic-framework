from functools import lru_cache

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mifos X Portfolio Health Agent"
    environment: str = Field(default="development")
    sqlite_url: str = Field(default="sqlite:///./portfolio_health.db")
    fineract_base_url: str = Field(default="http://localhost:8443/fineract-provider/api/v1")
    fineract_tenant: str = Field(default="default")
    fineract_username: str = Field(default="")
    fineract_password: str = Field(default="")
    fineract_timeout_seconds: float = Field(default=300.0, gt=0)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.1")
    default_autonomy_level: int = Field(default=1, ge=0, le=4)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("fineract_base_url", "ollama_base_url", mode="before")
    @classmethod
    def _default_non_empty_url(cls, value: str | None, info):
        if isinstance(value, str) and value.strip():
            return value.strip()
        defaults = {
            "fineract_base_url": "http://localhost:8443/fineract-provider/api/v1",
            "ollama_base_url": "http://localhost:11434",
        }
        return defaults.get(info.field_name, value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
