"""
Data models for documents through the RAG pipeline.
Follows the schema defined in Blog 1-5.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class DocumentQualityScore:
    """
    Blog 1 output: Quality score vector for each document.
    This travels with the document through all pipeline stages.
    """
    
    # Identifiers
    doc_id: str
    source_path: str
    
    # Format information
    format_type: str  # pdf_text, pdf_scanned, html, json, csv, txt, md, py
    
    # Text quality signals
    language: str  # ISO 639-1 code (en, fr, de, etc.)
    language_confidence: float  # 0.0 to 1.0
    perplexity: Optional[float] = None  # Lower = better (None for structured formats)
    char_count: int = 0
    word_count: int = 0
    
    # Format-specific signals
    layout_complexity: Optional[str] = None  # simple, multi_column, table_heavy, diagram_heavy
    content_ratio: Optional[float] = None  # HTML signal-to-noise (0.0 to 1.0)
    ocr_quality: Optional[float] = None  # For scanned PDFs
    schema_drift_flag: bool = False  # For JSON/SQL
    
    # Retrieval utility prediction
    quality_score: float = 0.0  # Overall quality (0.0 to 1.0)
    estimated_retrieval_utility: float = 0.0  # 0.0 to 1.0
    requires_special_handling: bool = False
    routing_tag: str = "unknown"
    
    # Near-dedup signal
    simhash: Optional[int] = None  # For near-dedup detection
    content_hash: Optional[str] = None  # SHA-256 for exact dedup
    
    # Audit metadata
    audit_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    audit_pipeline_version: str = "1.0"
    
    # Pipeline tracking
    blog_stages_passed: List[int] = field(default_factory=list)  # [1, 2, 3, ...]
    cleaning_filters_passed: Dict[str, bool] = field(default_factory=dict)
    is_final: bool = False  # True when passed all stages
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentQualityScore":
        """Create from dictionary."""
        return cls(**data)
    
    def __post_init__(self):
        """Validate after initialization."""
        if not self.doc_id:
            raise ValueError("doc_id is required")
        if self.format_type not in ["pdf_text", "pdf_scanned", "html", "json", "csv", "txt", "md", "py"]:
            raise ValueError(f"Unknown format_type: {self.format_type}")


@dataclass
class ParsedDocument:
    """
    Blog 2 output: Parsed, format-coherent text.
    """
    
    doc_id: str
    format_type: str
    text: str
    
    # Layout metadata (for PDFs)
    layout_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Heading hierarchy (for structured docs)
    heading_path: List[str] = field(default_factory=list)
    
    # Parsing quality
    parse_quality: float = 1.0  # 0.0 to 1.0
    parse_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CleanedDocument:
    """
    Blog 3 output: Cleaned, normalized text.
    """
    
    doc_id: str
    text_cleaned: str
    
    # Cleaning decisions
    encoding_normalized: bool = False
    filters_passed: Dict[str, bool] = field(default_factory=dict)
    boilerplate_fraction: float = 0.0
    language_consistency: float = 1.0
    
    # Cleaning metadata
    cleaned_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    cleaning_quality: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnrichedDocument:
    """
    Blog 4 output: Document with extracted structures.
    """
    
    doc_id: str
    text_main: str
    
    # Extracted structures
    tables: List[Dict[str, Any]] = field(default_factory=list)
    figures: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    enriched_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DedupDocument:
    """
    Blog 5 output: Deduplicated document info.
    """
    
    doc_id: str
    
    # Dedup signals
    content_hash: str  # SHA-256
    exact_dup_status: Optional[str] = None  # "kept", "duplicate"
    exact_dup_cluster_id: Optional[str] = None
    
    near_dup_cluster_id: Optional[str] = None
    near_dup_similarity: Optional[float] = None
    
    minhash_signature: Optional[List[int]] = None
    is_canonical: bool = True
    
    dedup_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
