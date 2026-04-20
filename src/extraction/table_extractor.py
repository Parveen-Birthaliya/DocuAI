"""
Blog 4: Table Extraction

Extract and preserve table structures from documents.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTable:
    """Extracted table data"""
    table_id: str
    headers: List[str]
    rows: List[List[str]]
    row_count: int
    column_count: int
    table_type: str  # "structured", "text_based", "inferred"
    confidence: float
    context: str  # Text around table


class TableExtractor:
    """Extract tables from text"""

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def extract_markdown_tables(self, text: str) -> List[ExtractedTable]:
        """Extract Markdown formatted tables"""
        tables = []
        table_pattern = r'\|.*?\|(?:\n\|(?:[-\s|:]+)\|)?(?:\n\|.*?\|)+?'
        
        for match in re.finditer(table_pattern, text):
            table_text = match.group(0)
            lines = table_text.strip().split('\n')
            
            if len(lines) < 2:
                continue
            
            # Parse headers
            headers = [h.strip() for h in lines[0].split('|')[1:-1]]
            
            # Parse rows
            rows = []
            for line in lines[2:]:  # Skip header and separator
                row = [cell.strip() for cell in line.split('|')[1:-1]]
                if row:
                    rows.append(row)
            
            if rows and headers:
                table = ExtractedTable(
                    table_id=f"table_{len(tables)}",
                    headers=headers,
                    rows=rows,
                    row_count=len(rows),
                    column_count=len(headers),
                    table_type="structured",
                    confidence=0.95,
                    context=text[max(0, match.start()-100):match.end()+100]
                )
                tables.append(table)
        
        return tables

    def extract_csv_like_tables(self, text: str) -> List[ExtractedTable]:
        """Extract comma/pipe-separated tables"""
        tables = []
        lines = text.split('\n')
        
        in_table = False
        table_lines = []
        
        for line in lines:
            # Check if line looks like a table row
            if '|' in line or (',' in line and line.count(',') > 2):
                if not in_table:
                    in_table = True
                    table_lines = [line]
                else:
                    table_lines.append(line)
            else:
                if in_table and table_lines:
                    # Process accumulated table
                    table = self._parse_table_lines(table_lines)
                    if table:
                        table.table_id = f"table_{len(tables)}"
                        tables.append(table)
                    in_table = False
                    table_lines = []
        
        return tables

    def _parse_table_lines(self, lines: List[str]) -> Optional[ExtractedTable]:
        """Parse raw table lines into table structure"""
        if len(lines) < 2:
            return None
        
        # Detect delimiter
        if '|' in lines[0]:
            delimiter = '|'
        else:
            delimiter = ','
        
        # Parse headers
        headers = [h.strip() for h in lines[0].split(delimiter)]
        headers = [h for h in headers if h]  # Remove empties
        
        # Parse rows
        rows = []
        for line in lines[1:]:
            row = [cell.strip() for cell in line.split(delimiter)]
            row = [cell for cell in row if cell]
            if row and len(row) == len(headers):
                rows.append(row)
        
        if len(rows) > 0:
            return ExtractedTable(
                table_id="",  # Set by caller
                headers=headers,
                rows=rows,
                row_count=len(rows),
                column_count=len(headers),
                table_type="text_based",
                confidence=0.70,
                context=""
            )
        
        return None

    def extract_all_tables(self, text: str) -> List[ExtractedTable]:
        """Extract all tables from text"""
        tables = []
        
        # Try markdown tables first
        tables.extend(self.extract_markdown_tables(text))
        
        # Try CSV-like tables
        csv_tables = self.extract_csv_like_tables(text)
        for table in csv_tables:
            table.table_id = f"table_{len(tables)}"
            tables.append(table)
        
        return tables


def extract_tables(text: str, config: Dict = None) -> List[ExtractedTable]:
    """Extract all tables from text"""
    extractor = TableExtractor(config)
    return extractor.extract_all_tables(text)
