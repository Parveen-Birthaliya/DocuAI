"""
PDF-specific audit checks.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from src.utils import logger


def audit_pdf(file_path: Path) -> Dict[str, Any]:
    """
    Audit a PDF document.
    
    Checks:
    - Page count
    - Encrypted/protected
    - Text extraction capability
    - Layout complexity
    
    Args:
        file_path: Path to PDF
    
    Returns:
        Audit results dict
    """
    file_path = Path(file_path)
    audit = {
        "page_count": 0,
        "is_encrypted": False,
        "has_text": False,
        "layout_complexity": "simple",
        "errors": [],
    }
    
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not installed, PDF audit skipped")
        return audit
    
    try:
        doc = fitz.open(file_path)
        
        audit["page_count"] = len(doc)
        audit["is_encrypted"] = doc.is_encrypted
        
        # Check for text
        total_chars = 0
        text_percentages = []
        
        for page in doc:
            text = page.get_text("text")
            total_chars += len(text) if text else 0
            
            if page.get_text():
                text_percentages.append(1.0)
            else:
                text_percentages.append(0.0)
        
        audit["has_text"] = total_chars > 100
        
        # Layout complexity: check if pages have text in different x-positions (columns)
        if len(doc) > 0:
            page = doc[0]
            blocks = page.get_text("blocks")
            
            # Get x-coordinates of text blocks
            x_coords = [
                (block[0] + block[2]) / 2  # center x
                for block in blocks
                if block[6] == 0 and block[4].strip()  # text blocks only
            ]
            
            if x_coords:
                # Check if spread across page (suggests multi-column)
                min_x = min(x_coords)
                max_x = max(x_coords)
                spread = max_x - min_x
                page_width = page.rect.width
                
                # If text spans > 60% of width with gap in middle, likely columns
                if spread > page_width * 0.6:
                    audit["layout_complexity"] = "multi_column"
                
                # Check for presence of lines/tables
                lines = page.get_drawings()
                if len(lines) > 10:
                    audit["layout_complexity"] = "table_heavy"
            
            # Check for images
            images = page.get_images()
            if len(images) > 5:
                audit["layout_complexity"] = "diagram_heavy"
        
        doc.close()
        
        logger.debug(f"PDF audit complete: {file_path.name} → {audit}")
        return audit
    
    except Exception as e:
        audit["errors"].append(str(e))
        logger.warning(f"PDF audit failed: {e}")
        return audit


def check_ocr_quality(text: str) -> Optional[float]:
    """
    Check OCR quality by analyzing character patterns.
    
    High OCR quality → clean text (few garbage chars)
    Low OCR quality → lots of ~$@#^ symbols
    
    Returns:
        Quality indicator 0-1, or None if can't determine
    """
    if not text or len(text) < 100:
        return None
    
    # Count "good" characters (alphanumeric, common punctuation)
    good_chars = sum(
        1 for c in text
        if c.isalnum() or c in " .,!?'-\"();:\n\t"
    )
    
    # OCR quality ratio
    quality = good_chars / len(text)
    
    logger.debug(f"OCR quality: {quality:.2f}")
    return round(quality, 3)
