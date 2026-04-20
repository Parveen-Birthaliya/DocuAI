"""
Blog 2: HTML Parser

Extracts content from HTML documents with structure preservation.
Uses trafilatura for content extraction and BeautifulSoup for structure analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import trafilatura
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
import re

logger = logging.getLogger(__name__)


@dataclass
class HTMLStructure:
    """Extracted HTML structure"""
    title: str
    headings: List[Dict]  # {level, text}
    paragraphs: int
    links: int
    images: int
    tables: int
    lists: int


@dataclass
class ParsedHTMLDocument:
    """Parsed HTML document"""
    doc_id: str
    source_path: str
    title: str
    main_content: str
    structure: Dict
    language: str
    charset: str
    extraction_method: str  # trafilatura or manual
    content_quality: float


class HTMLParser:
    """Parse HTML documents"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize HTML parser.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def extract_structure(self, soup: BeautifulSoup) -> HTMLStructure:
        """
        Extract structural information from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            HTMLStructure with document structure
        """
        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string or ""
        
        # Extract headings with levels
        headings = []
        for heading in soup.find_all(re.compile(r"^h[1-6]$")):
            level = int(heading.name[1])
            text = heading.get_text(strip=True)
            if text:
                headings.append({"level": level, "text": text})
        
        # Count structural elements
        paragraphs = len(soup.find_all("p"))
        links = len(soup.find_all("a"))
        images = len(soup.find_all("img"))
        tables = len(soup.find_all("table"))
        lists = len(soup.find_all(re.compile(r"^[ou]l$")))
        
        return HTMLStructure(
            title=title,
            headings=headings,
            paragraphs=paragraphs,
            links=links,
            images=images,
            tables=tables,
            lists=lists
        )

    def extract_with_trafilatura(self, html_content: str) -> Tuple[str, str]:
        """
        Extract content using trafilatura.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Tuple of (extracted text, extracted markdown)
        """
        try:
            # Extract main content
            content = trafilatura.extract(html_content, output_format="txt")
            markdown = trafilatura.extract(html_content, output_format="markdown")
            
            return content or "", markdown or ""
            
        except Exception as e:
            logger.error(f"Trafilatura extraction failed: {e}")
            return "", ""

    def extract_with_beautifulsoup(self, html_content: str) -> str:
        """
        Fallback extraction using BeautifulSoup.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Extracted text
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script and style tags
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            
            # Extract text
            text = soup.get_text(separator="\n", strip=True)
            
            return text
            
        except Exception as e:
            logger.error(f"BeautifulSoup extraction failed: {e}")
            return ""

    def extract_metadata(self, html_content: str, soup: BeautifulSoup) -> Dict:
        """
        Extract metadata from HTML.
        
        Args:
            html_content: Raw HTML content
            soup: BeautifulSoup object
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Language
        if soup.html and soup.html.get("lang"):
            metadata["language"] = soup.html.get("lang")
        
        # Charset via meta tag
        charset_meta = soup.find("meta", charset=True)
        if charset_meta:
            metadata["charset"] = charset_meta.get("charset")
        else:
            metadata["charset"] = "utf-8"
        
        # Description
        desc_meta = soup.find("meta", attrs={"name": "description"})
        if desc_meta:
            metadata["description"] = desc_meta.get("content", "")
        
        # Keywords
        keywords_meta = soup.find("meta", attrs={"name": "keywords"})
        if keywords_meta:
            metadata["keywords"] = keywords_meta.get("content", "")
        
        return metadata

    def calculate_content_quality(self, text: str, structure: HTMLStructure) -> float:
        """
        Calculate content quality score.
        
        Args:
            text: Extracted text
            structure: HTMLStructure
            
        Returns:
            Quality score 0-1.0
        """
        if not text:
            return 0.0
        
        text_length = len(text)
        
        # Check text length
        if text_length < 100:
            return 0.2
        elif text_length > 1000000:
            return 0.3
        
        # Check structure quality
        structure_score = 0.5
        
        if structure.headings:
            structure_score += 0.2  # Has heading hierarchy
        
        if structure.paragraphs > 0:
            structure_score += 0.1  # Has paragraphs
        
        if structure.tables > 0:
            structure_score += 0.1  # Has structured data
        
        # Check for excessive links/ads (low content ratio)
        link_density = structure.links / max(structure.paragraphs, 1)
        if link_density > 2:
            structure_score -= 0.2  # Too many links, likely navigation
        
        return min(structure_score, 1.0)

    def parse(self, html_path: Path, doc_id: str) -> ParsedHTMLDocument:
        """
        Parse HTML document.
        
        Args:
            html_path: Path to HTML file
            doc_id: Document ID
            
        Returns:
            ParsedHTMLDocument
        """
        try:
            with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()
        except Exception as e:
            logger.error(f"Error reading HTML file {html_path}: {e}")
            return ParsedHTMLDocument(
                doc_id=doc_id,
                source_path=str(html_path),
                title="",
                main_content="",
                structure={},
                language="unknown",
                charset="utf-8",
                extraction_method="none",
                content_quality=0.0
            )
        
        # Parse with BeautifulSoup for structure
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract structure
        structure = self.extract_structure(soup)
        
        # Extract metadata
        metadata = self.extract_metadata(html_content, soup)
        
        # Try trafilatura first
        content, _ = self.extract_with_trafilatura(html_content)
        extraction_method = "trafilatura"
        
        # Fallback to BeautifulSoup if trafilatura fails
        if not content or len(content) < 50:
            content = self.extract_with_beautifulsoup(html_content)
            extraction_method = "beautifulsoup"
        
        # Calculate quality
        quality = self.calculate_content_quality(content, structure)
        
        return ParsedHTMLDocument(
            doc_id=doc_id,
            source_path=str(html_path),
            title=structure.title,
            main_content=content,
            structure={
                "headings": structure.headings,
                "paragraphs": structure.paragraphs,
                "links": structure.links,
                "images": structure.images,
                "tables": structure.tables,
                "lists": structure.lists
            },
            language=metadata.get("language", "unknown"),
            charset=metadata.get("charset", "utf-8"),
            extraction_method=extraction_method,
            content_quality=quality
        )


def parse_html(html_path: Path, doc_id: str, config: Optional[Dict] = None) -> ParsedHTMLDocument:
    """
    Convenience function to parse HTML.
    
    Args:
        html_path: Path to HTML file
        doc_id: Document ID
        config: Optional configuration
        
    Returns:
        ParsedHTMLDocument
    """
    parser = HTMLParser(config)
    return parser.parse(html_path, doc_id)
