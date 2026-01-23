"""
Document classifier using LayoutLMv3 for layout-aware document classification.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import logging

from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForSequenceClassification

from docpipeliner.config import settings

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Document types supported by the classifier."""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    QUOTE = "quote"
    PURCHASE_ORDER = "purchase_order"
    INSURANCE_CLAIM = "insurance_claim"
    COMPLIANCE_FORM = "compliance_form"
    CONTRACT = "contract"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of document classification."""
    document_type: DocumentType
    subtype: Optional[str]
    confidence: float
    model_used: str
    alternative_types: List[tuple[DocumentType, float]]


class DocumentClassifier:
    """
    Document classifier using LayoutLMv3 for layout-aware classification.
    
    This classifier uses LayoutLMv3-base which is optimized for document
    understanding tasks, taking into account both text and layout information.
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/layoutlmv3-base",
        device: Optional[str] = None,
    ):
        """
        Initialize the document classifier.
        
        Args:
            model_name: Hugging Face model name or path
            device: Device to run inference on ('cuda', 'cpu', or None for auto)
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = None
        self.model = None
        self.label_map = {
            0: DocumentType.INVOICE,
            1: DocumentType.RECEIPT,
            2: DocumentType.QUOTE,
            3: DocumentType.PURCHASE_ORDER,
            4: DocumentType.INSURANCE_CLAIM,
            5: DocumentType.COMPLIANCE_FORM,
            6: DocumentType.CONTRACT,
            7: DocumentType.UNKNOWN,
        }
        
        logger.info(f"Initializing DocumentClassifier with model: {model_name}")
        logger.info(f"Using device: {self.device}")
    
    def load_model(self) -> None:
        """Load the model and processor."""
        if self.model is not None:
            return
        
        try:
            logger.info("Loading LayoutLMv3 model and processor...")
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                apply_ocr=False,  # We'll use our own OCR
            )
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                num_labels=len(self.label_map),
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def classify(
        self,
        image: Image.Image,
        ocr_text: str,
        ocr_words: Optional[List[dict]] = None,
    ) -> ClassificationResult:
        """
        Classify a document.
        
        Args:
            image: PIL Image of the document page
            ocr_text: Extracted text from OCR
            ocr_words: List of OCR word results with bounding boxes
            
        Returns:
            ClassificationResult with document type and confidence
        """
        self.load_model()
        
        try:
            # Prepare inputs
            if ocr_words:
                # Use layout-aware processing with bounding boxes
                inputs = self._prepare_layout_inputs(image, ocr_words)
            else:
                # Use text-only processing
                inputs = self._prepare_text_inputs(ocr_text)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)
                confidence, predicted_class = torch.max(probs, dim=-1)
            
            # Get results
            predicted_type = self.label_map[predicted_class.item()]
            confidence_score = confidence.item()
            
            # Get alternative types (top 3)
            top_k = 3
            top_probs, top_classes = torch.topk(probs, k=min(top_k, len(self.label_map)))
            alternatives = [
                (self.label_map[cls.item()], prob.item())
                for cls, prob in zip(top_classes[0], top_probs[0])
                if self.label_map[cls.item()] != predicted_type
            ]
            
            # Determine subtype based on type
            subtype = self._determine_subtype(predicted_type, ocr_text)
            
            return ClassificationResult(
                document_type=predicted_type,
                subtype=subtype,
                confidence=confidence_score,
                model_used=self.model_name,
                alternative_types=alternatives,
            )
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # Return unknown type on error
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                subtype=None,
                confidence=0.0,
                model_used=self.model_name,
                alternative_types=[],
            )
    
    def _prepare_layout_inputs(
        self,
        image: Image.Image,
        ocr_words: List[dict],
    ) -> dict:
        """Prepare inputs with layout information."""
        # Extract words and bounding boxes
        words = [word["text"] for word in ocr_words]
        boxes = [
            [
                word["bounding_box"]["x"],
                word["bounding_box"]["y"],
                word["bounding_box"]["x"] + word["bounding_box"]["width"],
                word["bounding_box"]["y"] + word["bounding_box"]["height"],
            ]
            for word in ocr_words
        ]
        
        # Normalize boxes to [0, 1000] range
        width, height = image.size
        boxes = [
            [
                int(x * 1000 / width),
                int(y * 1000 / height),
                int(x * 1000 / width),
                int(y * 1000 / height),
            ]
            for x, y, x2, y2 in boxes
        ]
        
        # Process with LayoutLMv3
        inputs = self.processor(
            image,
            words=words,
            boxes=boxes,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        
        return {k: v.to(self.device) for k, v in inputs.items()}
    
    def _prepare_text_inputs(self, text: str) -> dict:
        """Prepare inputs with text only."""
        inputs = self.processor(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        
        return {k: v.to(self.device) for k, v in inputs.items()}
    
    def _determine_subtype(
        self,
        document_type: DocumentType,
        text: str,
    ) -> Optional[str]:
        """
        Determine document subtype based on text content.
        
        Args:
            document_type: The main document type
            text: OCR text from the document
            
        Returns:
            Subtype string or None
        """
        text_lower = text.lower()
        
        if document_type == DocumentType.INVOICE:
            if "purchase order" in text_lower or "po #" in text_lower:
                return "purchase_order"
            elif "credit note" in text_lower or "credit memo" in text_lower:
                return "credit_note"
            elif "debit note" in text_lower or "debit memo" in text_lower:
                return "debit_note"
            return "standard_invoice"
        
        elif document_type == DocumentType.INSURANCE_CLAIM:
            if "auto" in text_lower or "vehicle" in text_lower:
                return "auto_claim"
            elif "property" in text_lower or "home" in text_lower:
                return "property_claim"
            elif "health" in text_lower or "medical" in text_lower:
                return "health_claim"
            return "general_claim"
        
        elif document_type == DocumentType.COMPLIANCE_FORM:
            if "tax" in text_lower:
                return "tax_form"
            elif "financial" in text_lower:
                return "financial_report"
            elif "regulatory" in text_lower:
                return "regulatory_filing"
            return "general_compliance"
        
        return None


# Singleton instance
_classifier_instance: Optional[DocumentClassifier] = None


def get_classifier() -> DocumentClassifier:
    """Get or create the singleton classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = DocumentClassifier(
            model_name=settings.ml_classifier_model,
        )
    return _classifier_instance
