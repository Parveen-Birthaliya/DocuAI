"""
Blog 2: Format-Aware Parsing

Parses documents according to their format and routing tags from Blog 1.
Supports 8 different formats with format-specific optimization.
"""

from .parser import FormatAwareParser, run_parsing, ParsedDocument
from .pdf_parser import PDFTextParser, parse_pdf_text, ParsedPDFDocument
from .pdf_ocr_parser import PDFOCRParser, parse_pdf_ocr, ParsedOCRDocument
from .html_parser import HTMLParser, parse_html, ParsedHTMLDocument
from .json_parser import JSONParser, parse_json, ParsedJSONDocument
from .csv_parser import CSVParser, parse_csv, ParsedCSVDocument
from .simple_parsers import (
    PlainTextParser, parse_plaintext, ParsedPlainTextDocument,
    MarkdownParser, parse_markdown, ParsedMarkdownDocument,
    PythonCodeParser, parse_python, ParsedCodeDocument
)

__all__ = [
    # Main orchestrator
    "FormatAwareParser",
    "run_parsing",
    "ParsedDocument",
    
    # PDF parsers
    "PDFTextParser",
    "parse_pdf_text",
    "ParsedPDFDocument",
    "PDFOCRParser",
    "parse_pdf_ocr",
    "ParsedOCRDocument",
    
    # HTML parser
    "HTMLParser",
    "parse_html",
    "ParsedHTMLDocument",
    
    # JSON parser
    "JSONParser",
    "parse_json",
    "ParsedJSONDocument",
    
    # CSV parser
    "CSVParser",
    "parse_csv",
    "ParsedCSVDocument",
    
    # Simple parsers
    "PlainTextParser",
    "parse_plaintext",
    "ParsedPlainTextDocument",
    "MarkdownParser",
    "parse_markdown",
    "ParsedMarkdownDocument",
    "PythonCodeParser",
    "parse_python",
    "ParsedCodeDocument",
]