"""Health check endpoints."""

from fastapi import APIRouter, Depends

from docpipeliner.api.dependencies import get_r2_client, get_supabase_client
from docpipeliner.storage.r2 import R2StorageClient
from docpipeliner.storage.supabase import SupabaseClient

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/health/detailed")
async def detailed_health_check(
    r2_client: R2StorageClient = Depends(get_r2_client),
    supabase_client: SupabaseClient = Depends(get_supabase_client),
):
    """Detailed health check with dependency status."""
    r2_healthy = await r2_client.health_check()
    supabase_healthy = await supabase_client.health_check()

    all_healthy = r2_healthy and supabase_healthy

    return {
        "status": "healthy" if all_healthy else "degraded",
        "dependencies": {
            "r2_storage": "healthy" if r2_healthy else "unhealthy",
            "supabase": "healthy" if supabase_healthy else "unhealthy",
        },
    }
