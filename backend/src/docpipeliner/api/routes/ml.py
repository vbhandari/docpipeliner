"""
API routes for ML/LLM features.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from docpipeliner.ml.classifier import DocumentClassifier, get_classifier
from docpipeliner.ml.ensemble import EnsembleExtractor, get_ensemble_extractor
from docpipeliner.ml.llm import LLMService, get_llm_service
from docpipeliner.ml.ner import EntityExtractor, get_entity_extractor

router = APIRouter(prefix="/ml", tags=["ML/LLM"])


# Request/Response Models
class ClassifyRequest(BaseModel):
    """Request for document classification."""
    document_id: UUID
    force_reclassify: bool = False


class ClassifyResponse(BaseModel):
    """Response for document classification."""
    document_id: UUID
    document_type: str
    subtype: str | None
    confidence: float
    model_used: str
    alternative_types: list[dict]


class ExtractLLMRequest(BaseModel):
    """Request for LLM extraction."""
    fields: list[str]
    use_reasoning: bool = True


class ExtractLLMResponse(BaseModel):
    """Response for LLM extraction."""
    document_id: UUID
    extracted_fields: list[dict]
    model_used: str
    tokens_used: int


class ExtractEnsembleRequest(BaseModel):
    """Request for ensemble extraction."""
    fields: list[str] | None = None
    use_llm_for_low_confidence: bool = True
    llm_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class ExtractEnsembleResponse(BaseModel):
    """Response for ensemble extraction."""
    document_id: UUID
    extracted_fields: list[dict]
    cost_breakdown: dict


class SummarizeRequest(BaseModel):
    """Request for document summarization."""
    max_length: int = Field(default=200, ge=50, le=1000)
    include_keypoints: bool = True
    focus: str | None = None


class SummarizeResponse(BaseModel):
    """Response for document summarization."""
    document_id: UUID
    summary: str
    key_points: list[str]
    model_used: str
    tokens_used: int


class ValidateSemanticRequest(BaseModel):
    """Request for semantic validation."""
    extracted_data: dict


class ValidateSemanticResponse(BaseModel):
    """Response for semantic validation."""
    document_id: UUID
    validation_result: dict


# Endpoints
@router.post("/documents/{document_id}/classify", response_model=ClassifyResponse)
async def classify_document(
    document_id: UUID,
    request: ClassifyRequest,
    classifier: DocumentClassifier = Depends(get_classifier),
):
    """
    Classify a document using LayoutLMv3.
    
    - **document_id**: UUID of the document to classify
    - **force_reclassify**: Force reclassification even if already classified
    """
    # TODO: Get document from database
    # document = await get_document(document_id)

    # TODO: Get OCR results from database
    # ocr_result = await get_ocr_result(document_id)

    # For now, return mock response
    return ClassifyResponse(
        document_id=document_id,
        document_type="invoice",
        subtype="standard_invoice",
        confidence=0.94,
        model_used="microsoft/layoutlmv3-base",
        alternative_types=[
            {"type": "receipt", "confidence": 0.04},
            {"type": "quote", "confidence": 0.02},
        ],
    )


@router.get("/documents/{document_id}/entities")
async def get_entities(
    document_id: UUID,
    ner: EntityExtractor = Depends(get_entity_extractor),
):
    """
    Get extracted entities from a document using spaCy NER.
    
    - **document_id**: UUID of the document
    """
    # TODO: Get document text from database
    # document = await get_document(document_id)
    # ocr_text = document.ocr_text

    # For now, return mock response
    return {
        "document_id": str(document_id),
        "entities": [
            {
                "entity_type": "PERSON",
                "text": "John Smith",
                "confidence": 0.97,
                "bounding_box": {"x": 100, "y": 200, "width": 80, "height": 20, "page": 1},
            },
            {
                "entity_type": "ORG",
                "text": "Acme Corporation",
                "confidence": 0.95,
                "bounding_box": {"x": 100, "y": 150, "width": 150, "height": 20, "page": 1},
            },
        ],
        "model_used": "en_core_web_lg",
    }


@router.post("/documents/{document_id}/extract-llm", response_model=ExtractLLMResponse)
async def extract_with_llm(
    document_id: UUID,
    request: ExtractLLMRequest,
    llm: LLMService = Depends(get_llm_service),
):
    """
    Extract fields from a document using LLM.
    
    - **document_id**: UUID of the document
    - **fields**: List of field names to extract
    - **use_reasoning**: Include reasoning in output
    """
    # TODO: Get document text from database
    # document = await get_document(document_id)
    # ocr_text = document.ocr_text
    # document_type = document.document_type

    # For now, return mock response
    return ExtractLLMResponse(
        document_id=document_id,
        extracted_fields=[
            {
                "field_name": "invoice_number",
                "field_value": "INV-2026-001",
                "confidence": 0.98,
                "reasoning": "Found in top-left corner with label 'Invoice No:'",
                "bounding_box": {"x": 100, "y": 50, "width": 150, "height": 20, "page": 1},
            },
            {
                "field_name": "vendor_name",
                "field_value": "Acme Corporation",
                "confidence": 0.95,
                "reasoning": "Found in header section",
                "bounding_box": {"x": 100, "y": 80, "width": 200, "height": 20, "page": 1},
            },
        ],
        model_used="gpt-4o-mini",
        tokens_used=1234,
    )


@router.post("/documents/{document_id}/extract-ensemble", response_model=ExtractEnsembleResponse)
async def extract_with_ensemble(
    document_id: UUID,
    request: ExtractEnsembleRequest,
    ensemble: EnsembleExtractor = Depends(get_ensemble_extractor),
):
    """
    Extract fields using ensemble ML+LLM approach.
    
    - **document_id**: UUID of the document
    - **fields**: Optional list of field names to extract
    - **use_llm_for_low_confidence**: Use LLM for low-confidence ML results
    - **llm_confidence_threshold**: Threshold for using LLM
    """
    # TODO: Get document text from database
    # document = await get_document(document_id)
    # ocr_text = document.ocr_text
    # ocr_words = document.ocr_words

    # For now, return mock response
    return ExtractEnsembleResponse(
        document_id=document_id,
        extracted_fields=[
            {
                "field_name": "invoice_number",
                "field_value": "INV-2026-001",
                "confidence": 0.98,
                "source": "both",
                "ml_confidence": 0.97,
                "llm_confidence": 0.98,
            },
            {
                "field_name": "vendor_name",
                "field_value": "Acme Corporation",
                "confidence": 0.95,
                "source": "ml",
                "ml_confidence": 0.95,
                "llm_confidence": None,
            },
        ],
        cost_breakdown={
            "ml_inference_time_ms": 150,
            "llm_tokens_used": 500,
            "estimated_cost_usd": 0.001,
        },
    )


@router.post("/documents/{document_id}/summarize", response_model=SummarizeResponse)
async def summarize_document(
    document_id: UUID,
    request: SummarizeRequest,
    llm: LLMService = Depends(get_llm_service),
):
    """
    Generate a summary of a document using LLM.
    
    - **document_id**: UUID of the document
    - **max_length**: Maximum length of summary in words
    - **include_keypoints**: Include bullet-point key points
    - **focus**: Optional focus area (financial, legal, general)
    """
    # TODO: Get document text from database
    # document = await get_document(document_id)
    # ocr_text = document.ocr_text

    # For now, return mock response
    return SummarizeResponse(
        document_id=document_id,
        summary="This invoice from Acme Corporation for $1,234.56 covers services rendered in January 2026. Payment is due within 30 days.",
        key_points=[
            "Invoice number: INV-2026-001",
            "Total amount: $1,234.56",
            "Due date: 2026-02-15",
            "Payment terms: Net 30",
        ],
        model_used="gpt-4o-mini",
        tokens_used=856,
    )


@router.post("/documents/{document_id}/validate-semantic", response_model=ValidateSemanticResponse)
async def validate_semantic(
    document_id: UUID,
    request: ValidateSemanticRequest,
    llm: LLMService = Depends(get_llm_service),
):
    """
    Validate extracted data using LLM semantic reasoning.
    
    - **document_id**: UUID of the document
    - **extracted_data**: Dictionary of extracted fields to validate
    """
    # TODO: Get document type from database
    # document = await get_document(document_id)
    # document_type = document.document_type

    # For now, return mock response
    return ValidateSemanticResponse(
        document_id=document_id,
        validation_result={
            "is_valid": True,
            "confidence": 0.92,
            "issues": [],
            "reasoning": "All fields extracted with high confidence. Line items sum matches total.",
        },
    )
