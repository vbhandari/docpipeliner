"""OCR engine abstraction layer."""

from docpipeliner.ocr.base import OCREngine, OCREngineError
from docpipeliner.ocr.manager import OCREngineManager
from docpipeliner.ocr.tesseract import TesseractEngine

__all__ = [
    "OCREngine",
    "OCREngineError",
    "OCREngineManager",
    "TesseractEngine",
]

# PaddleOCR import is optional due to heavy dependencies
try:
    from docpipeliner.ocr.paddle import PaddleOCREngine

    __all__.append("PaddleOCREngine")
except ImportError:
    pass
