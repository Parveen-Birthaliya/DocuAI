"""
Blog 2: PDF OCR Parser

Handles scanned PDF documents using Tesseract OCR.
Performs preprocessing, OCR, and confidence scoring.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import fitz  # PyMuPDF
import cv2
import numpy as np
import pytesseract
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result from OCR processing"""
    page_num: int
    text: str
    confidence: float
    num_blocks: int
    image_quality: float


@dataclass
class ParsedOCRDocument:
    """Parsed scanned PDF document"""
    doc_id: str
    source_path: str
    total_pages: int
    total_text: str
    ocr_results: List[Dict]
    average_confidence: float
    average_image_quality: float
    languages_detected: List[str]


class PDFOCRParser:
    """Parse scanned PDFs using OCR"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize OCR parser.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.language = self.config.get("language", "eng")
        self.confidence_threshold = self.config.get("confidence_threshold", 50)
        self.preprocess = self.config.get("preprocess", True)

    def image_to_pdf_page(self, pdf_path: Path, page_num: int) -> Optional[np.ndarray]:
        """
        Convert PDF page to image.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            
        Returns:
            Image as numpy array or None if failed
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            
            # Render page to image (300 DPI for better OCR)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            image_array = np.frombuffer(pix.samples, dtype=np.uint8)
            image_array = image_array.reshape(pix.height, pix.width, pix.n)
            
            # Convert RGBA to BGR if needed
            if pix.n == 4:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            doc.close()
            return image_array
            
        except Exception as e:
            logger.error(f"Error converting PDF page {page_num} to image: {e}")
            return None

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply bilateral filter to reduce noise while keeping edges
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Threshold to binary
        _, binary = cv2.threshold(denoised, 150, 255, cv2.THRESH_BINARY)
        
        return binary

    def extract_image_quality(self, image: np.ndarray) -> float:
        """
        Estimate image quality for OCR.
        
        Args:
            image: Input image
            
        Returns:
            Quality score 0-1.0
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Estimate sharpness using Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize to 0-1.0 range (assume good sharpness is > 100)
        quality = min(laplacian_var / 500, 1.0)
        
        return max(0.0, quality)

    def ocr_page(self, image: np.ndarray) -> Dict:
        """
        Perform OCR on image.
        
        Args:
            image: Input image
            
        Returns:
            Dictionary with OCR results
        """
        try:
            # Optional preprocessing
            if self.preprocess:
                image = self.preprocess_image(image)
            
            # Perform OCR using pytesseract
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text with confidence
            text = ""
            confidences = []
            num_blocks = 0
            
            for i in range(len(data["text"])):
                if int(data["conf"][i]) > self.confidence_threshold:
                    text += data["text"][i] + " "
                    confidences.append(int(data["conf"][i]))
                    num_blocks += 1
            
            # Calculate average confidence
            avg_confidence = np.mean(confidences) if confidences else 0
            
            return {
                "text": text.strip(),
                "confidence": float(avg_confidence),
                "num_blocks": num_blocks,
                "total_words": len(data["text"])
            }
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "num_blocks": 0,
                "total_words": 0
            }

    def parse(self, pdf_path: Path, doc_id: str) -> ParsedOCRDocument:
        """
        Parse scanned PDF using OCR.
        
        Args:
            pdf_path: Path to PDF file
            doc_id: Document ID
            
        Returns:
            ParsedOCRDocument with OCR results
        """
        try:
            doc = fitz.open(pdf_path)
            total_pages = doc.page_count
            doc.close()
            
        except Exception as e:
            logger.error(f"Error opening PDF {pdf_path}: {e}")
            return ParsedOCRDocument(
                doc_id=doc_id,
                source_path=str(pdf_path),
                total_pages=0,
                total_text="",
                ocr_results=[],
                average_confidence=0.0,
                average_image_quality=0.0,
                languages_detected=[]
            )
        
        ocr_results = []
        all_text = []
        confidences = []
        image_qualities = []
        
        for page_num in range(total_pages):
            # Convert page to image
            image = self.image_to_pdf_page(pdf_path, page_num)
            
            if image is None:
                continue
            
            # Extract quality
            quality = self.extract_image_quality(image)
            image_qualities.append(quality)
            
            # Perform OCR
            ocr_data = self.ocr_page(image)
            text = ocr_data["text"]
            confidence = ocr_data["confidence"]
            
            all_text.append(text)
            confidences.append(confidence)
            
            result = OCRResult(
                page_num=page_num,
                text=text,
                confidence=confidence,
                num_blocks=ocr_data["num_blocks"],
                image_quality=quality
            )
            
            ocr_results.append(asdict(result))
        
        # Calculate averages
        avg_confidence = np.mean(confidences) if confidences else 0
        avg_quality = np.mean(image_qualities) if image_qualities else 0
        
        total_text = "\n[PAGE_BREAK]\n".join(all_text)
        
        return ParsedOCRDocument(
            doc_id=doc_id,
            source_path=str(pdf_path),
            total_pages=total_pages,
            total_text=total_text,
            ocr_results=ocr_results,
            average_confidence=float(avg_confidence),
            average_image_quality=float(avg_quality),
            languages_detected=[self.language]
        )


def parse_pdf_ocr(pdf_path: Path, doc_id: str, config: Optional[Dict] = None) -> ParsedOCRDocument:
    """
    Convenience function to parse scanned PDF.
    
    Args:
        pdf_path: Path to PDF file
        doc_id: Document ID
        config: Optional configuration
        
    Returns:
        ParsedOCRDocument
    """
    parser = PDFOCRParser(config)
    return parser.parse(pdf_path, doc_id)
