"""Configuration management for DocPipeliner."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "DocPipeliner"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # API Configuration
    api_prefix: str = "/api/v1"
    api_key_header: str = "X-API-Key"
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # Cloudflare R2
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "docpipeliner-documents"
    r2_endpoint_url: str = ""

    # Cloudflare Queues
    cf_queue_url: str = ""
    cf_queue_api_token: str = ""

    # OCR Configuration
    tesseract_path: str = "/usr/bin/tesseract"
    tesseract_lang: str = "eng"
    paddleocr_use_gpu: bool = False
    paddleocr_lang: str = "en"

    # Processing Configuration
    confidence_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    max_file_size_mb: int = Field(default=50, ge=1, le=500)
    max_pages_per_document: int = Field(default=100, ge=1, le=1000)
    image_dpi: int = Field(default=300, ge=72, le=600)

    # API Keys (for MVP authentication)
    api_keys: list[str] = Field(default_factory=list)

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def r2_endpoint(self) -> str:
        """Get R2 endpoint URL."""
        if self.r2_endpoint_url:
            return self.r2_endpoint_url
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
