"""Document-related data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types for extraction."""

    INVOICE = "invoice"
    INSURANCE_CLAIM = "insurance_claim"
    COMPLIANCE_FORM = "compliance_form"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    """Document processing status."""

    UPLOADED = "uploaded"
    PREPROCESSING = "preprocessing"
    OCR_PROCESSING = "ocr_processing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    NEEDS_REVIEW = "needs_review"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    FAILED = "failed"


class BoundingBox(BaseModel):
    """Bounding box coordinates for extracted text."""

    x: float = Field(..., description="X coordinate (left)")
    y: float = Field(..., description="Y coordinate (top)")
    width: float = Field(..., ge=0, description="Width of bounding box")
    height: float = Field(..., ge=0, description="Height of bounding box")
    page: int = Field(..., ge=1, description="Page number (1-indexed)")


class PageCreate(BaseModel):
    """Schema for creating a new page record."""

    document_id: UUID
    page_number: int = Field(..., ge=1)
    image_path: str
    classification: Optional[str] = None


class Page(PageCreate):
    """Page model with database fields."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    """Schema for creating a new document."""

    filename: str = Field(..., min_length=1, max_length=255)
    document_type: DocumentType = DocumentType.UNKNOWN
    metadata: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """Document model with all fields."""

    id: UUID = Field(default_factory=uuid4)
    filename: str
    document_type: DocumentType
    storage_path: str
    status: DocumentStatus = DocumentStatus.UPLOADED
    metadata: dict[str, Any] = Field(default_factory=dict)
    page_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """API response schema for document."""

    id: UUID
    filename: str
    document_type: DocumentType
    status: DocumentStatus
    page_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None

    class Config:
        from_attributes = True
