"""Storage clients for DocPipeliner."""

from docpipeliner.storage.r2 import R2StorageClient
from docpipeliner.storage.supabase import SupabaseClient

__all__ = ["R2StorageClient", "SupabaseClient"]
