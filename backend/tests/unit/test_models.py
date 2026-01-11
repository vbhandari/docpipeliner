"""Unit tests for data models."""

import pytest
from uuid import uuid4

from docpipeliner.models.document import (
    BoundingBox,
    Document,
    DocumentCreate,
    DocumentStatus,
    DocumentType,
)
from docpipeliner.models.extraction import (
    ExtractedField,
    ExtractionResult,
    ValidationError,
    ValidationStatus,
)


class TestDocumentModels:
    """Tests for document-related models."""

    def test_document_create(self):
        """Test DocumentCreate model creation."""
        doc = DocumentCreate(
            filename="test.pdf",
            document_type=DocumentType.INVOICE,
            metadata={"source": "email"},
        )
        assert doc.filename == "test.pdf"
        assert doc.document_type == DocumentType.INVOICE
        assert doc.metadata == {"source": "email"}

    def test_document_create_defaults(self):
        """Test DocumentCreate with default values."""
        doc = DocumentCreate(filename="test.pdf")
        assert doc.document_type == DocumentType.UNKNOWN
        assert doc.metadata == {}

    def test_document_status_enum(self):
        """Test DocumentStatus enum values."""
        assert DocumentStatus.UPLOADED.value == "uploaded"
        assert DocumentStatus.COMPLETED.value == "completed"
        assert DocumentStatus.FAILED.value == "failed"

    def test_bounding_box(self):
        """Test BoundingBox model."""
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0, page=1)
        assert bbox.x == 10.0
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 50.0
        assert bbox.page == 1


class TestExtractionModels:
    """Tests for extraction-related models."""

    def test_extracted_field(self):
        """Test ExtractedField model."""
        field = ExtractedField(
            field_name="invoice_number",
            field_value="INV-001",
            confidence=0.95,
            source_engine="tesseract",
        )
        assert field.field_name == "invoice_number"
        assert field.field_value == "INV-001"
        assert field.confidence == 0.95
        assert field.source_engine == "tesseract"

    def test_validation_error(self):
        """Test ValidationError model."""
        error = ValidationError(
            field_name="total_amount",
            error_type="format",
            message="Invalid currency format",
        )
        assert error.field_name == "total_amount"
        assert error.error_type == "format"
        assert error.severity == "error"

    def test_extraction_result_get_field(self):
        """Test ExtractionResult.get_field method."""
        result = ExtractionResult(
            document_id=uuid4(),
            document_type=DocumentType.INVOICE,
            fields=[
                ExtractedField(
                    field_name="invoice_number",
                    field_value="INV-001",
                    confidence=0.95,
                    source_engine="tesseract",
                ),
            ],
            overall_confidence=0.92,
            validation_status=ValidationStatus.VALID,
            validation_errors=[],
        )

        field = result.get_field("invoice_number")
        assert field is not None
        assert field.field_value == "INV-001"

        missing = result.get_field("nonexistent")
        assert missing is None
