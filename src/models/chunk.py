"""
Chunk data model for RAG pipeline.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Chunk:
    """
    Represents a chunk of text ready for embedding.
    Tracks full provenance from source document.
    """
    
    # Identifiers
    chunk_id: str
    doc_id: str
    
    # Content
    text: str
    
    # Chunk metadata
    chunk_type: str = "main_text"  # main_text, table, figure_caption, metadata
    chunk_index: int = 0  # Order within document
    
    # Provenance - trace back to source
    provenance: Dict[str, Any] = field(default_factory=dict)
    # Expected keys:
    #   - source_location: file path or location in doc
    #   - format_type: pdf, html, json, etc.
    #   - blog_stage: BlogN_StageName
    #   - page_num: if applicable
    #   - section_heading: if hierarchical
    
    # Quality / Scoring
    chunk_score: float = 1.0  # Quality indicator (0.0 to 1.0)
    global_rank: int = 0  # For ranking in retrieval
    
    # Flags
    is_table: bool = False
    is_figure_caption: bool = False
    is_header: bool = False
    is_footer: bool = False
    
    # Embedding (will be filled after encoding)
    embedding: Optional[list] = None
    embedding_dim: int = 384  # For all-MiniLM-L6-v2
    
    # Administrative
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    indexed: bool = False
    index_position: Optional[int] = None  # Position in FAISS index
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        # Don't include embedding in JSON for size reasons
        if d.get("embedding"):
            d["embedding"] = None
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        """Create from dictionary."""
        # Handle None embedding
        if data.get("embedding") is None:
            data["embedding"] = None
        return cls(**data)
    
    def __post_init__(self):
        """Validate after initialization."""
        if not self.chunk_id:
            raise ValueError("chunk_id is required")
        if not self.doc_id:
            raise ValueError("doc_id is required")
        if len(self.text.strip()) == 0:
            raise ValueError("text cannot be empty")


@dataclass
class IndexedChunk:
    """
    Chunk after embedding and FAISS indexing.
    """
    
    chunk_id: str
    embedding: list  # numpy array serialized to list
    
    # FAISS metadata
    faiss_index: int  # Position in FAISS index
    
    # Original text for retrieval
    text: str
    
    # Metadata for context
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
