"""
Blog 6: Embedding Generation

Generate vector embeddings for text chunks using lightweight models.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json
import hashlib
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

logger = logging.getLogger(__name__)


@dataclass
class Embedding:
    """Single embedding vector with metadata"""
    chunk_id: str
    doc_id: str
    vector: List[float]
    text_preview: str  # First 100 chars of text
    text_hash: str
    embedding_dim: int
    source_type: str
    metadata: Dict = None


class EmbeddingGenerator:
    """
    Generate embeddings for text chunks.
    Uses lightweight models suitable for CPU-only environments.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", 
                 use_gpu: bool = False):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of sentence-transformers model
            use_gpu: Whether to use GPU (if available)
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.model = None
        self.embedding_dim = 384  # Default for MiniLM
        
        self._init_model()
    
    def _init_model(self):
        """Initialize embedding model"""
        if not HAS_SENTENCE_TRANSFORMERS:
            logger.warning(
                "sentence-transformers not installed. "
                "Using fallback hashing for embeddings. "
                "Install: pip install sentence-transformers"
            )
            self.model = None
            return
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            device = "cuda" if self.use_gpu else "cpu"
            self.model = SentenceTransformer(self.model_name, device=device)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Error loading model {self.model_name}: {e}")
            logger.warning("Falling back to hash-based embeddings")
            self.model = None
    
    def embed_text(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Embed single text string.
        
        Args:
            text: Text to embed
            normalize: Whether to normalize embedding
            
        Returns:
            Embedding vector
        """
        if not text:
            # Return zero vector for empty text
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        if self.model:
            # Use real embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            if normalize:
                # L2 normalization
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
            
            return embedding.astype(np.float32)
        else:
            # Fallback: hash-based embedding
            return self._hash_based_embedding(text, normalize)
    
    def embed_batch(self, texts: List[str], batch_size: int = 64,
                   normalize: bool = True) -> List[np.ndarray]:
        """
        Embed multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            normalize: Whether to normalize embeddings
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        if self.model:
            # Use real embedding
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=normalize
            )
            return [emb.astype(np.float32) for emb in embeddings]
        else:
            # Fallback: hash-based embeddings
            return [self._hash_based_embedding(text, normalize) for text in texts]
    
    def _hash_based_embedding(self, text: str, 
                             normalize: bool = True) -> np.ndarray:
        """
        Generate deterministic embedding from text hash.
        Used as fallback when model is unavailable.
        
        Args:
            text: Text to embed
            normalize: Whether to normalize
            
        Returns:
            Pseudo-random embedding vector
        """
        # Create deterministic pseudo-random embedding from text hash
        text_hash = hashlib.sha256(text.encode()).digest()
        
        # Convert hash bytes to float32 values
        embedding = np.frombuffer(text_hash, dtype=np.uint8).astype(np.float32)
        
        # Expand to embedding dimension
        if len(embedding) < self.embedding_dim:
            # Tile and hash to reach desired dimension
            expanded = np.zeros(self.embedding_dim, dtype=np.float32)
            for i in range(self.embedding_dim):
                hash_seed = (text_hash[i % len(text_hash)] + i) % 256
                expanded[i] = np.sin(hash_seed * np.pi / 256)
            embedding = expanded
        else:
            embedding = embedding[:self.embedding_dim]
        
        if normalize:
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
        
        return embedding
    
    def create_embeddings(self, chunks: List[Dict]) -> List[Embedding]:
        """
        Create embeddings from chunks.
        
        Args:
            chunks: List of chunk dicts with 'chunk_id', 'text', etc.
            
        Returns:
            List of Embedding objects
        """
        if not chunks:
            return []
        
        # Extract texts
        texts = [chunk.get("text", "") for chunk in chunks]
        
        # Generate embeddings
        vectors = self.embed_batch(texts)
        
        # Create Embedding objects
        embeddings = []
        
        for chunk, vector in zip(chunks, vectors):
            text_preview = chunk.get("text", "")[:100]
            text_hash = hashlib.sha256(
                chunk.get("text", "").encode()
            ).hexdigest()
            
            embedding = Embedding(
                chunk_id=chunk.get("chunk_id", ""),
                doc_id=chunk.get("doc_id", ""),
                vector=vector.tolist(),
                text_preview=text_preview,
                text_hash=text_hash,
                embedding_dim=self.embedding_dim,
                source_type=chunk.get("source_type", "document"),
                metadata=chunk.get("metadata", {})
            )
            embeddings.append(embedding)
        
        logger.info(f"Created {len(embeddings)} embeddings")
        return embeddings


def generate_embeddings(texts: List[str],
                       model_name: str = "all-MiniLM-L6-v2",
                       batch_size: int = 64) -> List[List[float]]:
    """
    Generate embeddings for texts.
    
    Args:
        texts: List of texts to embed
        model_name: Name of model to use
        batch_size: Batch size for processing
        
    Returns:
        List of embedding vectors
    """
    generator = EmbeddingGenerator(model_name)
    embeddings = generator.embed_batch(texts, batch_size=batch_size)
    return [emb.tolist() for emb in embeddings]
