"""
Blog 4: Structured Knowledge Extraction

Extracts tables, metadata, code blocks, and document structure.
"""

from .extractor import KnowledgeExtractor, run_extraction, ExtractedKnowledge
from .table_extractor import TableExtractor, extract_tables, ExtractedTable
from .metadata_extractor import MetadataExtractor, extract_metadata, ExtractedMetadata
from .structure_extractor import (
    CodeExtractor, SectionExtractor,
    extract_code_blocks, extract_sections,
    extract_paragraphs, extract_lists,
    ExtractedCode, ExtractedSection
)

__all__ = [
    # Main orchestrator
    "KnowledgeExtractor",
    "run_extraction",
    "ExtractedKnowledge",
    
    # Table extraction
    "TableExtractor",
    "extract_tables",
    "ExtractedTable",
    
    # Metadata extraction
    "MetadataExtractor",
    "extract_metadata",
    "ExtractedMetadata",
    
    # Structure extraction
    "CodeExtractor",
    "SectionExtractor",
    "extract_code_blocks",
    "extract_sections",
    "extract_paragraphs",
    "extract_lists",
    "ExtractedCode",
    "ExtractedSection",
]