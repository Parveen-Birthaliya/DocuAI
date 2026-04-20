"""
Blog 2: PDF Text Parser

Extracts text from PDF documents with layout awareness and reading order reconstruction.
Handles multi-column layouts by detecting column boundaries and extracting text in proper reading order.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import fitz  # PyMuPDF
import re
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a block of text with position information"""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    font_size: float
    font_name: str
    is_bold: bool
    block_index: int


@dataclass
class ParsedPDFDocument:
    """Parsed PDF document with extracted content and metadata"""
    doc_id: str
    source_path: str
    total_pages: int
    total_text: str
    blocks: List[Dict]
    column_count: int
    has_headers_footers: bool
    reading_order: List[int]
    extraction_quality: float


class PDFTextParser:
    """Parse text-based PDFs with layout awareness"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize PDF parser.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.column_threshold = self.config.get("column_threshold", 50)
        self.min_block_width = self.config.get("min_block_width", 50)

    def extract_blocks(self, pdf_path: Path) -> Tuple[List[TextBlock], int]:
        """
        Extract text blocks from PDF with position information.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (text blocks list, page count)
        """
        blocks = []
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = doc.page_count
            block_index = 0
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # Extract blocks from page
                for block_data in page.get_text("dict")["blocks"]:
                    if block_data["type"] == 0:  # Text block
                        bbox = block_data["bbox"]
                        
                        for line in block_data.get("lines", []):
                            line_text = ""
                            font_size = 0
                            font_name = "unknown"
                            is_bold = False
                            
                            for span in line.get("spans", []):
                                line_text += span.get("text", "")
                                font_size = span.get("size", 0)
                                font_name = span.get("font", "unknown")
                                is_bold = "Bold" in font_name
                            
                            if line_text.strip():
                                block = TextBlock(
                                    text=line_text.strip(),
                                    x0=bbox[0],
                                    y0=bbox[1],
                                    x1=bbox[2],
                                    y1=bbox[3],
                                    font_size=font_size,
                                    font_name=font_name,
                                    is_bold=is_bold,
                                    block_index=block_index
                                )
                                blocks.append(block)
                                block_index += 1
                
                # Add page break marker
                blocks.append(TextBlock(
                    text="\n[PAGE_BREAK]\n",
                    x0=0, y0=0, x1=0, y1=0,
                    font_size=0,
                    font_name="marker",
                    is_bold=False,
                    block_index=block_index
                ))
                block_index += 1
            
            doc.close()
            return blocks, total_pages
            
        except Exception as e:
            logger.error(f"Error extracting blocks from {pdf_path}: {e}")
            return [], 0

    def detect_columns(self, blocks: List[TextBlock]) -> int:
        """
        Detect number of columns in document.
        
        Args:
            blocks: List of text blocks
            
        Returns:
            Estimated column count
        """
        if not blocks:
            return 1
        
        # Analyze x0 positions to detect column structure
        x_positions = sorted(set(int(b.x0 / self.column_threshold) for b in blocks))
        
        # Simple heuristic: if we have multiple distinct x positions, we have columns
        column_count = len(x_positions)
        
        return min(column_count, 4)  # Cap at 4 columns

    def reconstruct_reading_order(self, blocks: List[TextBlock]) -> List[int]:
        """
        Reconstruct proper reading order for blocks.
        
        For single column: top-to-bottom
        For multi-column: left-to-right (each column), then next row
        
        Args:
            blocks: List of text blocks
            
        Returns:
            List of block indices in reading order
        """
        if not blocks:
            return []
        
        # Sort by y position (top to bottom) then x position (left to right)
        indexed_blocks = [(i, b) for i, b in enumerate(blocks)]
        
        # Group by approximate y position (with tolerance)
        y_position = 0
        rows = []
        current_row = []
        tolerance = 15
        
        for idx, block in indexed_blocks:
            if not current_row:
                current_row.append((idx, block))
                y_position = block.y0
            elif abs(block.y0 - y_position) < tolerance:
                current_row.append((idx, block))
            else:
                # Sort current row by x position (left to right)
                current_row.sort(key=lambda x: x[1].x0)
                rows.append([idx for idx, _ in current_row])
                current_row = [(idx, block)]
                y_position = block.y0
        
        # Sort final row
        if current_row:
            current_row.sort(key=lambda x: x[1].x0)
            rows.append([idx for idx, _ in current_row])
        
        # Flatten rows
        reading_order = [idx for row in rows for idx in row]
        return reading_order

    def extract_quality_metrics(self, blocks: List[TextBlock]) -> float:
        """
        Calculate text extraction quality.
        
        Args:
            blocks: List of text blocks
            
        Returns:
            Quality score 0-1.0
        """
        if not blocks:
            return 0.0
        
        total_chars = sum(len(b.text) for b in blocks)
        
        # Check for reasonable character count
        if total_chars < 100:
            return 0.2
        elif total_chars > 1000000:
            return 0.3  # Suspiciously large
        
        # Check for text diversity (not just repeated characters)
        text = "".join(b.text for b in blocks)
        unique_chars = len(set(text))
        char_diversity = unique_chars / len(text) if text else 0
        
        # Should have decent character diversity
        quality = min(char_diversity, 1.0)
        return quality

    def parse(self, pdf_path: Path, doc_id: str) -> ParsedPDFDocument:
        """
        Parse PDF document.
        
        Args:
            pdf_path: Path to PDF file
            doc_id: Document ID
            
        Returns:
            ParsedPDFDocument with extracted content
        """
        # Extract blocks
        blocks, total_pages = self.extract_blocks(pdf_path)
        
        if not blocks:
            logger.warning(f"No text extracted from {pdf_path}")
            return ParsedPDFDocument(
                doc_id=doc_id,
                source_path=str(pdf_path),
                total_pages=total_pages,
                total_text="",
                blocks=[],
                column_count=1,
                has_headers_footers=False,
                reading_order=[],
                extraction_quality=0.0
            )
        
        # Detect layout
        column_count = self.detect_columns(blocks)
        
        # Reconstruct reading order
        reading_order = self.reconstruct_reading_order(blocks)
        
        # Extract text in reading order
        total_text = "\n".join(blocks[i].text for i in reading_order if i < len(blocks))
        
        # Calculate quality
        quality = self.extract_quality_metrics(blocks)
        
        # Check for headers/footers (blocks at top/bottom of page)
        has_headers_footers = any(
            b.y0 < 50 or b.y1 > 550 for b in blocks if b.text != "\n[PAGE_BREAK]\n"
        )
        
        return ParsedPDFDocument(
            doc_id=doc_id,
            source_path=str(pdf_path),
            total_pages=total_pages,
            total_text=total_text,
            blocks=[asdict(b) for b in blocks],
            column_count=column_count,
            has_headers_footers=has_headers_footers,
            reading_order=reading_order,
            extraction_quality=quality
        )


def parse_pdf_text(pdf_path: Path, doc_id: str, config: Optional[Dict] = None) -> ParsedPDFDocument:
    """
    Convenience function to parse PDF text.
    
    Args:
        pdf_path: Path to PDF file
        doc_id: Document ID
        config: Optional configuration
        
    Returns:
        ParsedPDFDocument
    """
    parser = PDFTextParser(config)
    return parser.parse(pdf_path, doc_id)
