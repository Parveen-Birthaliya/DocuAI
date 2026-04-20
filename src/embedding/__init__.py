"""Blog 6: Embedding & Retrieval

Generate embeddings and build vector index for semantic search and RAG.
"""

from .chunk_manager import ChunkManager, DocumentChunk, create_document_chunks
from .embedding_generator import EmbeddingGenerator, Embedding, generate_embeddings
from .vector_store import VectorStore, RetrievalResult, create_vector_store
from .retriever import Retriever, RetrievalContext, create_retriever
from .orchestrator import Blog6Orchestrator, STAGE6Results, run_blog6, load_retriever

__all__ = [
    # Chunk management
    "ChunkManager",
    "DocumentChunk",
    "create_document_chunks",
    
    # Embedding generation
    "EmbeddingGenerator",
    "Embedding",
    "generate_embeddings",
    
    # Vector store
    "VectorStore",
    "RetrievalResult",
    "create_vector_store",
    
    # Retriever
    "Retriever",
    "RetrievalContext",
    "create_retriever",
    
    # Orchestrator
    "Blog6Orchestrator",
    "STAGE6Results",
    "run_blog6",
    "load_retriever",
]
