"""Document API endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from docpipeliner.api.dependencies import ApiKey, AppSettings, R2Client, SupabaseDB
from docpipeliner.models.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentStatus,
    DocumentType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(default=DocumentType.UNKNOWN),
    metadata: Optional[str] = Form(default=None),
    api_key: str = ApiKey,
    settings: AppSettings = None,
    r2_client: R2Client = None,
    supabase_client: SupabaseDB = None,
):
    """Upload a new document for processing.

    Args:
        file: PDF file to upload
        document_type: Type of document (invoice, insurance_claim, compliance_form)
        metadata: Optional JSON metadata string
        api_key: API key for authentication
        settings: Application settings
        r2_client: R2 storage client
        supabase_client: Supabase database client

    Returns:
        Created document details

    Raises:
        HTTPException: If file validation fails
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Validate file size
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum of {settings.max_file_size_mb}MB",
        )

    # Parse metadata
    import json

    parsed_metadata = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata JSON",
            )

    # Create document record
    document_create = DocumentCreate(
        filename=file.filename,
        document_type=document_type,
        metadata=parsed_metadata,
    )

    try:
        # Upload to R2
        from io import BytesIO

        file_stream = BytesIO(file_content)

        # Create document in database first to get ID
        document = await supabase_client.create_document(
            document_create,
            storage_path="",  # Will be updated after upload
        )

        # Upload to R2 with document ID
        storage_path = await r2_client.upload_document(
            document_id=document.id,
            filename=file.filename,
            file_data=file_stream,
            content_type="application/pdf",
        )

        # Update document with storage path and file size
        document.storage_path = storage_path
        document.file_size_bytes = file_size

        # Estimate completion time (2 minutes for processing)
        estimated_completion = datetime.utcnow() + timedelta(minutes=2)

        logger.info(f"Document uploaded: {document.id}")

        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            document_type=document.document_type,
            status=document.status,
            page_count=document.page_count,
            file_size_bytes=file_size,
            metadata=document.metadata,
            error_message=document.error_message,
            created_at=document.created_at,
            updated_at=document.updated_at,
            estimated_completion=estimated_completion,
        )

    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}",
        )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    status_filter: Optional[DocumentStatus] = None,
    document_type: Optional[DocumentType] = None,
    limit: int = 100,
    offset: int = 0,
    api_key: str = ApiKey,
    supabase_client: SupabaseDB = None,
):
    """List documents with optional filters.

    Args:
        status_filter: Filter by document status
        document_type: Filter by document type
        limit: Maximum number of results (default: 100)
        offset: Offset for pagination
        api_key: API key for authentication
        supabase_client: Supabase database client

    Returns:
        List of documents
    """
    try:
        documents = await supabase_client.list_documents(
            status=status_filter,
            document_type=document_type,
            limit=limit,
            offset=offset,
        )

        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                document_type=doc.document_type,
                status=doc.status,
                page_count=doc.page_count,
                file_size_bytes=doc.file_size_bytes,
                metadata=doc.metadata,
                error_message=doc.error_message,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            for doc in documents
        ]

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    api_key: str = ApiKey,
    supabase_client: SupabaseDB = None,
):
    """Get document details by ID.

    Args:
        document_id: Document UUID
        api_key: API key for authentication
        supabase_client: Supabase database client

    Returns:
        Document details

    Raises:
        HTTPException: If document not found
    """
    try:
        document = await supabase_client.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            document_type=document.document_type,
            status=document.status,
            page_count=document.page_count,
            file_size_bytes=document.file_size_bytes,
            metadata=document.metadata,
            error_message=document.error_message,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}",
        )


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: UUID,
    api_key: str = ApiKey,
    supabase_client: SupabaseDB = None,
):
    """Get document processing status.

    Args:
        document_id: Document UUID
        api_key: API key for authentication
        supabase_client: Supabase database client

    Returns:
        Document status information
    """
    try:
        document = await supabase_client.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        return {
            "document_id": document.id,
            "status": document.status,
            "error_message": document.error_message,
            "updated_at": document.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document status: {str(e)}",
        )


@router.get("/{document_id}/results")
async def get_document_results(
    document_id: UUID,
    api_key: str = ApiKey,
    supabase_client: SupabaseDB = None,
):
    """Get extraction results for a document.

    Args:
        document_id: Document UUID
        api_key: API key for authentication
        supabase_client: Supabase database client

    Returns:
        Extraction results

    Raises:
        HTTPException: If document not found or results not available
    """
    try:
        document = await supabase_client.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        if document.status not in [DocumentStatus.COMPLETED, DocumentStatus.NEEDS_REVIEW]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Results not available. Document status: {document.status}",
            )

        extraction = await supabase_client.get_extraction_result(document_id)

        if not extraction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extraction results not found",
            )

        return {
            "document_id": extraction.document_id,
            "document_type": extraction.document_type,
            "status": document.status,
            "overall_confidence": extraction.overall_confidence,
            "fields": [f.model_dump() for f in extraction.fields],
            "validation_status": extraction.validation_status,
            "validation_errors": [e.model_dump() for e in extraction.validation_errors],
            "created_at": extraction.created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document results: {str(e)}",
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    api_key: str = ApiKey,
    r2_client: R2Client = None,
    supabase_client: SupabaseDB = None,
):
    """Delete a document and its associated files.

    Args:
        document_id: Document UUID
        api_key: API key for authentication
        r2_client: R2 storage client
        supabase_client: Supabase database client

    Raises:
        HTTPException: If document not found
    """
    try:
        document = await supabase_client.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        # Delete from R2
        await r2_client.delete_document_folder(document_id)

        # Delete from database
        await supabase_client.delete_document(document_id)

        logger.info(f"Document deleted: {document_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )
