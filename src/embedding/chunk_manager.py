"""
Blog 6: Document Chunk Management

Split documents into chunks for embedding with overlap and metadata preservation.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Chunk of a document for embedding"""
    chunk_id: str
    doc_id: str
    text: str
    chunk_index: int
    total_chunks: int
    start_pos: int
    end_pos: int
    metadata: Dict = None
    source_type: str = "document"  # document, table, code, etc.


class ChunkManager:
    """
    Manage document chunking with configurable size and overlap.
    Preserves metadata and maintains chunk integrity.
    """
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50, 
                 min_chunk_size: int = 100):
        """
        Initialize chunk manager.
        
        Args:
            chunk_size: Target size of each chunk (in characters)
            overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum chunk size to keep
        """
        self.chunk_size = chunk_size
        self.overlap = min(overlap, chunk_size // 4)
        self.min_chunk_size = min_chunk_size
    
    def chunk_text(self, text: str, chunk_id_prefix: str = "chunk") -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to chunk
            chunk_id_prefix: Prefix for chunk IDs
            
        Returns:
            List of chunk strings
        """
        if not text:
            return []
        
        chunks = []
        current_pos = 0
        chunk_count = 0
        
        while current_pos < len(text):
            # Try to end chunk at sentence boundary
            chunk_end = min(current_pos + self.chunk_size, len(text))
            
            # Search for sentence end near chunk_end
            if chunk_end < len(text):
                # Look back for period, question mark, exclamation
                search_end = max(current_pos + self.min_chunk_size, chunk_end - 100)
                best_end = None
                
                for i in range(chunk_end, search_end, -1):
                    if text[i] in '.!?\n':
                        best_end = i + 1
                        break
                
                if best_end:
                    chunk_end = best_end
            
            chunk_text = text[current_pos:chunk_end].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(chunk_text)
                chunk_count += 1
            
            # Move position with overlap
            current_pos = chunk_end - self.overlap
            if current_pos <= current_pos - self.chunk_size//2:
                current_pos = chunk_end
        
        return chunks
    
    def create_chunks(self, doc_id: str, text: str, 
                     metadata: Optional[Dict] = None,
                     source_type: str = "document") -> List[DocumentChunk]:
        """
        Create chunks from document with metadata.
        
        Args:
            doc_id: Document ID
            text: Document text
            metadata: Document metadata
            source_type: Type of source (document, table, code, etc.)
            
        Returns:
            List of DocumentChunk objects
        """
        if not text:
            return []
        
        chunks = self.chunk_text(text)
        if not chunks:
            return []
        
        document_chunks = []
        current_pos = 0
        
        for chunk_idx, chunk_text in enumerate(chunks):
            # Find actual position in original text
            start_pos = text.find(chunk_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            
            end_pos = start_pos + len(chunk_text)
            current_pos = end_pos
            
            chunk_id = f"{doc_id}_chunk_{chunk_idx}"
            
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                text=chunk_text,
                chunk_index=chunk_idx,
                total_chunks=len(chunks),
                start_pos=start_pos,
                end_pos=end_pos,
                metadata=metadata or {},
                source_type=source_type
            )
            
            document_chunks.append(chunk)
        
        logger.debug(f"Created {len(document_chunks)} chunks from {doc_id}")
        return document_chunks
    
    def chunk_structured_knowledge(self, doc_id: str, 
                                   knowledge: Dict) -> List[DocumentChunk]:
        """
        Create chunks from extracted knowledge.
        
        Args:
            doc_id: Document ID
            knowledge: Extracted knowledge dict with tables, code, etc.
            
        Returns:
            List of DocumentChunk objects
        """
        all_chunks = []
        
        # Chunk main text
        if knowledge.get("text"):
            text_chunks = self.create_chunks(
                doc_id,
                knowledge["text"],
                metadata=knowledge.get("metadata", {}),
                source_type="text"
            )
            all_chunks.extend(text_chunks)
        
        # Chunk metadata as separate chunks
        if knowledge.get("metadata"):
            meta = knowledge["metadata"]
            meta_text_parts = []
            
            if meta.get("title"):
                meta_text_parts.append(f"Title: {meta['title']}")
            
            if meta.get("summary"):
                meta_text_parts.append(f"Summary: {meta['summary']}")
            
            if meta.get("authors"):
                meta_text_parts.append(f"Authors: {', '.join(meta['authors'])}")
            
            if meta.get("keywords"):
                meta_text_parts.append(f"Keywords: {', '.join(meta['keywords'])}")
            
            if meta_text_parts:
                meta_text = "\n".join(meta_text_parts)
                meta_chunks = self.create_chunks(
                    f"{doc_id}_meta",
                    meta_text,
                    metadata=meta,
                    source_type="metadata"
                )
                all_chunks.extend(meta_chunks)
        
        # Create chunks from code blocks
        if knowledge.get("code_blocks"):
            for idx, code_block in enumerate(knowledge["code_blocks"]):
                code_text = code_block.get("code", "")
                if code_text:
                    code_chunks = self.create_chunks(
                        f"{doc_id}_code_{idx}",
                        code_text,
                        metadata={"language": code_block.get("language", "unknown")},
                        source_type="code"
                    )
                    all_chunks.extend(code_chunks)
        
        # Create chunks from tables
        if knowledge.get("tables"):
            for idx, table in enumerate(knowledge["tables"]):
                table_text = self._table_to_text(table)
                if table_text:
                    table_chunks = self.create_chunks(
                        f"{doc_id}_table_{idx}",
                        table_text,
                        metadata={"table_type": table.get("table_type", "unknown")},
                        source_type="table"
                    )
                    all_chunks.extend(table_chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from extracted knowledge")
        return all_chunks
    
    @staticmethod
    def _table_to_text(table: Dict) -> str:
        """Convert table to text representation"""
        text_parts = []
        
        if table.get("headers"):
            text_parts.append("Headers: " + ", ".join(table["headers"]))
        
        if table.get("rows"):
            for row_idx, row in enumerate(table["rows"][:10]):  # Limit to 10 rows
                row_text = " | ".join(str(cell) for cell in row)
                text_parts.append(f"Row {row_idx}: {row_text}")
        
        if len(table.get("rows", [])) > 10:
            text_parts.append(f"... and {len(table['rows']) - 10} more rows")
        
        return "\n".join(text_parts)


def create_document_chunks(doc_id: str, text: str,
                          metadata: Optional[Dict] = None,
                          chunk_size: int = 512,
                          overlap: int = 50) -> List[DocumentChunk]:
    """
    Create chunks from document.
    
    Args:
        doc_id: Document ID
        text: Document text
        metadata: Optional metadata
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List of DocumentChunk objects
    """
    manager = ChunkManager(chunk_size=chunk_size, overlap=overlap)
    return manager.create_chunks(doc_id, text, metadata)
