"""OCR Engine Manager for orchestrating multiple OCR engines."""

import asyncio
import logging
from typing import Optional

from PIL import Image

from docpipeliner.ocr.base import EngineCapabilities, OCREngine, OCREngineError, OCRResult

logger = logging.getLogger(__name__)


class OCREngineManager:
    """Manager for orchestrating multiple OCR engines."""

    def __init__(self):
        """Initialize the OCR engine manager."""
        self._engines: dict[str, OCREngine] = {}

    def register_engine(self, engine: OCREngine) -> None:
        """Register an OCR engine."""
        if engine.name in self._engines:
            raise ValueError(f"Engine '{engine.name}' is already registered")
        self._engines[engine.name] = engine
        logger.info(f"Registered OCR engine: {engine.name}")

    def unregister_engine(self, name: str) -> None:
        """Unregister an OCR engine."""
        if name in self._engines:
            del self._engines[name]
            logger.info(f"Unregistered OCR engine: {name}")

    def get_engine(self, name: str) -> Optional[OCREngine]:
        """Get a registered engine by name."""
        return self._engines.get(name)

    def list_engines(self) -> list[str]:
        """List all registered engine names."""
        return list(self._engines.keys())

    def get_capabilities(self, name: str) -> Optional[EngineCapabilities]:
        """Get capabilities of a specific engine."""
        engine = self._engines.get(name)
        return engine.get_capabilities() if engine else None

    async def process_with_engine(
        self,
        image: Image.Image,
        engine_name: str,
    ) -> OCRResult:
        """Process an image with a specific engine."""
        engine = self._engines.get(engine_name)
        if engine is None:
            raise ValueError(f"Engine '{engine_name}' is not registered")
        return await engine.process_image(image)

    async def process_with_all(
        self,
        image: Image.Image,
        engines: Optional[list[str]] = None,
    ) -> list[OCRResult]:
        """Process an image with multiple engines in parallel."""
        engine_names = engines or list(self._engines.keys())

        if not engine_names:
            raise ValueError("No OCR engines registered")

        for name in engine_names:
            if name not in self._engines:
                raise ValueError(f"Engine '{name}' is not registered")

        tasks = [self._engines[name].process_image(image) for name in engine_names]
        results: list[OCRResult] = []
        exceptions: list[tuple[str, Exception]] = []

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(engine_names, completed):
            if isinstance(result, Exception):
                logger.error(f"Engine '{name}' failed: {result}")
                exceptions.append((name, result))
            else:
                results.append(result)

        if not results and exceptions:
            raise OCREngineError(
                message=f"All OCR engines failed. First error: {exceptions[0][1]}",
                engine_name=exceptions[0][0],
                original_error=exceptions[0][1],
            )

        return results

    def select_best_result(self, results: list[OCRResult]) -> OCRResult:
        """Select the best result from multiple engine results."""
        if not results:
            raise ValueError("No results to select from")
        return max(results, key=lambda r: r.avg_confidence)

    def merge_results(self, results: list[OCRResult]) -> OCRResult:
        """Merge results from multiple engines using consensus."""
        if not results:
            raise ValueError("No results to merge")

        if len(results) == 1:
            return results[0]

        best = self.select_best_result(results)
        avg_confidence = sum(r.avg_confidence for r in results) / len(results)

        return OCRResult(
            engine_name="merged",
            raw_text=best.raw_text,
            words=best.words,
            avg_confidence=avg_confidence,
            processing_time_ms=sum(r.processing_time_ms for r in results),
        )

    async def health_check_all(self) -> dict[str, bool]:
        """Check health of all registered engines."""
        results = {}
        for name, engine in self._engines.items():
            try:
                results[name] = await engine.health_check()
            except Exception as e:
                logger.error(f"Health check failed for '{name}': {e}")
                results[name] = False
        return results
