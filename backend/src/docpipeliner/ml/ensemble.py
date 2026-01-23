"""
Ensemble extractor that combines ML and LLM results for optimal accuracy.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

from docpipeliner.ml.classifier import DocumentClassifier, get_classifier
from docpipeliner.ml.ner import EntityExtractor, get_entity_extractor
from docpipeliner.ml.llm import LLMService, get_llm_service, LLMExtractionResult

logger = logging.getLogger(__name__)


@dataclass
class EnsembleField:
    """Field extracted by ensemble."""
    field_name: str
    field_value: str
    confidence: float
    source: str  # 'ml', 'llm', or 'both'
    ml_confidence: Optional[float]
    llm_confidence: Optional[float]
    reasoning: Optional[str]


@dataclass
class EnsembleResult:
    """Result of ensemble extraction."""
    document_id: str
    extracted_fields: List[EnsembleField]
    cost_breakdown: Dict[str, Any]


class EnsembleExtractor:
    """
    Ensemble extractor that combines ML and LLM results.
    
    Uses ML models for fast, cheap extraction and LLMs for
    low-confidence cases or complex reasoning.
    """
    
    def __init__(
        self,
        llm_confidence_threshold: float = 0.7,
    ):
        """
        Initialize ensemble extractor.
        
        Args:
            llm_confidence_threshold: Threshold below which LLM is used
        """
        self.llm_confidence_threshold = llm_confidence_threshold
        self.classifier = get_classifier()
        self.ner = get_entity_extractor()
        self.llm = get_llm_service()
        
        logger.info(f"Initialized EnsembleExtractor with LLM threshold: {llm_confidence_threshold}")
    
    def extract(
        self,
        ocr_text: str,
        ocr_words: Optional[List[dict]] = None,
        fields: Optional[List[str]] = None,
        document_type: Optional[str] = None,
        use_llm_for_low_confidence: bool = True,
    ) -> EnsembleResult:
        """
        Extract fields using ensemble approach.
        
        Args:
            ocr_text: Text extracted from OCR
            ocr_words: Optional list of OCR words with bounding boxes
            fields: List of field names to extract
            document_type: Type of document
            use_llm_for_low_confidence: Whether to use LLM for low confidence
            
        Returns:
            EnsembleResult with extracted fields and cost breakdown
        """
        import time
        
        start_time = time.time()
        ml_time = 0
        llm_time = 0
        llm_tokens = 0
        
        # Step 1: Extract entities using ML (spaCy)
        ml_start = time.time()
        ner_result = self.ner.extract_entities(ocr_text, ocr_words)
        ml_time = time.time() - ml_start
        
        # Step 2: Determine if LLM is needed
        needs_llm = self._needs_llm(ner_result, use_llm_for_low_confidence)
        
        llm_results = {}
        if needs_llm and fields:
            # Step 3: Use LLM for extraction
            llm_start = time.time()
            llm_extractions = self.llm.extract_fields(
                ocr_text=ocr_text,
                fields=fields,
                document_type=document_type or "unknown",
                use_reasoning=True,
            )
            llm_time = time.time() - llm_start
            
            # Convert to dict for easy lookup
            llm_results = {e.field_name: e for e in llm_extractions}
            # Estimate tokens based on text length (rough estimate: ~4 chars per token)
            llm_tokens = int(len(ocr_text) / 4)
        
        # Step 4: Merge results
        merged_fields = self._merge_results(
            ner_result,
            llm_results,
            fields,
        )
        
        # Step 5: Calculate cost breakdown
        total_time = time.time() - start_time
        cost_breakdown = {
            "ml_inference_time_ms": int(ml_time * 1000),
            "llm_inference_time_ms": int(llm_time * 1000),
            "llm_tokens_used": llm_tokens,
            "estimated_cost_usd": self._estimate_cost(ml_time, llm_tokens),
        }
        
        return EnsembleResult(
            document_id="",  # Will be set by caller
            extracted_fields=merged_fields,
            cost_breakdown=cost_breakdown,
        )
    
    def _needs_llm(
        self,
        ner_result,
        use_llm_for_low_confidence: bool,
    ) -> bool:
        """
        Determine if LLM extraction is needed.
        
        Args:
            ner_result: NER extraction result
            use_llm_for_low_confidence: Whether to use LLM for low confidence
            
        Returns:
            True if LLM should be used
        """
        if not use_llm_for_low_confidence:
            return False
        
        # Check if any entity has low confidence
        for entity in ner_result.entities:
            if entity.confidence < self.llm_confidence_threshold:
                return True
        
        return False
    
    def _merge_results(
        self,
        ner_result,
        llm_results: Dict[str, LLMExtractionResult],
        requested_fields: Optional[List[str]],
    ) -> List[EnsembleField]:
        """
        Merge ML and LLM results.
        
        Args:
            ner_result: NER extraction result
            llm_results: LLM extraction results
            requested_fields: Requested field names
            
        Returns:
            List of merged ensemble fields
        """
        merged = {}
        
        # Add ML results
        for entity in ner_result.entities:
            field_name = entity.entity_type.value.lower()
            merged[field_name] = EnsembleField(
                field_name=field_name,
                field_value=entity.text,
                confidence=entity.confidence,
                source="ml",
                ml_confidence=entity.confidence,
                llm_confidence=None,
                reasoning=None,
            )
        
        # Merge LLM results
        for field_name, llm_result in llm_results.items():
            if field_name in merged:
                # Conflict - use higher confidence
                ml_field = merged[field_name]
                if llm_result.confidence > ml_field.ml_confidence:
                    merged[field_name] = EnsembleField(
                        field_name=field_name,
                        field_value=llm_result.field_value,
                        confidence=llm_result.confidence,
                        source="llm",
                        ml_confidence=ml_field.ml_confidence,
                        llm_confidence=llm_result.confidence,
                        reasoning=llm_result.reasoning,
                    )
                else:
                    # Keep ML result but add LLM reasoning
                    merged[field_name].reasoning = llm_result.reasoning
            else:
                # Only LLM has this field
                merged[field_name] = EnsembleField(
                    field_name=field_name,
                    field_value=llm_result.field_value,
                    confidence=llm_result.confidence,
                    source="llm",
                    ml_confidence=None,
                    llm_confidence=llm_result.confidence,
                    reasoning=llm_result.reasoning,
                )
        
        # Filter to requested fields if provided
        if requested_fields:
            merged = {
                k: v for k, v in merged.items()
                if k in requested_fields
            }
        
        return list(merged.values())
    
    def _estimate_cost(
        self,
        ml_time: float,
        llm_tokens: int,
    ) -> float:
        """
        Estimate cost of extraction.
        
        Args:
            ml_time: ML inference time in seconds
            llm_tokens: LLM tokens used
            
        Returns:
            Estimated cost in USD
        """
        # ML cost (very low - CPU inference)
        ml_cost = ml_time * 0.00001  # ~$0.01 per 1000 seconds
        
        # LLM cost (GPT-4o mini: ~$0.15 per 1M input tokens, $0.60 per 1M output tokens)
        # Assume 50/50 split input/output
        llm_cost = (llm_tokens * 0.5 * 0.15 / 1_000_000) + (llm_tokens * 0.5 * 0.60 / 1_000_000)
        
        return ml_cost + llm_cost


# Singleton instance
_ensemble_instance: Optional[EnsembleExtractor] = None


def get_ensemble_extractor() -> EnsembleExtractor:
    """Get or create singleton ensemble extractor instance."""
    global _ensemble_instance
    if _ensemble_instance is None:
        _ensemble_instance = EnsembleExtractor(
            llm_confidence_threshold=0.7,
        )
    return _ensemble_instance
