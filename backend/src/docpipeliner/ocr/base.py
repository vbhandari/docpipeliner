"""Abstract base class for OCR engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from PIL import Image


class OCREngineError(Exception):
    """Exception raised by OCR engines."""

    def __init__(self, message: str, engine_name: str, original_error: Optional[Exception] = None):
        self.message = message
        self.engine_name = engine_name
        self.original_error = original_error
        super().__init__(f"[{engine_name}] {message}")


@dataclass
class BoundingBox:
    """Bounding box for text location."""

    x: float
    y: float
    width: float
    height: float

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class WordResult:
    """Result for a single word from OCR."""

    text: str
    confidence: float
    bounding_box: Optional[BoundingBox] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
        }


@dataclass
class OCRResult:
    """Result from OCR processing."""

    engine_name: str
    raw_text: str
    words: list[WordResult] = field(default_factory=list)
    avg_confidence: float = 0.0
    processing_time_ms: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "engine_name": self.engine_name,
            "raw_text": self.raw_text,
            "words": [w.to_dict() for w in self.words],
            "avg_confidence": self.avg_confidence,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class EngineCapabilities:
    """Capabilities of an OCR engine."""

    supports_handwriting: bool = False
    supports_tables: bool = False
    supports_layout_analysis: bool = False
    supported_languages: list[str] = field(default_factory=lambda: ["eng"])
    max_image_size: Optional[tuple[int, int]] = None


class OCREngine(ABC):
    """Abstract base class for OCR engines.

    All OCR engine implementations must inherit from this class
    and implement the required abstract methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this OCR engine."""
        pass

    @abstractmethod
    async def process_image(self, image: Image.Image) -> OCRResult:
        """Process an image and return OCR results.

        Args:
            image: PIL Image to process

        Returns:
            OCRResult containing extracted text and metadata

        Raises:
            OCREngineError: If processing fails
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> EngineCapabilities:
        """Return the capabilities of this engine."""
        pass

    async def health_check(self) -> bool:
        """Check if the engine is healthy and ready to process.

        Returns:
            True if engine is ready, False otherwise
        """
        return True

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image before OCR (optional override).

        Default implementation returns the image unchanged.
        Subclasses can override for engine-specific preprocessing.

        Args:
            image: Input PIL Image

        Returns:
            Preprocessed PIL Image
        """
        return image
