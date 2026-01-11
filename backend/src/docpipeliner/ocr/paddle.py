"""PaddleOCR engine implementation."""

import asyncio
import time
from typing import Optional

from PIL import Image

from docpipeliner.config import get_settings
from docpipeliner.ocr.base import (
    BoundingBox,
    EngineCapabilities,
    OCREngine,
    OCREngineError,
    OCRResult,
    WordResult,
)

# PaddleOCR is imported lazily due to heavy dependencies
_paddleocr = None


def _get_paddleocr():
    """Lazy import of PaddleOCR."""
    global _paddleocr
    if _paddleocr is None:
        try:
            from paddleocr import PaddleOCR

            _paddleocr = PaddleOCR
        except ImportError as e:
            raise ImportError(
                "PaddleOCR is not installed. Install with: pip install paddleocr paddlepaddle"
            ) from e
    return _paddleocr


class PaddleOCREngine(OCREngine):
    """PaddleOCR engine implementation.

    Uses PaddleOCR for text recognition with support for
    multiple languages and layout analysis.
    """

    def __init__(
        self,
        use_gpu: Optional[bool] = None,
        lang: Optional[str] = None,
    ):
        """Initialize PaddleOCR engine.

        Args:
            use_gpu: Whether to use GPU acceleration (default: from settings)
            lang: Language code for OCR (default: from settings)
        """
        settings = get_settings()
        self._use_gpu = use_gpu if use_gpu is not None else settings.paddleocr_use_gpu
        self._lang = lang or settings.paddleocr_lang
        self._ocr_instance: Optional[object] = None

    @property
    def name(self) -> str:
        """Return engine name."""
        return "paddleocr"

    def _get_ocr(self):
        """Get or create PaddleOCR instance (lazy initialization)."""
        if self._ocr_instance is None:
            PaddleOCR = _get_paddleocr()
            self._ocr_instance = PaddleOCR(
                use_angle_cls=True,
                lang=self._lang,
                use_gpu=self._use_gpu,
                show_log=False,
            )
        return self._ocr_instance

    def get_capabilities(self) -> EngineCapabilities:
        """Return PaddleOCR capabilities."""
        return EngineCapabilities(
            supports_handwriting=True,
            supports_tables=True,
            supports_layout_analysis=True,
            supported_languages=["en", "ch", "japan", "korean", "french", "german"],
            max_image_size=None,
        )

    async def process_image(self, image: Image.Image) -> OCRResult:
        """Process image with PaddleOCR.

        Args:
            image: PIL Image to process

        Returns:
            OCRResult with extracted text and word-level data

        Raises:
            OCREngineError: If PaddleOCR processing fails
        """
        start_time = time.perf_counter()

        try:
            # Run PaddleOCR in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._process_sync, image)
            result.processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            return result

        except ImportError as e:
            raise OCREngineError(
                message=str(e),
                engine_name=self.name,
                original_error=e,
            )
        except Exception as e:
            raise OCREngineError(
                message=f"PaddleOCR processing failed: {str(e)}",
                engine_name=self.name,
                original_error=e,
            )

    def _process_sync(self, image: Image.Image) -> OCRResult:
        """Synchronous image processing (runs in thread pool)."""
        import numpy as np

        # Preprocess and convert to numpy array
        processed_image = self.preprocess_image(image)
        img_array = np.array(processed_image)

        # Run OCR
        ocr = self._get_ocr()
        result = ocr.ocr(img_array, cls=True)

        # Parse results
        words: list[WordResult] = []
        text_lines: list[str] = []
        total_confidence = 0.0
        word_count = 0

        # PaddleOCR returns list of pages, each page has list of lines
        if result and result[0]:
            for line in result[0]:
                if line is None:
                    continue

                # Each line is (bounding_box, (text, confidence))
                bbox_points, (text, confidence) = line

                if not text.strip():
                    continue

                # Convert bbox from 4 points to x, y, width, height
                # bbox_points is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                x_coords = [p[0] for p in bbox_points]
                y_coords = [p[1] for p in bbox_points]
                x = min(x_coords)
                y = min(y_coords)
                width = max(x_coords) - x
                height = max(y_coords) - y

                word = WordResult(
                    text=text.strip(),
                    confidence=float(confidence),
                    bounding_box=BoundingBox(
                        x=float(x),
                        y=float(y),
                        width=float(width),
                        height=float(height),
                    ),
                )
                words.append(word)
                text_lines.append(text.strip())
                total_confidence += float(confidence)
                word_count += 1

        # Combine text lines
        raw_text = "\n".join(text_lines)

        # Calculate average confidence
        avg_confidence = total_confidence / word_count if word_count > 0 else 0.0

        return OCRResult(
            engine_name=self.name,
            raw_text=raw_text,
            words=words,
            avg_confidence=avg_confidence,
            processing_time_ms=0,  # Will be set by caller
        )

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for PaddleOCR.

        Args:
            image: Input PIL Image

        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image

    async def health_check(self) -> bool:
        """Check if PaddleOCR is available and working."""
        try:
            _get_paddleocr()
            return True
        except ImportError:
            return False
