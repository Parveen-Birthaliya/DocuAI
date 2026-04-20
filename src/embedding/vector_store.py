"""
Blog 6: Vector Store for Embedding Index

Store and retrieve embeddings using FAISS with metadata support.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import numpy as np

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result from vector search"""
    chunk_id: str
    doc_id: str
    text_preview: str
    distance: float
    similarity_score: float
    source_type: str
    metadata: Dict


class VectorStore:
    """
    Store and index embeddings using FAISS.
    Maintains metadata for each embedding.
    """
    
    def __init__(self, embedding_dim: int = 384, index_type: str = "flat"):
        """
        Initialize vector store.
        
        Args:
            embedding_dim: Dimension of embeddings
            index_type: "flat" for exact search, "ivf" for approximate
        """
        if not HAS_FAISS:
            logger.warning(
                "FAISS not installed. Install: pip install faiss-cpu"
            )
        
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.index = None
        self.metadata = {}  # Map from index to metadata
        self.embedding_ids = []  # List of chunk IDs in order
        self.doc_count = 0
        
        self._init_index()
    
    def _init_index(self):
        """Initialize FAISS index"""
        if not HAS_FAISS:
            logger.warning("FAISS not available, vector store will not work")
            return
        
        if self.index_type == "flat":
            # Exact search - L2 distance
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        elif self.index_type == "ivf":
            # Approximate search with IVF (Inverted File)
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            self.index = faiss.IndexIVFFlat(
                quantizer,
                self.embedding_dim,
                min(100, max(10, self.embedding_dim // 2))
            )
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
        
        logger.info(f"Initialized {self.index_type} FAISS index")
    
    def add_embeddings(self, embeddings: List[Dict], 
                      metadata_list: List[Dict]) -> None:
        """
        Add embeddings to index.
        
        Args:
            embeddings: List of embedding vectors (as lists)
            metadata_list: List of metadata dicts (must match embeddings length)
        """
        if not HAS_FAISS or self.index is None:
            logger.error("FAISS not available")
            return
        
        if not embeddings:
            return
        
        if len(embeddings) != len(metadata_list):
            raise ValueError("Embeddings and metadata lists must have same length")
        
        # Convert to numpy array
        embedding_array = np.array(embeddings, dtype=np.float32)
        
        # Add to index
        self.index.add(embedding_array)
        
        # Store metadata
        for idx, metadata in enumerate(metadata_list):
            chunk_id = metadata.get("chunk_id", f"chunk_{idx}")
            self.embedding_ids.append(chunk_id)
            self.metadata[len(self.embedding_ids) - 1] = metadata
        
        self.doc_count += 1
        logger.info(f"Added {len(embeddings)} embeddings to index")
    
    def search(self, query_embedding: List[float], 
              top_k: int = 5) -> List[RetrievalResult]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult
        """
        if not HAS_FAISS or self.index is None:
            logger.error("FAISS not available")
            return []
        
        if len(self.embedding_ids) == 0:
            logger.warning("Index is empty")
            return []
        
        # Ensure query is right shape
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search
        try:
            distances, indices = self.index.search(query_array, min(top_k, len(self.embedding_ids)))
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
        
        # Convert distances to similarity scores
        # For L2 distance: higher distance = lower similarity
        results = []
        
        for idx, distance in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(self.embedding_ids):
                continue
            
            # Convert L2 distance to similarity score (0-1)
            # Assuming normalized embeddings: distance ~ 2 - 2*similarity
            similarity = 1.0 - (distance / 2.0)
            similarity = max(0.0, min(1.0, similarity))
            
            chunk_id = self.embedding_ids[idx]
            metadata = self.metadata.get(idx, {})
            
            result = RetrievalResult(
                chunk_id=chunk_id,
                doc_id=metadata.get("doc_id", ""),
                text_preview=metadata.get("text_preview", ""),
                distance=float(distance),
                similarity_score=float(similarity),
                source_type=metadata.get("source_type", "document"),
                metadata=metadata.get("metadata", {})
            )
            results.append(result)
        
        return results
    
    def batch_search(self, query_embeddings: List[List[float]],
                    top_k: int = 5) -> List[List[RetrievalResult]]:
        """
        Search for multiple queries.
        
        Args:
            query_embeddings: List of query embedding vectors
            top_k: Number of results per query
            
        Returns:
            List of result lists
        """
        results = []
        
        for query_embedding in query_embeddings:
            result = self.search(query_embedding, top_k=top_k)
            results.append(result)
        
        return results
    
    def save(self, index_path: str, metadata_path: str = None) -> None:
        """
        Save index to disk.
        
        Args:
            index_path: Path to save FAISS index
            metadata_path: Path to save metadata (optional)
        """
        if not HAS_FAISS or self.index is None:
            logger.error("Cannot save: FAISS not available")
            return
        
        try:
            faiss.write_index(self.index, index_path)
            logger.info(f"Saved index to {index_path}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
        
        # Save metadata
        if metadata_path is None:
            metadata_path = index_path.replace(".faiss", "_metadata.json")
        
        metadata_to_save = {
            "embedding_ids": self.embedding_ids,
            "metadata": {str(k): v for k, v in self.metadata.items()},
            "doc_count": self.doc_count,
            "embedding_dim": self.embedding_dim
        }
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata_to_save, f, indent=2)
            logger.info(f"Saved metadata to {metadata_path}")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def load(self, index_path: str, metadata_path: str = None) -> None:
        """
        Load index from disk.
        
        Args:
            index_path: Path to load FAISS index
            metadata_path: Path to load metadata
        """
        if not HAS_FAISS:
            logger.error("FAISS not available")
            return
        
        try:
            self.index = faiss.read_index(index_path)
            logger.info(f"Loaded index from {index_path}")
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return
        
        # Load metadata
        if metadata_path is None:
            metadata_path = index_path.replace(".faiss", "_metadata.json")
        
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                self.embedding_ids = data.get("embedding_ids", [])
                self.metadata = {int(k): v for k, v in data.get("metadata", {}).items()}
                self.doc_count = data.get("doc_count", 0)
                self.embedding_dim = data.get("embedding_dim", self.embedding_dim)
            logger.info(f"Loaded metadata from {metadata_path}")
        except FileNotFoundError:
            logger.warning(f"Metadata file not found: {metadata_path}")
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        return {
            "index_type": self.index_type,
            "embedding_dim": self.embedding_dim,
            "total_embeddings": len(self.embedding_ids),
            "total_documents": self.doc_count,
            "index_trained": self.index.is_trained if self.index else False
        }


def create_vector_store(embedding_dim: int = 384) -> VectorStore:
    """
    Create vector store instance.
    
    Args:
        embedding_dim: Dimension of embeddings
        
    Returns:
        VectorStore instance
    """
    return VectorStore(embedding_dim=embedding_dim, index_type="flat")
