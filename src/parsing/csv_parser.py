"""
Blog 2: CSV Parser

Parses CSV documents with tabular structure preservation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import csv
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedCSVDocument:
    """Parsed CSV document"""
    doc_id: str
    source_path: str
    headers: List[str]
    rows: int
    columns: int
    data_preview: str
    has_headers: bool
    delimiter: str
    quote_char: str
    parsing_quality: float


class CSVParser:
    """Parse CSV documents"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize CSV parser.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.max_preview_rows = self.config.get("max_preview_rows", 10)

    def detect_delimiter(self, file_path: Path) -> str:
        """
        Detect CSV delimiter.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Detected delimiter character
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                sample = f.read(4096)
            
            # Use csv.Sniffer to detect delimiter
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            return delimiter
        
        except Exception as e:
            logger.warning(f"Could not detect delimiter: {e}, using comma")
            return ","

    def parse(self, csv_path: Path, doc_id: str) -> ParsedCSVDocument:
        """
        Parse CSV document.
        
        Args:
            csv_path: Path to CSV file
            doc_id: Document ID
            
        Returns:
            ParsedCSVDocument
        """
        try:
            # Detect delimiter
            delimiter = self.detect_delimiter(csv_path)
            
            # Read CSV file
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f, delimiter=delimiter)
                
                # Read header
                try:
                    headers = next(reader)
                except StopIteration:
                    return ParsedCSVDocument(
                        doc_id=doc_id,
                        source_path=str(csv_path),
                        headers=[],
                        rows=0,
                        columns=0,
                        data_preview="",
                        has_headers=False,
                        delimiter=delimiter,
                        quote_char='"',
                        parsing_quality=0.0
                    )
                
                # Read rows
                rows = []
                for i, row in enumerate(reader):
                    rows.append(row)
                    if i >= self.max_preview_rows - 1:
                        break
            
            # Determine if first row is header
            has_headers = self._is_header_row(headers)
            columns = len(headers)
            
            # Create preview text
            preview_parts = []
            preview_parts.append(" | ".join(headers))
            preview_parts.append("-" * min(len(" | ".join(headers)), 100))
            for row in rows[:self.max_preview_rows]:
                # Pad row to match header length
                padded_row = row + [""] * (columns - len(row))
                preview_parts.append(" | ".join(padded_row[:columns]))
            
            data_preview = "\n".join(preview_parts)
            
            # Count actual rows in file
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f, delimiter=delimiter)
                row_count = sum(1 for _ in reader)
            
            # Adjust row count if headers exist
            if has_headers:
                row_count -= 1
            
            # Calculate quality
            quality = 1.0 if columns > 0 and row_count > 0 else 0.5
            
            return ParsedCSVDocument(
                doc_id=doc_id,
                source_path=str(csv_path),
                headers=headers,
                rows=row_count,
                columns=columns,
                data_preview=data_preview,
                has_headers=has_headers,
                delimiter=delimiter,
                quote_char='"',
                parsing_quality=quality
            )
        
        except Exception as e:
            logger.error(f"Error parsing CSV {csv_path}: {e}")
            return ParsedCSVDocument(
                doc_id=doc_id,
                source_path=str(csv_path),
                headers=[],
                rows=0,
                columns=0,
                data_preview="",
                has_headers=False,
                delimiter=",",
                quote_char='"',
                parsing_quality=0.0
            )

    def _is_header_row(self, row: List[str]) -> bool:
        """
        Heuristic to determine if row is a header.
        
        Args:
            row: First row of CSV
            
        Returns:
            True if likely a header row
        """
        if not row:
            return False
        
        # Check if row contains many non-numeric values (common for headers)
        non_numeric = sum(1 for cell in row if not self._is_numeric(cell))
        return non_numeric / len(row) > 0.5
    
    @staticmethod
    def _is_numeric(value: str) -> bool:
        """Check if value is numeric"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False


def parse_csv(csv_path: Path, doc_id: str, config: Optional[Dict] = None) -> ParsedCSVDocument:
    """
    Convenience function to parse CSV.
    
    Args:
        csv_path: Path to CSV file
        doc_id: Document ID
        config: Optional configuration
        
    Returns:
        ParsedCSVDocument
    """
    parser = CSVParser(config)
    return parser.parse(csv_path, doc_id)
