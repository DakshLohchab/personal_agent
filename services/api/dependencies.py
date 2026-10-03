"""Configuration and dependency utilities for the API layer."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator

load_dotenv()


def _api_port_from_env() -> int:
    return int(os.getenv("PORT", os.getenv("API_PORT", "8000")))


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "local"))
    api_host: str = Field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = Field(default_factory=_api_port_from_env)
    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    @field_validator("api_port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("api_port must be between 1 and 65535")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise TypeError("cors_origins must be a comma-separated string or list")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_env=os.getenv("APP_ENV", "local"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=_api_port_from_env(),
            cors_origins=cls.parse_cors_origins(
                os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
