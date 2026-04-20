"""
Blog 6: Retriever for RAG

Retrieve relevant documents based on semantic similarity.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .embedding_generator import EmbeddingGenerator
from .vector_store import VectorStore, RetrievalResult
from .chunk_manager import ChunkManager

logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    """Context for RAG generation"""
    query: str
    results: List[RetrievalResult]
    context_text: str
    metadata: Dict


class Retriever:
    """
    Retrieve relevant documents for queries.
    Combines chunking, embedding, and vector search.
    """
    
    def __init__(self, embedding_dim: int = 384,
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize retriever.
        
        Args:
            embedding_dim: Dimension of embeddings
            model_name: Name of embedding model
        """
        self.embedding_generator = EmbeddingGenerator(model_name)
        self.vector_store = VectorStore(embedding_dim=embedding_dim)
        self.chunk_manager = ChunkManager()
    
    def index_documents(self, documents: Dict[str, Dict]) -> Dict:
        """
        Index documents for retrieval.
        
        Args:
            documents: Dict mapping doc_id -> document dict with extracted knowledge
            
        Returns:
            Indexing statistics
        """
        logger.info("Indexing documents...")
        
        all_chunks = []
        chunk_embeddings = []
        metadata_list = []
        
        for doc_id, doc in documents.items():
            try:
                # Create chunks from document
                chunks = self.chunk_manager.chunk_structured_knowledge(doc_id, doc)
                
                if not chunks:
                    continue
                
                # Convert chunks to embedding format
                for chunk in chunks:
                    chunk_dict = {
                        "chunk_id": chunk.chunk_id,
                        "doc_id": chunk.doc_id,
                        "text": chunk.text,
                        "source_type": chunk.source_type,
                        "metadata": chunk.metadata
                    }
                    all_chunks.append(chunk_dict)
                
            except Exception as e:
                logger.error(f"Error chunking document {doc_id}: {e}")
        
        if not all_chunks:
            logger.warning("No chunks created from documents")
            return {"status": "empty", "chunks": 0}
        
        logger.info(f"Created {len(all_chunks)} chunks from documents")
        
        # Generate embeddings for all chunks
        texts = [chunk["text"] for chunk in all_chunks]
        embeddings = self.embedding_generator.embed_batch(texts)
        
        # Prepare metadata
        for chunk, embedding in zip(all_chunks, embeddings):
            metadata = {
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "text_preview": chunk["text"][:100],
                "source_type": chunk["source_type"],
                "metadata": chunk.get("metadata", {})
            }
            metadata_list.append(metadata)
            chunk_embeddings.append(embedding.tolist())
        
        # Add to vector store
        self.vector_store.add_embeddings(chunk_embeddings, metadata_list)
        
        stats = {
            "status": "success",
            "documents": len(documents),
            "chunks": len(all_chunks),
            "embeddings": len(chunk_embeddings),
            "embedding_dim": self.embedding_generator.embedding_dim
        }
        
        logger.info(f"Indexing complete: {stats}")
        return stats
    
    def retrieve(self, query: str, top_k: int = 5,
                filter_by_type: Optional[str] = None) -> RetrievalContext:
        """
        Retrieve relevant documents for query.
        
        Args:
            query: Query text
            top_k: Number of results to return
            filter_by_type: Optional source type filter (document, table, code, etc.)
            
        Returns:
            RetrievalContext with results
        """
        logger.info(f"Retrieving for query: {query[:100]}")
        
        # Embed query
        query_embedding = self.embedding_generator.embed_text(query)
        
        # Search
        results = self.vector_store.search(query_embedding.tolist(), top_k=top_k*2)
        
        # Filter by type if specified
        if filter_by_type:
            results = [r for r in results if r.source_type == filter_by_type]
        
        # Limit to top_k
        results = results[:top_k]
        
        # Build context text
        context_parts = []
        for result in results:
            context_parts.append(
                f"[{result.source_type.upper()}] {result.text_preview}"
            )
        context_text = "\n\n".join(context_parts)
        
        # Build metadata
        metadata = {
            "num_results": len(results),
            "query": query,
            "top_k": top_k,
            "filter_by_type": filter_by_type
        }
        
        ctx = RetrievalContext(
            query=query,
            results=results,
            context_text=context_text,
            metadata=metadata
        )
        
        logger.info(f"Retrieved {len(results)} results")
        return ctx
    
    def batch_retrieve(self, queries: List[str], 
                      top_k: int = 5) -> List[RetrievalContext]:
        """
        Retrieve for multiple queries.
        
        Args:
            queries: List of query texts
            top_k: Number of results per query
            
        Returns:
            List of RetrievalContext
        """
        contexts = []
        
        for query in queries:
            ctx = self.retrieve(query, top_k=top_k)
            contexts.append(ctx)
        
        return contexts
    
    def save_index(self, index_path: str) -> None:
        """
        Save retriever index.
        
        Args:
            index_path: Path to save index
        """
        metadata_path = index_path.replace(".faiss", "_metadata.json")
        self.vector_store.save(index_path, metadata_path)
        logger.info(f"Saved index to {index_path}")
    
    def load_index(self, index_path: str) -> None:
        """
        Load retriever index.
        
        Args:
            index_path: Path to load index
        """
        metadata_path = index_path.replace(".faiss", "_metadata.json")
        self.vector_store.load(index_path, metadata_path)
        logger.info(f"Loaded index from {index_path}")
    
    def get_stats(self) -> Dict:
        """Get retriever statistics"""
        store_stats = self.vector_store.get_stats()
        return {
            "embedding_model": self.embedding_generator.model_name,
            **store_stats
        }


def create_retriever(model_name: str = "all-MiniLM-L6-v2") -> Retriever:
    """
    Create retriever instance.
    
    Args:
        model_name: Name of embedding model
        
    Returns:
        Retriever instance
    """
    return Retriever(model_name=model_name)
