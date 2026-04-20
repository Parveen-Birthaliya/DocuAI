"""
Blog 6: Embedding & Retrieval Orchestrator

Main orchestrator for STAGE 6:
- Load deduplicated documents from Blog 5
- Create chunks and generate embeddings
- Build vector index for retrieval
- Enable semantic search for RAG
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from tqdm import tqdm

from .chunk_manager import ChunkManager
from .embedding_generator import EmbeddingGenerator
from .vector_store import VectorStore
from .retriever import Retriever
from src.utils.json_store import JSONStore
from src.utils.logger import setup_logger
from src.config import get_config

logger = setup_logger(__name__)


@dataclass
class STAGE6Results:
    """Results from STAGE 6 (Embedding & Retrieval)"""
    total_documents: int
    total_chunks: int
    embeddings_created: int
    embedding_dimension: int
    index_stats: Dict
    statistics: Dict


class Blog6Orchestrator:
    """
    Main orchestrator for Blog 6: Embedding & Retrieval
    
    Pipeline:
    1. Load deduplicated documents from Blog 5
    2. Create chunks from documents with overlap
    3. Generate embeddings for all chunks
    4. Build and index vector store
    5. Enable retrieval interface
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.data_dir = Path(self.config.get("data_dir", "data/processed"))
        
        self.chunk_manager = ChunkManager(
            chunk_size=self.config.get("chunk_size", 512),
            overlap=self.config.get("chunk_overlap", 50)
        )
        
        model_name = self.config.get("embedding_model", "all-MiniLM-L6-v2")
        self.embedding_generator = EmbeddingGenerator(model_name)
        self.vector_store = VectorStore(
            embedding_dim=self.embedding_generator.embedding_dim
        )
        
        self.retriever = Retriever(model_name=model_name)
        self.json_store = JSONStore()
    
    def load_deduplicated_documents(self) -> Dict:
        """
        Load deduplicated documents from Blog 5.
        
        Returns:
            Dict mapping doc_id -> document with extracted knowledge
        """
        logger.info("Loading deduplicated documents from Blog 5...")
        
        knowledge_path = self.data_dir / "deduplicated" / "deduplicated_knowledge.json"
        
        if not knowledge_path.exists():
            logger.warning(f"Deduplicated knowledge file not found: {knowledge_path}")
            return {}
        
        try:
            knowledge_list = self.json_store.load_list(str(knowledge_path))
            
            # Convert to dict format expected by retriever
            documents = {}
            for item in knowledge_list:
                doc_id = item.get("canonical_doc_id", "")
                documents[doc_id] = {
                    "text": item.get("text", ""),
                    "metadata": item.get("merged_metadata", {}),
                    "tables": item.get("merged_tables", []),
                    "code_blocks": item.get("merged_code_blocks", []),
                    "sections": item.get("merged_sections", [])
                }
            
            logger.info(f"Loaded {len(documents)} deduplicated documents")
            return documents
        
        except Exception as e:
            logger.error(f"Error loading deduplicated documents: {e}")
            return {}
    
    def create_chunks(self, documents: Dict) -> Tuple[List[Dict], Dict]:
        """
        Create chunks from documents.
        
        Args:
            documents: Dict mapping doc_id -> document
            
        Returns:
            Tuple of (chunks list, stats dict)
        """
        logger.info("Creating document chunks...")
        
        all_chunks = []
        stats = {
            "documents": len(documents),
            "chunks": 0,
            "by_source_type": {},
            "avg_chunk_length": 0
        }
        
        for doc_id, doc in tqdm(documents.items(), desc="Chunking"):
            try:
                chunks = self.chunk_manager.chunk_structured_knowledge(doc_id, doc)
                all_chunks.extend(chunks)
                
                for chunk in chunks:
                    source_type = chunk.source_type
                    if source_type not in stats["by_source_type"]:
                        stats["by_source_type"][source_type] = 0
                    stats["by_source_type"][source_type] += 1
            
            except Exception as e:
                logger.error(f"Error chunking document {doc_id}: {e}")
        
        stats["chunks"] = len(all_chunks)
        if all_chunks:
            total_length = sum(len(c.text) for c in all_chunks)
            stats["avg_chunk_length"] = total_length / len(all_chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        
        # Convert chunks to dict format
        chunk_dicts = []
        for chunk in all_chunks:
            chunk_dict = {
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "text": chunk.text,
                "start_pos": chunk.start_pos,
                "end_pos": chunk.end_pos,
                "source_type": chunk.source_type,
                "metadata": chunk.metadata
            }
            chunk_dicts.append(chunk_dict)
        
        return chunk_dicts, stats
    
    def generate_embeddings(self, chunks: List[Dict]) -> Tuple[List[List[float]], Dict]:
        """
        Generate embeddings for all chunks.
        
        Args:
            chunks: List of chunk dicts with 'text' field
            
        Returns:
            Tuple of (embeddings list, stats dict)
        """
        logger.info("Generating embeddings...")
        
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_generator.embed_batch(texts)
        
        stats = {
            "embeddings": len(embeddings),
            "embedding_dim": self.embedding_generator.embedding_dim,
            "model": self.embedding_generator.model_name
        }
        
        logger.info(f"Generated {len(embeddings)} embeddings (dim={stats['embedding_dim']})")
        
        return [emb.tolist() for emb in embeddings], stats
    
    def build_index(self, chunks: List[Dict],
                   embeddings: List[List[float]]) -> Dict:
        """
        Build vector index.
        
        Args:
            chunks: List of chunk dicts
            embeddings: List of embedding vectors
            
        Returns:
            Index statistics
        """
        logger.info("Building vector index...")
        
        # Prepare metadata
        metadata_list = []
        for chunk in chunks:
            metadata = {
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "text_preview": chunk["text"][:100],
                "source_type": chunk["source_type"],
                "metadata": chunk.get("metadata", {})
            }
            metadata_list.append(metadata)
        
        # Add to vector store
        self.vector_store.add_embeddings(embeddings, metadata_list)
        
        stats = self.vector_store.get_stats()
        logger.info(f"Index built: {stats}")
        
        return stats
    
    def save_results(self, chunks: List[Dict],
                    embeddings: List[List[float]],
                    index_stats: Dict,
                    chunk_stats: Dict,
                    embedding_stats: Dict,
                    documents: Dict) -> STAGE6Results:
        """
        Save embedding results.
        
        Args:
            chunks: List of chunks
            embeddings: List of embeddings
            index_stats: Index statistics
            chunk_stats: Chunking statistics
            embedding_stats: Embedding generation statistics
            documents: Original documents
            
        Returns:
            STAGE6Results
        """
        logger.info("Saving results...")
        
        output_dir = self.data_dir / "embeddings"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save chunks
        self.json_store.save_list(
            chunks,
            str(output_dir / "chunks.json")
        )
        logger.info("Saved chunks to chunks.json")
        
        # Save embeddings with reduced precision (float16 for space saving)
        import numpy as np
        embeddings_fp16 = [
            np.array(emb, dtype=np.float32).astype(np.float16).tolist()
            for emb in embeddings
        ]
        self.json_store.save_list(
            embeddings_fp16,
            str(output_dir / "embeddings.json")
        )
        logger.info("Saved embeddings to embeddings.json")
        
        # Save vector store index
        index_path = str(output_dir / "index.faiss")
        metadata_path = str(output_dir / "index_metadata.json")
        self.vector_store.save(index_path, metadata_path)
        logger.info("Saved vector index")
        
        # Save statistics
        stats = {
            "stage": "blog6_embedding",
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "chunking": chunk_stats,
            "embedding": embedding_stats,
            "index": index_stats,
            "summary": {
                "total_documents": len(documents),
                "total_chunks": len(chunks),
                "embeddings_created": len(embeddings),
                "embedding_dimension": embedding_stats["embedding_dim"],
                "index_size_mb": Path(index_path).stat().st_size / (1024*1024) if Path(index_path).exists() else 0
            }
        }
        
        self.json_store.save_single(
            stats,
            str(output_dir / "embedding_stats.json")
        )
        logger.info("Saved statistics")
        
        results = STAGE6Results(
            total_documents=len(documents),
            total_chunks=len(chunks),
            embeddings_created=len(embeddings),
            embedding_dimension=embedding_stats["embedding_dim"],
            index_stats=index_stats,
            statistics=stats["summary"]
        )
        
        logger.info("✓ Blog 6 embedding complete")
        return results
    
    def run_blog6(self) -> STAGE6Results:
        """
        Run complete Blog 6 pipeline.
        
        Returns:
            STAGE6Results with all outputs
        """
        logger.info("=" * 60)
        logger.info("STAGE 6 - Blog 6: Embedding & Retrieval")
        logger.info("=" * 60)
        
        try:
            # 1. Load documents
            documents = self.load_deduplicated_documents()
            if not documents:
                raise ValueError("No deduplicated documents found")
            
            # 2. Create chunks
            chunks, chunk_stats = self.create_chunks(documents)
            if not chunks:
                raise ValueError("No chunks created from documents")
            
            # 3. Generate embeddings
            embeddings, embedding_stats = self.generate_embeddings(chunks)
            if not embeddings:
                raise ValueError("No embeddings generated")
            
            # 4. Build index
            index_stats = self.build_index(chunks, embeddings)
            
            # 5. Save results
            results = self.save_results(
                chunks, embeddings, index_stats,
                chunk_stats, embedding_stats, documents
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Blog 6 failed: {e}", exc_info=True)
            raise


def run_blog6(config: Dict = None) -> STAGE6Results:
    """
    Run Blog 6 embedding and retrieval pipeline.
    
    Args:
        config: Configuration dict
        
    Returns:
        STAGE6Results
    """
    orchestrator = Blog6Orchestrator(config)
    return orchestrator.run_blog6()


def load_retriever(config: Dict = None) -> Retriever:
    """
    Load a Retriever instance with saved embeddings and index.
    Used by Blog 7 for RAG.
    
    Args:
        config: Configuration dict
        
    Returns:
        Retriever instance with loaded index
    """
    config = config or {}
    data_dir = Path(config.get("data_dir", "data/processed"))
    embedding_index_dir = data_dir / "embeddings"
    
    model_name = config.get("embedding_model", "all-MiniLM-L6-v2")
    
    # Create retriever
    retriever = Retriever(model_name=model_name)
    
    # Load saved index
    index_path = str(embedding_index_dir / "index.faiss")
    if Path(index_path).exists():
        logger.info(f"Loading retriever index from {index_path}")
        retriever.load_index(index_path)
    else:
        logger.warning(f"Index not found at {index_path}. Running Blog 6 first may be needed.")
    
    return retriever
