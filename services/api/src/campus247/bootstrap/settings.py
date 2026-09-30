from __future__ import annotations

from pathlib import Path
from typing import Literal
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[5]
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Validated environment configuration for Campus 24/7 API service."""

    model_config = SettingsConfigDict(
        env_file=(str(ENV_FILE), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = Field(default="Campus 24/7 API", description="Tên ứng dụng")
    ENVIRONMENT: Literal["development", "testing", "staging", "production"] = Field(
        default="development",
        description="Môi trường triển khai",
    )
    HOST: str = Field(default="127.0.0.1", description="Host lắng nghe")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Port dịch vụ")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://campus247:campus247_local_dev@localhost:5433/campus247_local",
        description="Chuỗi kết nối PostgreSQL pgvector",
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6380/0",
        description="Chuỗi kết nối Redis cache & queue",
    )
    LOG_LEVEL: str = Field(default="INFO", description="Mức ghi log hệ thống")
    DEMO_MODE: bool = Field(
        default=True,
        description="Cờ chế độ thử nghiệm HUCE Demo (dữ liệu tổng hợp)",
    )
    IDENTITY_SECRET_KEY: str = Field(
        default="campus247-demo-secret-key-huce",
        description="Khóa ký danh tính demo",
    )
    CONFIRMATION_SIGNING_KEY: str = Field(
        default="campus247-secret-signing-key",
        description="Khóa ký token xác nhận hành động",
    )
    # LLM Multi-Provider Configurations
    GEMINI_API_KEY: str | None = Field(default=None, description="Khóa API Gemini (Free)")
    OPENAI_API_KEY: str | None = Field(default=None, description="Khóa API OpenAI endpoint")
    OPENAI_BASE_URL: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        description="Base URL endpoint cho OpenAI-compatible API",
    )
    LAB_MODEL: str = Field(default="gemini-3.6-flash", description="Mô hình LLM chính")
    LAB_MINI_MODEL: str = Field(default="gemini-3.6-flash", description="Mô hình LLM nhẹ/mini")
    DEEPSEEK_API_KEY: str | None = Field(default=None, description="Khóa API DeepSeek (Paid)")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com", description="Base URL DeepSeek API")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", description="Mô hình DeepSeek")
    LLM_PRIMARY_PROVIDER: str = Field(default="deepseek", description="Nhà cung cấp LLM chính (deepseek, gemini, auto)")

    _INSECURE_DEFAULTS = frozenset({
        "campus247-demo-secret-key-huce",
        "campus247-secret-signing-key",
    })

    @model_validator(mode="after")
    def _reject_default_keys_in_production(self) -> "Settings":
        """Block startup with default insecure keys in production/staging."""
        if self.ENVIRONMENT in ("production", "staging"):
            for field_name in ("IDENTITY_SECRET_KEY", "CONFIRMATION_SIGNING_KEY"):
                value = getattr(self, field_name, "")
                if value in self._INSECURE_DEFAULTS:
                    raise ValueError(
                        f"{field_name} uses an insecure default value in {self.ENVIRONMENT}. "
                        f"Set a secure secret via environment variable."
                    )
        return self


def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()
