"""
Retrieval result data model.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class RetrievalResult:
    """
    Result of a retrieval query.
    """
    
    # Query info
    query: str
    query_id: str = ""
    
    # Retrieved chunks
    retrieved_chunks: List[Dict[str, Any]] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    
    # Retrieval metadata
    k: int = 5  # top-k requested
    actual_k: int = 0  # actual number returned
    retrieval_time_ms: float = 0.0
    
    # Context for LLM
    context: str = ""  # Formatted context from chunks
    context_tokens: int = 0
    
    # Metadata
    retrieved_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def format_for_llm(self) -> str:
        """Format retrieved chunks as context for LLM."""
        if not self.retrieved_chunks:
            return "No relevant documents found."
        
        context_parts = []
        for i, (chunk, score) in enumerate(zip(self.retrieved_chunks, self.scores), 1):
            text = chunk.get("text", "")
            source = chunk.get("provenance", {}).get("source_location", "Unknown")
            context_parts.append(
                f"[{i}] (Score: {score:.3f}, Source: {source})\n{text}\n"
            )
        
        self.context = "\n".join(context_parts)
        self.context_tokens = len(self.context.split())
        return self.context
