"""
LLM service for semantic understanding and extraction using OpenAI API or self-hosted models.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
import logging
import json

from openai import OpenAI
import redis

from docpipeliner.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM provider options."""
    OPENAI = "openai"
    LLAMA = "llama"


@dataclass
class LLMExtractionResult:
    """Result of LLM extraction."""
    field_name: str
    field_value: str
    confidence: float
    reasoning: str
    bounding_box: Optional[dict]


@dataclass
class LLMValidationResult:
    """Result of LLM validation."""
    is_valid: bool
    confidence: float
    issues: List[Dict[str, Any]]
    reasoning: str


@dataclass
class LLMSummaryResult:
    """Result of LLM summarization."""
    summary: str
    key_points: List[str]
    model_used: str
    tokens_used: int


class LLMService:
    """
    LLM service for semantic understanding and extraction.
    
    Supports both OpenAI API (GPT-4o mini) and self-hosted Llama models
    via OpenAI-compatible API (e.g., vLLM).
    """
    
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_ttl: int = 3600,  # 1 hour
    ):
        """
        Initialize LLM service.
        
        Args:
            provider: LLM provider to use
            model: Model name
            api_key: API key (for OpenAI)
            base_url: Base URL for self-hosted models
            cache_ttl: Cache time-to-live in seconds
        """
        self.provider = provider
        self.model = model
        self.cache_ttl = cache_ttl
        
        # Initialize Redis for caching
        self.redis_client = None
        if settings.redis_url:
            try:
                self.redis_client = redis.from_url(settings.redis_url)
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}")
        
        # Initialize OpenAI client
        if provider == LLMProvider.OPENAI:
            self.client = OpenAI(
                api_key=api_key or settings.openai_api_key,
            )
        elif provider == LLMProvider.LLAMA:
            self.client = OpenAI(
                api_key="dummy",  # vLLM doesn't require real key
                base_url=base_url or settings.llama_base_url,
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        logger.info(f"Initialized LLM service with provider: {provider}, model: {model}")
    
    def extract_fields(
        self,
        ocr_text: str,
        fields: List[str],
        document_type: str,
        use_reasoning: bool = True,
    ) -> List[LLMExtractionResult]:
        """
        Extract structured fields from OCR text using LLM.
        
        Args:
            ocr_text: Text extracted from OCR
            fields: List of field names to extract
            document_type: Type of document (for context)
            use_reasoning: Whether to include reasoning in output
            
        Returns:
            List of extracted fields with confidence and reasoning
        """
        # Check cache
        cache_key = f"extract:{hash(ocr_text)}:{document_type}:{','.join(fields)}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.info("Returning cached extraction result")
            return cached
        
        # Build prompt
        prompt = self._build_extraction_prompt(ocr_text, fields, document_type, use_reasoning)
        
        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured data from documents. Always respond in valid JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"},
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Convert to extraction results
            extractions = []
            for field_name, field_data in result.get("fields", {}).items():
                extractions.append(LLMExtractionResult(
                    field_name=field_name,
                    field_value=field_data.get("value", ""),
                    confidence=field_data.get("confidence", 0.5),
                    reasoning=field_data.get("reasoning", ""),
                    bounding_box=field_data.get("bounding_box"),
                ))
            
            # Cache result
            self._set_cache(cache_key, extractions)
            
            logger.info(f"Extracted {len(extractions)} fields using {self.tokens_used(response)} tokens")
            return extractions
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return []
    
    def validate_semantic(
        self,
        extracted_data: Dict[str, Any],
        document_type: str,
    ) -> LLMValidationResult:
        """
        Validate extracted data using LLM reasoning.
        
        Args:
            extracted_data: Dictionary of extracted fields
            document_type: Type of document
            
        Returns:
            Validation result with issues and reasoning
        """
        # Check cache
        cache_key = f"validate:{hash(json.dumps(extracted_data))}:{document_type}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Build prompt
        prompt = self._build_validation_prompt(extracted_data, document_type)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at validating document data. Check for consistency, completeness, and potential errors.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            validation_result = LLMValidationResult(
                is_valid=result.get("is_valid", False),
                confidence=result.get("confidence", 0.5),
                issues=result.get("issues", []),
                reasoning=result.get("reasoning", ""),
            )
            
            # Cache result
            self._set_cache(cache_key, validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return LLMValidationResult(
                is_valid=False,
                confidence=0.0,
                issues=[],
                reasoning=f"Validation failed: {str(e)}",
            )
    
    def summarize(
        self,
        text: str,
        max_length: int = 200,
        include_keypoints: bool = True,
        focus: Optional[str] = None,
    ) -> LLMSummaryResult:
        """
        Generate summary of document text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in words
            include_keypoints: Whether to include bullet-point key points
            focus: Optional focus area (financial, legal, general)
            
        Returns:
            Summary result with summary and key points
        """
        # Check cache
        cache_key = f"summary:{hash(text)}:{max_length}:{focus}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Build prompt
        prompt = self._build_summary_prompt(text, max_length, include_keypoints, focus)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at summarizing documents. Provide clear, concise summaries.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            
            content = response.choices[0].message.content
            
            # Parse summary and key points
            summary = content
            key_points = []
            
            if include_keypoints:
                # Extract bullet points
                lines = content.split('\n')
                summary_lines = []
                for line in lines:
                    if line.strip().startswith('-') or line.strip().startswith('*'):
                        key_points.append(line.strip().lstrip('-*').strip())
                    else:
                        summary_lines.append(line)
                summary = '\n'.join(summary_lines).strip()
            
            result = LLMSummaryResult(
                summary=summary,
                key_points=key_points,
                model_used=self.model,
                tokens_used=self.tokens_used(response),
            )
            
            # Cache result
            self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return LLMSummaryResult(
                summary="",
                key_points=[],
                model_used=self.model,
                tokens_used=0,
            )
    
    def _build_extraction_prompt(
        self,
        ocr_text: str,
        fields: List[str],
        document_type: str,
        use_reasoning: bool,
    ) -> str:
        """Build prompt for field extraction."""
        prompt = f"""
Extract the following fields from this {document_type}:

Fields to extract:
{', '.join(fields)}

OCR Text:
{ocr_text}

Respond in JSON format with this structure:
{{
  "fields": {{
    "field_name": {{
      "value": "extracted value",
      "confidence": 0.95,
      "reasoning": "brief explanation of where and how you found this field"
    }}
  }}
}}
"""
        if use_reasoning:
            prompt += "\n\nThink step by step about where each field is located and verify your extractions."
        
        return prompt
    
    def _build_validation_prompt(
        self,
        extracted_data: Dict[str, Any],
        document_type: str,
    ) -> str:
        """Build prompt for validation."""
        prompt = f"""
Review the extracted data from this {document_type} for consistency and potential issues:

Extracted Data:
{json.dumps(extracted_data, indent=2)}

Check for:
1. Required fields are present
2. Dates are valid and logical
3. Numerical values are reasonable
4. Cross-field consistency (e.g., line items sum equals total)
5. Any missing or suspicious data

Respond in JSON format:
{{
  "is_valid": true/false,
  "confidence": 0.95,
  "issues": [
    {{
      "field": "field_name",
      "issue": "description of issue",
      "severity": "high/medium/low"
    }}
  ],
  "reasoning": "explanation of your validation"
}}
"""
        return prompt
    
    def _build_summary_prompt(
        self,
        text: str,
        max_length: int,
        include_keypoints: bool,
        focus: Optional[str],
    ) -> str:
        """Build prompt for summarization."""
        prompt = f"""
Summarize the following document in approximately {max_length} words.

"""
        if focus:
            prompt += f"Focus on {focus} aspects.\n"
        
        prompt += f"""
Document Text:
{text[:4000]}  # Limit to first 4000 chars to avoid token limits

"""
        if include_keypoints:
            prompt += """
Provide:
1. A concise summary paragraph
2. Bullet-point key points (start each with -)

Format your response as:
[Summary paragraph]

- Key point 1
- Key point 2
- Key point 3
"""
        else:
            prompt += "Provide a concise summary paragraph."
        
        return prompt
    
    def tokens_used(self, response) -> int:
        """Get total tokens used from response."""
        return response.usage.total_tokens
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        return None
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Set value in Redis cache."""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(
                key,
                self.cache_ttl,
                json.dumps(value),
            )
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")


# Singleton instance
_llm_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create singleton LLM service instance."""
    global _llm_instance
    if _llm_instance is None:
        provider = LLMProvider(settings.llm_provider)
        _llm_instance = LLMService(
            provider=provider,
            model=settings.llm_model,
        )
    return _llm_instance
