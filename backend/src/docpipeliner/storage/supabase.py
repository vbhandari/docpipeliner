"""Supabase database client."""

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from supabase import Client, create_client

from docpipeliner.config import get_settings
from docpipeliner.models.document import Document, DocumentCreate, DocumentStatus, DocumentType
from docpipeliner.models.extraction import ExtractionResult, ExtractionResultCreate
from docpipeliner.models.review import ReviewTask, ReviewTaskCreate, ReviewTaskStatus

logger = logging.getLogger(__name__)


class SupabaseError(Exception):
    """Exception raised by Supabase operations."""

    pass


class SupabaseClient:
    """Client for Supabase PostgreSQL database.

    Provides methods for CRUD operations on documents,
    extraction results, and review tasks.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
    ):
        """Initialize Supabase client.

        Args:
            url: Supabase project URL (default: from settings)
            key: Supabase service key (default: from settings)
        """
        settings = get_settings()

        self._url = url or settings.supabase_url
        self._key = key or settings.supabase_service_key

        if not self._url or not self._key:
            logger.warning("Supabase credentials not configured")
            self._client: Optional[Client] = None
        else:
            self._client = create_client(self._url, self._key)

    def _ensure_client(self) -> Client:
        """Ensure client is initialized."""
        if self._client is None:
            raise SupabaseError("Supabase client not initialized. Check credentials.")
        return self._client

    # Document operations

    async def create_document(self, document: DocumentCreate, storage_path: str) -> Document:
        """Create a new document record.

        Args:
            document: Document creation data
            storage_path: R2 storage path

        Returns:
            Created Document

        Raises:
            SupabaseError: If creation fails
        """
        client = self._ensure_client()

        try:
            data = {
                "filename": document.filename,
                "document_type": document.document_type.value,
                "storage_path": storage_path,
                "status": DocumentStatus.UPLOADED.value,
                "metadata": document.metadata,
            }

            result = client.table("documents").insert(data).execute()

            if not result.data:
                raise SupabaseError("Failed to create document")

            return self._parse_document(result.data[0])

        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise SupabaseError(f"Failed to create document: {e}") from e

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get a document by ID.

        Args:
            document_id: Document UUID

        Returns:
            Document or None if not found
        """
        client = self._ensure_client()

        try:
            result = (
                client.table("documents")
                .select("*")
                .eq("id", str(document_id))
                .execute()
            )

            if not result.data:
                return None

            return self._parse_document(result.data[0])

        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            raise SupabaseError(f"Failed to get document: {e}") from e

    async def update_document_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        error_message: Optional[str] = None,
    ) -> Document:
        """Update document status.

        Args:
            document_id: Document UUID
            status: New status
            error_message: Optional error message (for FAILED status)

        Returns:
            Updated Document

        Raises:
            SupabaseError: If update fails
        """
        client = self._ensure_client()

        try:
            data: dict[str, Any] = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
            }

            if error_message:
                data["error_message"] = error_message

            result = (
                client.table("documents")
                .update(data)
                .eq("id", str(document_id))
                .execute()
            )

            if not result.data:
                raise SupabaseError(f"Document {document_id} not found")

            return self._parse_document(result.data[0])

        except Exception as e:
            logger.error(f"Failed to update document status: {e}")
            raise SupabaseError(f"Failed to update document status: {e}") from e

    async def list_documents(
        self,
        status: Optional[DocumentStatus] = None,
        document_type: Optional[DocumentType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """List documents with optional filters.

        Args:
            status: Filter by status
            document_type: Filter by document type
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of Documents
        """
        client = self._ensure_client()

        try:
            query = client.table("documents").select("*")

            if status:
                query = query.eq("status", status.value)
            if document_type:
                query = query.eq("document_type", document_type.value)

            result = (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return [self._parse_document(row) for row in result.data]

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise SupabaseError(f"Failed to list documents: {e}") from e

    async def delete_document(self, document_id: UUID) -> None:
        """Delete a document.

        Args:
            document_id: Document UUID

        Raises:
            SupabaseError: If deletion fails
        """
        client = self._ensure_client()

        try:
            client.table("documents").delete().eq("id", str(document_id)).execute()
            logger.info(f"Deleted document: {document_id}")

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise SupabaseError(f"Failed to delete document: {e}") from e

    # Extraction result operations

    async def create_extraction_result(
        self,
        extraction: ExtractionResultCreate,
    ) -> ExtractionResult:
        """Create an extraction result record.

        Args:
            extraction: Extraction result data

        Returns:
            Created ExtractionResult

        Raises:
            SupabaseError: If creation fails
        """
        client = self._ensure_client()

        try:
            data = {
                "document_id": str(extraction.document_id),
                "document_type": extraction.document_type.value,
                "extractor_version": extraction.extractor_version,
                "fields": [f.model_dump() for f in extraction.fields],
                "overall_confidence": extraction.overall_confidence,
                "validation_status": extraction.validation_status.value,
                "validation_errors": [e.model_dump() for e in extraction.validation_errors],
                "raw_ocr_text": extraction.raw_ocr_text,
                "processing_metadata": extraction.processing_metadata,
            }

            result = client.table("extraction_results").insert(data).execute()

            if not result.data:
                raise SupabaseError("Failed to create extraction result")

            return self._parse_extraction_result(result.data[0])

        except Exception as e:
            logger.error(f"Failed to create extraction result: {e}")
            raise SupabaseError(f"Failed to create extraction result: {e}") from e

    async def get_extraction_result(
        self,
        document_id: UUID,
    ) -> Optional[ExtractionResult]:
        """Get extraction result for a document.

        Args:
            document_id: Document UUID

        Returns:
            ExtractionResult or None if not found
        """
        client = self._ensure_client()

        try:
            result = (
                client.table("extraction_results")
                .select("*")
                .eq("document_id", str(document_id))
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not result.data:
                return None

            return self._parse_extraction_result(result.data[0])

        except Exception as e:
            logger.error(f"Failed to get extraction result: {e}")
            raise SupabaseError(f"Failed to get extraction result: {e}") from e

    # Review task operations

    async def create_review_task(self, task: ReviewTaskCreate) -> ReviewTask:
        """Create a review task.

        Args:
            task: Review task data

        Returns:
            Created ReviewTask

        Raises:
            SupabaseError: If creation fails
        """
        client = self._ensure_client()

        try:
            data = {
                "document_id": str(task.document_id),
                "priority": task.priority.value,
                "reason": task.reason,
                "flagged_fields": task.flagged_fields,
                "status": ReviewTaskStatus.PENDING.value,
            }

            result = client.table("review_tasks").insert(data).execute()

            if not result.data:
                raise SupabaseError("Failed to create review task")

            return self._parse_review_task(result.data[0])

        except Exception as e:
            logger.error(f"Failed to create review task: {e}")
            raise SupabaseError(f"Failed to create review task: {e}") from e

    async def get_review_tasks(
        self,
        status: Optional[ReviewTaskStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReviewTask]:
        """List review tasks.

        Args:
            status: Filter by status
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of ReviewTasks
        """
        client = self._ensure_client()

        try:
            query = client.table("review_tasks").select("*")

            if status:
                query = query.eq("status", status.value)

            result = (
                query.order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            return [self._parse_review_task(row) for row in result.data]

        except Exception as e:
            logger.error(f"Failed to list review tasks: {e}")
            raise SupabaseError(f"Failed to list review tasks: {e}") from e

    # Helper methods

    def _parse_document(self, data: dict[str, Any]) -> Document:
        """Parse document data from database."""
        return Document(
            id=UUID(data["id"]),
            filename=data["filename"],
            document_type=DocumentType(data["document_type"]),
            storage_path=data["storage_path"],
            status=DocumentStatus(data["status"]),
            metadata=data.get("metadata", {}),
            page_count=data.get("page_count"),
            file_size_bytes=data.get("file_size_bytes"),
            error_message=data.get("error_message"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
        )

    def _parse_extraction_result(self, data: dict[str, Any]) -> ExtractionResult:
        """Parse extraction result data from database."""
        from docpipeliner.models.extraction import (
            ExtractedField,
            ValidationError,
            ValidationStatus,
        )

        return ExtractionResult(
            id=UUID(data["id"]),
            document_id=UUID(data["document_id"]),
            document_type=DocumentType(data["document_type"]),
            extractor_version=data["extractor_version"],
            fields=[ExtractedField(**f) for f in data.get("fields", [])],
            overall_confidence=data["overall_confidence"],
            validation_status=ValidationStatus(data["validation_status"]),
            validation_errors=[ValidationError(**e) for e in data.get("validation_errors", [])],
            raw_ocr_text=data.get("raw_ocr_text"),
            processing_metadata=data.get("processing_metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
        )

    def _parse_review_task(self, data: dict[str, Any]) -> ReviewTask:
        """Parse review task data from database."""
        from docpipeliner.models.review import ReviewTaskPriority

        return ReviewTask(
            id=UUID(data["id"]),
            document_id=UUID(data["document_id"]),
            status=ReviewTaskStatus(data["status"]),
            priority=ReviewTaskPriority(data["priority"]),
            assigned_to=data.get("assigned_to"),
            reason=data.get("reason"),
            flagged_fields=data.get("flagged_fields", []),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            completed_at=(
                datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00"))
                if data.get("completed_at")
                else None
            ),
        )

    async def health_check(self) -> bool:
        """Check if Supabase is accessible.

        Returns:
            True if Supabase is accessible, False otherwise
        """
        try:
            client = self._ensure_client()
            # Simple query to check connection
            client.table("documents").select("id").limit(1).execute()
            return True
        except Exception:
            return False
