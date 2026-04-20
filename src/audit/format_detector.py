"""
Format detection for documents.
Identifies file format from extension and magic bytes.
"""

import magic
from pathlib import Path
from typing import Optional, Dict, Any
import json
from src.utils import logger


class FormatDetector:
    """Detects document format from file extension and magic bytes."""
    
    # Supported formats
    FORMATS = {
        "pdf": "application/pdf",
        "html": "text/html",
        "json": "application/json",
        "csv": "text/csv",
        "txt": "text/plain",
        "md": "text/markdown",
        "py": "text/x-python",
    }
    
    # Extension to format mapping
    EXTENSION_MAP = {
        ".pdf": "pdf",
        ".html": "html",
        ".htm": "html",
        ".json": "json",
        ".csv": "csv",
        ".txt": "txt",
        ".md": "md",
        ".markdown": "md",
        ".py": "py",
    }
    
    def __init__(self):
        """Initialize format detector."""
        self.mime = magic.Magic(mime=True)
    
    def detect_format(self, file_path: Path) -> Optional[str]:
        """
        Detect format from file.
        
        Tries: extension → magic bytes → fallback to txt
        
        Args:
            file_path: Path to file
        
        Returns:
            Format string (pdf, html, json, etc.) or None
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        
        # Method 1: Check extension
        ext = file_path.suffix.lower()
        if ext in self.EXTENSION_MAP:
            format_type = self.EXTENSION_MAP[ext]
            logger.debug(f"Format detected (extension): {file_path.name} → {format_type}")
            return format_type
        
        # Method 2: Use magic bytes (MIME type)
        try:
            mime_type = self.mime.from_file(str(file_path))
            for fmt, mime in self.FORMATS.items():
                if mime in mime_type:
                    logger.debug(f"Format detected (MIME): {file_path.name} → {fmt}")
                    return fmt
        except Exception as e:
            logger.debug(f"Magic detection failed for {file_path}: {e}")
        
        # Method 3: Try to parse as JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            logger.debug(f"Format detected (JSON parse): {file_path.name} → json")
            return "json"
        except:
            pass
        
        # Fallback: treat as text
        logger.debug(f"Format detected (fallback): {file_path.name} → txt")
        return "txt"
    
    def classify_pdf(self, file_path: Path) -> str:
        """
        Classify PDF as text-extractable or scanned.
        
        Returns:
            "pdf_text" (direct extraction viable)
            "pdf_scanned" (needs OCR)
            "pdf_image_only" (images, no text)
        """
        file_path = Path(file_path)
        
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.warning("PyMuPDF not installed, assuming pdf_text")
            return "pdf_text"
        
        try:
            doc = fitz.open(file_path)
            
            total_chars = 0
            total_image_area = 0.0
            
            for page in doc:
                text = page.get_text("text")
                total_chars += len(text) if text else 0
                
                # Calculate image area
                for img in page.get_images():
                    try:
                        # img = (xref, smask, width, height, ...)
                        total_image_area += img[2] * img[3]
                    except:
                        pass
            
            doc.close()
            
            # Classification logic
            if total_chars < 100:
                if total_image_area > 0:
                    result = "pdf_image_only"
                else:
                    result = "pdf_image_only"
            else:
                # Char density: chars per pixel area
                char_density = total_chars / max(total_image_area, 1.0)
                if char_density < 0.001:
                    result = "pdf_scanned"
                else:
                    result = "pdf_text"
            
            logger.debug(
                f"PDF classified: {file_path.name} → {result} "
                f"(chars={total_chars}, images={total_image_area})"
            )
            return result
        
        except Exception as e:
            logger.warning(f"PDF classification failed: {e}, assuming pdf_text")
            return "pdf_text"
    
    def classify_html(self, file_path: Path) -> Dict[str, Any]:
        """
        Classify HTML by measuring content ratio (signal vs boilerplate).
        
        Returns:
            {"classification": "high_content" | "high_boilerplate" | "mixed",
             "content_ratio": float (0-1)}
        """
        file_path = Path(file_path)
        
        try:
            import trafilatura
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("trafilatura/BeautifulSoup not installed")
            return {"classification": "unknown", "content_ratio": 0.5}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # Extract main content
            extracted = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=False,
            ) or ""
            
            # Get total text
            soup = BeautifulSoup(html_content, "lxml")
            total_text = soup.get_text(separator=" ", strip=True)
            
            # Calculate ratio
            if len(total_text) == 0:
                content_ratio = 0.0
            else:
                content_ratio = len(extracted) / len(total_text)
            
            # Classify
            if content_ratio > 0.7:
                classification = "high_content"
            elif content_ratio < 0.15:
                classification = "high_boilerplate"
            else:
                classification = "mixed"
            
            logger.debug(
                f"HTML classified: {file_path.name} → {classification} "
                f"(ratio={content_ratio:.2f})"
            )
            
            return {
                "classification": classification,
                "content_ratio": round(content_ratio, 3),
            }
        
        except Exception as e:
            logger.warning(f"HTML classification failed: {e}")
            return {"classification": "unknown", "content_ratio": 0.5}


# Global instance
_detector: Optional[FormatDetector] = None


def get_detector() -> FormatDetector:
    """Get singleton format detector."""
    global _detector
    if _detector is None:
        _detector = FormatDetector()
    return _detector
