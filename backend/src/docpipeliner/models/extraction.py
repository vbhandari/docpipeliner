"""Extraction-related data models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from docpipeliner.models.document import BoundingBox, DocumentType


class ValidationStatus(str, Enum):
    """Validation status for extraction results."""

    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REVIEW = "needs_review"


class ValidationError(BaseModel):
    """Validation error details."""

    field_name: str
    error_type: str = Field(..., description="Type of error (e.g., 'missing', 'format', 'confidence')")
    message: str
    severity: str = Field(default="error", description="Severity level: 'error', 'warning', 'info'")


class ExtractedField(BaseModel):
    """Individual extracted field from a document."""

    field_name: str
    field_value: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: Optional[BoundingBox] = None
    source_engine: str = Field(..., description="OCR engine that produced this extraction")
    normalized_value: Optional[Any] = Field(
        default=None, description="Normalized/parsed value (e.g., date object, decimal)"
    )


class ExtractionResultCreate(BaseModel):
    """Schema for creating an extraction result."""

    document_id: UUID
    document_type: DocumentType
    extractor_version: str = Field(default="1.0.0")
    fields: list[ExtractedField] = Field(default_factory=list)
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    validation_status: ValidationStatus = ValidationStatus.NEEDS_REVIEW
    validation_errors: list[ValidationError] = Field(default_factory=list)
    raw_ocr_text: Optional[str] = None
    processing_metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(ExtractionResultCreate):
    """Extraction result model with database fields."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

    def get_field(self, field_name: str) -> Optional[ExtractedField]:
        """Get a specific field by name."""
        for field in self.fields:
            if field.field_name == field_name:
                return field
        return None

    def get_field_value(self, field_name: str, default: Any = None) -> Any:
        """Get a field's value by name, with optional default."""
        field = self.get_field(field_name)
        return field.field_value if field else default


class ExtractionResultResponse(BaseModel):
    """API response schema for extraction results."""

    document_id: UUID
    document_type: DocumentType
    status: str
    overall_confidence: float
    fields: list[ExtractedField]
    validation_status: ValidationStatus
    validation_errors: list[ValidationError]
    ocr_engines_used: list[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
