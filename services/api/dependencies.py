"""Configuration and dependency utilities for the API layer."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator

from packages.ports.auth import AuthPrincipal
from packages.ports.object_store import ObjectStore
from packages.ports.research import ResearchProvider
from services.agents.orchestrator import DecisionOrchestrator
from services.application.ai_service import AIService
from services.llm.nebius import NebiusLLMProvider, NebiusSettings
from services.llm.token_harbor import TokenHarborLLMProvider, TokenHarborSettings
from services.storage.r2 import R2ObjectStore, R2Settings

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
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "nebius"))
    r2_account_id: str = Field(default_factory=lambda: os.getenv("R2_ACCOUNT_ID", ""))
    r2_bucket: str = Field(default_factory=lambda: os.getenv("R2_BUCKET", ""))
    r2_access_key_id: str = Field(default_factory=lambda: os.getenv("R2_ACCESS_KEY_ID", ""))
    r2_secret_access_key: str = Field(default_factory=lambda: os.getenv("R2_SECRET_ACCESS_KEY", ""))
    r2_endpoint_url: str = Field(default_factory=lambda: os.getenv("R2_ENDPOINT_URL", ""))
    r2_presign_ttl_seconds: int = Field(
        default_factory=lambda: int(os.getenv("R2_PRESIGN_TTL_SECONDS", "300"))
    )
    r2_max_upload_bytes: int = Field(
        default_factory=lambda: int(os.getenv("R2_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
    )
    nebius_api_key: str = Field(default_factory=lambda: os.getenv("NEBIUS_API_KEY", ""))
    nebius_base_url: str = Field(
        default_factory=lambda: os.getenv(
            "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
        )
    )
    nebius_model: str = Field(
        default_factory=lambda: os.getenv("NEBIUS_MODEL", "nvidia/Nemotron-3_5-Lightning")
    )
    nebius_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("NEBIUS_TIMEOUT_SECONDS", "60"))
    )
    nebius_max_retries: int = Field(
        default_factory=lambda: int(os.getenv("NEBIUS_MAX_RETRIES", "2"))
    )
    tokenharbor_api_key: str = Field(default_factory=lambda: os.getenv("TOKENHARBOR_API_KEY", ""))
    tokenharbor_base_url: str = Field(
        default_factory=lambda: os.getenv("TOKENHARBOR_BASE_URL", "https://tokenharbor.ai/v1")
    )
    tokenharbor_model: str = Field(
        default_factory=lambda: os.getenv("TOKENHARBOR_MODEL", "deepseek-v4.1-flash:free")
    )
    tokenharbor_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("TOKENHARBOR_TIMEOUT_SECONDS", "60"))
    )
    tokenharbor_max_retries: int = Field(
        default_factory=lambda: int(os.getenv("TOKENHARBOR_MAX_RETRIES", "2"))
    )

    @field_validator("api_port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("api_port must be between 1 and 65535")
        return value

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, value: str) -> str:
        if value not in {"nebius", "token_harbor"}:
            raise ValueError(f"unsupported LLM_PROVIDER: {value}")
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
            llm_provider=os.getenv("LLM_PROVIDER", "nebius"),
            r2_account_id=os.getenv("R2_ACCOUNT_ID", ""),
            r2_bucket=os.getenv("R2_BUCKET", ""),
            r2_access_key_id=os.getenv("R2_ACCESS_KEY_ID", ""),
            r2_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY", ""),
            r2_endpoint_url=os.getenv("R2_ENDPOINT_URL", ""),
            r2_presign_ttl_seconds=int(os.getenv("R2_PRESIGN_TTL_SECONDS", "300")),
            r2_max_upload_bytes=int(
                os.getenv("R2_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024))
            ),
            nebius_api_key=os.getenv("NEBIUS_API_KEY", ""),
            nebius_base_url=os.getenv(
                "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
            ),
            nebius_model=os.getenv("NEBIUS_MODEL", "nvidia/Nemotron-3_5-Lightning"),
            nebius_timeout_seconds=float(os.getenv("NEBIUS_TIMEOUT_SECONDS", "60")),
            nebius_max_retries=int(os.getenv("NEBIUS_MAX_RETRIES", "2")),
            tokenharbor_api_key=os.getenv("TOKENHARBOR_API_KEY", ""),
            tokenharbor_base_url=os.getenv("TOKENHARBOR_BASE_URL", "https://tokenharbor.ai/v1"),
            tokenharbor_model=os.getenv("TOKENHARBOR_MODEL", "deepseek-v4.1-flash:free"),
            tokenharbor_timeout_seconds=float(os.getenv("TOKENHARBOR_TIMEOUT_SECONDS", "60")),
            tokenharbor_max_retries=int(os.getenv("TOKENHARBOR_MAX_RETRIES", "2")),
        )

    @property
    def llm_model(self) -> str:
        if self.llm_provider == "nebius":
            return self.nebius_model
        if self.llm_provider == "token_harbor":
            return self.tokenharbor_model
        raise ValueError(f"unsupported LLM_PROVIDER: {self.llm_provider}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


def get_current_principal() -> AuthPrincipal:
    """Resolve the authenticated identity supplied by the host auth integration."""
    raise NotImplementedError("authentication provider integration is required")


@lru_cache(maxsize=1)
def get_object_store() -> ObjectStore:
    settings = get_settings()
    return R2ObjectStore(
        R2Settings(
            account_id=settings.r2_account_id,
            bucket=settings.r2_bucket,
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            endpoint_url=settings.r2_endpoint_url,
            presign_ttl_seconds=settings.r2_presign_ttl_seconds,
            max_upload_bytes=settings.r2_max_upload_bytes,
        )
    )


@lru_cache(maxsize=1)
def get_research_provider() -> ResearchProvider:
    from services.research.tavily import TavilyResearchProvider

    return TavilyResearchProvider(os.getenv("TAVILY_API_KEY", ""))


@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    settings = get_settings()
    if settings.llm_provider == "nebius":
        provider = NebiusLLMProvider(
            NebiusSettings(
                api_key=settings.nebius_api_key,
                base_url=settings.nebius_base_url,
                model=settings.nebius_model,
                timeout_seconds=settings.nebius_timeout_seconds,
                max_retries=settings.nebius_max_retries,
            )
        )
    elif settings.llm_provider == "token_harbor":
        provider = TokenHarborLLMProvider(
            TokenHarborSettings(
                api_key=settings.tokenharbor_api_key,
                base_url=settings.tokenharbor_base_url,
                model=settings.tokenharbor_model,
                timeout_seconds=settings.tokenharbor_timeout_seconds,
                max_retries=settings.tokenharbor_max_retries,
            )
        )
    else:
        raise ValueError(f"unsupported LLM_PROVIDER: {settings.llm_provider}")
    return AIService(
        provider
    )


@lru_cache(maxsize=1)
def get_decision_orchestrator() -> DecisionOrchestrator:
    return DecisionOrchestrator(research_provider=get_research_provider())
