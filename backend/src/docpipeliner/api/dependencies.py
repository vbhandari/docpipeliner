"""FastAPI dependencies for dependency injection."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from docpipeliner.config import Settings, get_settings
from docpipeliner.ocr.manager import OCREngineManager
from docpipeliner.ocr.tesseract import TesseractEngine
from docpipeliner.storage.r2 import R2StorageClient
from docpipeliner.storage.supabase import SupabaseClient


def get_settings_dep() -> Settings:
    """Get application settings."""
    return get_settings()


@lru_cache
def get_r2_client() -> R2StorageClient:
    """Get R2 storage client (singleton)."""
    return R2StorageClient()


@lru_cache
def get_supabase_client() -> SupabaseClient:
    """Get Supabase client (singleton)."""
    return SupabaseClient()


@lru_cache
def get_ocr_manager() -> OCREngineManager:
    """Get OCR engine manager with registered engines (singleton)."""
    manager = OCREngineManager()

    # Register Tesseract engine
    try:
        tesseract = TesseractEngine()
        manager.register_engine(tesseract)
    except Exception:
        pass  # Tesseract not available

    # Register PaddleOCR engine if available
    try:
        from docpipeliner.ocr.paddle import PaddleOCREngine

        paddle = PaddleOCREngine()
        manager.register_engine(paddle)
    except ImportError:
        pass  # PaddleOCR not installed

    return manager


async def verify_api_key(
    x_api_key: Annotated[str, Header()],
    settings: Settings = Depends(get_settings_dep),
) -> str:
    """Verify API key from request header.

    Args:
        x_api_key: API key from X-API-Key header
        settings: Application settings

    Returns:
        The verified API key

    Raises:
        HTTPException: If API key is invalid
    """
    if not settings.api_keys:
        # No API keys configured, allow all requests (development mode)
        return x_api_key

    if x_api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return x_api_key


# Type aliases for dependency injection
R2Client = Annotated[R2StorageClient, Depends(get_r2_client)]
SupabaseDB = Annotated[SupabaseClient, Depends(get_supabase_client)]
OCRManager = Annotated[OCREngineManager, Depends(get_ocr_manager)]
ApiKey = Annotated[str, Depends(verify_api_key)]
AppSettings = Annotated[Settings, Depends(get_settings_dep)]
