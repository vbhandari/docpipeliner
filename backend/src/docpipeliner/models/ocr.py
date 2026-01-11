"""OCR-related data models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from docpipeliner.models.document import BoundingBox


class WordResult(BaseModel):
    """Individual word result from OCR."""

    text: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: Optional[BoundingBox] = None


class OCRResultCreate(BaseModel):
    """Schema for creating an OCR result record."""

    page_id: UUID
    engine: str = Field(..., description="OCR engine name (e.g., 'tesseract', 'paddleocr')")
    raw_text: str
    words: list[WordResult] = Field(default_factory=list)
    avg_confidence: float = Field(..., ge=0.0, le=1.0)
    processing_ms: int = Field(..., ge=0, description="Processing time in milliseconds")


class OCRResult(OCRResultCreate):
    """OCR result model with database fields."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class OCREngineResult(BaseModel):
    """Result from a single OCR engine processing."""

    engine_name: str
    raw_text: str
    words: list[WordResult]
    avg_confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: int


class AggregatedOCRResult(BaseModel):
    """Aggregated result from multiple OCR engines."""

    page_id: UUID
    engine_results: list[OCREngineResult]
    best_result: OCREngineResult
    consensus_text: Optional[str] = None
    consensus_confidence: Optional[float] = None
