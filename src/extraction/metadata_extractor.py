"""
Blog 4: Metadata and Entity Extraction

Extract metadata, named entities, and structured information from documents.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedMetadata:
    """Extracted document metadata"""
    title: Optional[str]
    authors: List[str]
    date_published: Optional[str]
    keywords: List[str]
    summary: Optional[str]
    language: str
    entities: Dict[str, List[str]]  # entity_type -> list of values


class EntityExtractor:
    """Extract named entities and metadata"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.entity_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "url": r'https?://[^\s]+',
            "phone": r'(?:\+\d{1,3}[-.]?)?\(?(\d{3})\)?[-.]?(\d{3})[-.]?(\d{4})',
            "date": r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b',
            "number": r'\b\d+(?:\.\d+)?\b',
        }

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        matches = re.findall(self.entity_patterns["email"], text)
        return list(set(matches))

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs"""
        matches = re.findall(self.entity_patterns["url"], text)
        return list(set(matches))

    def extract_dates(self, text: str) -> List[str]:
        """Extract dates"""
        matches = re.findall(self.entity_patterns["date"], text)
        return list(set(matches))

    def extract_organizations(self, text: str) -> List[str]:
        """Extract potential organization names (capitalized phrases)"""
        # Look for capitalized multi-word phrases
        pattern = r'\b(?:[A-Z][a-z]+ ){1,3}(?:Inc|Corp|Ltd|LLC|University|Bank|School|Company|Group|Systems|Technologies)\b'
        matches = re.findall(pattern, text)
        return list(set(matches))

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract all named entities"""
        entities = {
            "emails": self.extract_emails(text),
            "urls": self.extract_urls(text),
            "dates": self.extract_dates(text),
            "organizations": self.extract_organizations(text),
        }
        
        # Remove duplicates and sort
        for entity_type in entities:
            entities[entity_type] = sorted(list(set(entities[entity_type])))
        
        return entities

    def extract_title(self, text: str) -> Optional[str]:
        """Extract document title (usually first line or first heading)"""
        lines = text.split('\n')
        
        # Look for markdown heading
        for line in lines[:10]:
            if line.startswith('#'):
                return line.lstrip('#').strip()
        
        # Otherwise, first substantial line
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                return line
        
        return None

    def extract_authors(self, text: str) -> List[str]:
        """Extract author names"""
        authors = []
        
        # Look for "by Author" or "Author:"patterns
        author_pattern = r'(?:by|author|authors?):\s*([^,\n]+(?:,\s*[^,\n]+)*)'
        matches = re.finditer(author_pattern, text[:1000], re.IGNORECASE)
        
        for match in matches:
            author_text = match.group(1)
            # Split by comma
            names = [name.strip() for name in author_text.split(',')]
            authors.extend(names)
        
        return list(set(authors))[:5]  # Limit to 5 authors

    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords/tags"""
        keywords = []
        
        # Look for "keywords:" or "tags:" sections
        keyword_pattern = r'(?:keywords?|tags?):\s*([^\n]+)'
        matches = re.finditer(keyword_pattern, text, re.IGNORECASE)
        
        for match in matches:
            keyword_text = match.group(1)
            # Split by comma or space
            kws = [kw.strip() for kw in re.split(r'[,;]', keyword_text)]
            keywords.extend(kws)
        
        return list(set(keywords))[:10]  # Limit to 10


class MetadataExtractor:
    """Extract and infer document metadata"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.entity_extractor = EntityExtractor(config)

    def extract_metadata(self, text: str, doc_id: str = "", 
                        format_type: str = "") -> ExtractedMetadata:
        """
        Extract metadata from text.
        
        Args:
            text: Document text
            doc_id: Document ID (used as fallback title)
            format_type: Document format
            
        Returns:
            ExtractedMetadata
        """
        title = self.entity_extractor.extract_title(text)
        if not title:
            title = doc_id or "Untitled"
        
        authors = self.entity_extractor.extract_authors(text)
        dates = self.entity_extractor.extract_dates(text)
        date_published = dates[0] if dates else None
        keywords = self.entity_extractor.extract_keywords(text)
        
        entities = self.entity_extractor.extract_entities(text)
        
        # Extract summary (first substantial paragraph)
        summary = self._extract_summary(text)
        
        # Estimate language
        language = self._detect_language(text)
        
        return ExtractedMetadata(
            title=title,
            authors=authors,
            date_published=date_published,
            keywords=keywords,
            summary=summary,
            language=language,
            entities=entities
        )

    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract first substantial paragraph as summary"""
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50 and len(para) < 500:
                return para
        
        return None

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on common words"""
        # Check for common words in different languages
        english_words = {'the', 'and', 'is', 'that', 'to', 'of', 'in', 'a', 'it', 'for'}
        spanish_words = {'el', 'y', 'es', 'de', 'que', 'en', 'la', 'a', 'por', 'para'}
        french_words = {'le', 'et', 'est', 'de', 'que', 'en', 'la', 'un', 'par', 'pour'}
        
        words = set(text.lower().split()[:100])
        
        en_match = len(words & english_words)
        es_match = len(words & spanish_words)
        fr_match = len(words & french_words)
        
        if max(en_match, es_match, fr_match) == 0:
            return "unknown"
        
        if en_match >= es_match and en_match >= fr_match:
            return "en"
        elif es_match >= fr_match:
            return "es"
        else:
            return "fr"


def extract_metadata(text: str, doc_id: str = "", config: Dict = None) -> ExtractedMetadata:
    """Extract metadata from text"""
    extractor = MetadataExtractor(config)
    return extractor.extract_metadata(text, doc_id)
