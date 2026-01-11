"""Tesseract OCR engine implementation."""

import asyncio
import time
from typing import Optional

import pytesseract
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


class TesseractEngine(OCREngine):
    """Tesseract OCR engine implementation.

    Uses pytesseract to interface with the Tesseract OCR engine.
    Supports multiple languages and provides word-level confidence scores.
    """

    def __init__(
        self,
        tesseract_cmd: Optional[str] = None,
        lang: Optional[str] = None,
    ):
        """Initialize Tesseract engine.

        Args:
            tesseract_cmd: Path to tesseract executable (optional)
            lang: Language code for OCR (default: from settings)
        """
        settings = get_settings()
        self._lang = lang or settings.tesseract_lang

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif settings.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path

    @property
    def name(self) -> str:
        """Return engine name."""
        return "tesseract"

    def get_capabilities(self) -> EngineCapabilities:
        """Return Tesseract capabilities."""
        return EngineCapabilities(
            supports_handwriting=False,
            supports_tables=True,
            supports_layout_analysis=True,
            supported_languages=self._get_available_languages(),
            max_image_size=None,  # No hard limit
        )

    def _get_available_languages(self) -> list[str]:
        """Get list of available Tesseract languages."""
        try:
            langs = pytesseract.get_languages()
            return [lang for lang in langs if lang != "osd"]
        except Exception:
            return ["eng"]

    async def process_image(self, image: Image.Image) -> OCRResult:
        """Process image with Tesseract OCR.

        Args:
            image: PIL Image to process

        Returns:
            OCRResult with extracted text and word-level data

        Raises:
            OCREngineError: If Tesseract processing fails
        """
        start_time = time.perf_counter()

        try:
            # Run Tesseract in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._process_sync, image
            )
            result.processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            return result

        except pytesseract.TesseractError as e:
            raise OCREngineError(
                message=f"Tesseract processing failed: {str(e)}",
                engine_name=self.name,
                original_error=e,
            )
        except Exception as e:
            raise OCREngineError(
                message=f"Unexpected error during OCR: {str(e)}",
                engine_name=self.name,
                original_error=e,
            )

    def _process_sync(self, image: Image.Image) -> OCRResult:
        """Synchronous image processing (runs in thread pool)."""
        # Preprocess image
        processed_image = self.preprocess_image(image)

        # Get detailed data with bounding boxes and confidence
        data = pytesseract.image_to_data(
            processed_image,
            lang=self._lang,
            output_type=pytesseract.Output.DICT,
        )

        # Extract words with confidence
        words: list[WordResult] = []
        total_confidence = 0.0
        word_count = 0

        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = float(data["conf"][i])

            # Skip empty text or low confidence markers (-1)
            if not text or conf < 0:
                continue

            # Normalize confidence to 0-1 range
            normalized_conf = conf / 100.0

            word = WordResult(
                text=text,
                confidence=normalized_conf,
                bounding_box=BoundingBox(
                    x=float(data["left"][i]),
                    y=float(data["top"][i]),
                    width=float(data["width"][i]),
                    height=float(data["height"][i]),
                ),
            )
            words.append(word)
            total_confidence += normalized_conf
            word_count += 1

        # Get full text
        raw_text = pytesseract.image_to_string(
            processed_image,
            lang=self._lang,
        ).strip()

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
        """Preprocess image for better Tesseract results.

        Converts to grayscale if needed for better OCR accuracy.

        Args:
            image: Input PIL Image

        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if necessary (Tesseract works best with RGB or grayscale)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        return image

    async def health_check(self) -> bool:
        """Check if Tesseract is available and working."""
        try:
            version = pytesseract.get_tesseract_version()
            return version is not None
        except Exception:
            return False
