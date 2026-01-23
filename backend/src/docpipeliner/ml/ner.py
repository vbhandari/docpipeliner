"""
Named Entity Recognition using spaCy for extracting entities from documents.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import logging

import spacy

from docpipeliner.config import settings

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Entity types supported by NER."""
    PERSON = "PERSON"
    ORG = "ORG"
    DATE = "DATE"
    ADDRESS = "ADDRESS"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    MONEY = "MONEY"
    CARDINAL = "CARDINAL"
    GPE = "GPE"  # Geopolitical entity (countries, cities, states)


@dataclass
class Entity:
    """Extracted entity from document."""
    entity_type: EntityType
    text: str
    confidence: float
    bounding_box: Optional[dict]
    start_char: int
    end_char: int


@dataclass
class NERResult:
    """Result of NER extraction."""
    document_id: str
    entities: List[Entity]
    model_used: str


class EntityExtractor:
    """
    Entity extractor using spaCy for fast, accurate NER.
    
    Uses spaCy's en_core_web_lg model which provides good accuracy
    for English text with reasonable performance.
    """
    
    def __init__(
        self,
        model_name: str = "en_core_web_lg",
    ):
        """
        Initialize entity extractor.
        
        Args:
            model_name: spaCy model name
        """
        self.model_name = model_name
        self.nlp = None
        
        logger.info(f"Initializing EntityExtractor with model: {model_name}")
    
    def load_model(self) -> None:
        """Load spaCy model."""
        if self.nlp is not None:
            return
        
        try:
            logger.info("Loading spaCy model...")
            self.nlp = spacy.load(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            logger.info("Attempting to download model...")
            try:
                import subprocess
                subprocess.run(
                    ["python", "-m", "spacy", "download", self.model_name],
                    check=True,
                )
                self.nlp = spacy.load(self.model_name)
                logger.info("Model downloaded and loaded successfully")
            except Exception as download_error:
                logger.error(f"Failed to download model: {download_error}")
                raise
    
    def extract_entities(
        self,
        text: str,
        ocr_words: Optional[List[dict]] = None,
    ) -> NERResult:
        """
        Extract entities from text.
        
        Args:
            text: Text to extract entities from
            ocr_words: Optional list of OCR words with bounding boxes for mapping
            
        Returns:
            NERResult with extracted entities
        """
        self.load_model()
        
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            entities = []
            for ent in doc.ents:
                # Map entity type to our enum
                entity_type = self._map_entity_type(ent.label_)
                if entity_type is None:
                    continue
                
                # Calculate confidence based on spaCy's confidence
                confidence = self._calculate_confidence(ent)
                
                # Get bounding box if OCR words provided
                bounding_box = self._get_bounding_box(ent, ocr_words) if ocr_words else None
                
                entities.append(Entity(
                    entity_type=entity_type,
                    text=ent.text,
                    confidence=confidence,
                    bounding_box=bounding_box,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                ))
            
            return NERResult(
                document_id="",  # Will be set by caller
                entities=entities,
                model_used=self.model_name,
            )
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return NERResult(
                document_id="",
                entities=[],
                model_used=self.model_name,
            )
    
    def _map_entity_type(self, spacy_label: str) -> Optional[EntityType]:
        """
        Map spaCy entity labels to our EntityType enum.
        
        Args:
            spacy_label: spaCy entity label (e.g., 'PERSON', 'ORG')
            
        Returns:
            EntityType or None if not mapped
        """
        mapping = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORG,
            "DATE": EntityType.DATE,
            "GPE": EntityType.GPE,
            "LOC": EntityType.GPE,
            "MONEY": EntityType.MONEY,
            "CARDINAL": EntityType.CARDINAL,
            "QUANTITY": EntityType.CARDINAL,
        }
        
        return mapping.get(spacy_label)
    
    def _calculate_confidence(self, ent) -> float:
        """
        Calculate confidence score for entity.
        
        spaCy doesn't provide direct confidence scores, so we estimate
        based on entity characteristics.
        
        Args:
            ent: spaCy entity
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.85
        
        # Increase confidence for longer entities (less likely to be false positives)
        if len(ent.text) > 10:
            confidence += 0.05
        
        # Increase confidence for well-known patterns
        if ent.label_ in ["PERSON", "ORG", "DATE"]:
            confidence += 0.05
        
        # Decrease confidence for very short entities
        if len(ent.text) < 3:
            confidence -= 0.15
        
        # Decrease confidence for entities with numbers (more likely to be false positives)
        if any(char.isdigit() for char in ent.text) and ent.label_ not in ["DATE", "MONEY", "CARDINAL"]:
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def _get_bounding_box(
        self,
        ent,
        ocr_words: List[dict],
    ) -> Optional[dict]:
        """
        Get bounding box for entity by matching to OCR words.
        
        Args:
            ent: spaCy entity
            ocr_words: List of OCR words with bounding boxes
            
        Returns:
            Bounding box dict or None if not found
        """
        # Find OCR words that overlap with entity
        entity_start = ent.start_char
        entity_end = ent.end_char
        
        matching_words = []
        for word in ocr_words:
            # Simple character position matching
            # In production, you'd want more sophisticated matching
            word_start = word.get("start_char", 0)
            word_end = word.get("end_char", 0)
            
            if word_start >= entity_start and word_end <= entity_end:
                matching_words.append(word)
        
        if not matching_words:
            return None
        
        # Calculate bounding box from matching words
        min_x = min(w["bounding_box"]["x"] for w in matching_words)
        min_y = min(w["bounding_box"]["y"] for w in matching_words)
        max_x = max(
            w["bounding_box"]["x"] + w["bounding_box"]["width"]
            for w in matching_words
        )
        max_y = max(
            w["bounding_box"]["y"] + w["bounding_box"]["height"]
            for w in matching_words
        )
        
        return {
            "x": min_x,
            "y": min_y,
            "width": max_x - min_x,
            "height": max_y - min_y,
        }
    
    def extract_emails(self, text: str) -> List[Entity]:
        """
        Extract email addresses using regex pattern.
        
        Args:
            text: Text to extract emails from
            
        Returns:
            List of email entities
        """
        import re
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.finditer(email_pattern, text)
        
        entities = []
        for match in matches:
            entities.append(Entity(
                entity_type=EntityType.EMAIL,
                text=match.group(),
                confidence=0.95,  # High confidence for regex matches
                bounding_box=None,
                start_char=match.start(),
                end_char=match.end(),
            ))
        
        return entities
    
    def extract_phones(self, text: str) -> List[Entity]:
        """
        Extract phone numbers using regex pattern.
        
        Args:
            text: Text to extract phones from
            
        Returns:
            List of phone entities
        """
        import re
        
        # Match various phone formats
        phone_pattern = r'''
            (?:                                 # Optional country code
                \+?\d{1,3}[-.\s]?
            )?
            \(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}
        '''
        matches = re.finditer(phone_pattern, text, re.VERBOSE)
        
        entities = []
        for match in matches:
            entities.append(Entity(
                entity_type=EntityType.PHONE,
                text=match.group(),
                confidence=0.90,
                bounding_box=None,
                start_char=match.start(),
                end_char=match.end(),
            ))
        
        return entities


# Singleton instance
_ner_instance: Optional[EntityExtractor] = None


def get_entity_extractor() -> EntityExtractor:
    """Get or create singleton entity extractor instance."""
    global _ner_instance
    if _ner_instance is None:
        _ner_instance = EntityExtractor(
            model_name=settings.ml_ner_model,
        )
    return _ner_instance
