"""
Blog 7: RAG Engine - Query Answering with Retrieval Augmented Generation

Combines document retrieval with language generation for intelligent Q&A.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.embedding.retriever import Retriever, RetrievalContext
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG engine"""
    query: str
    response: str
    context: str
    sources: List[Dict]
    confidence: float
    retrieval_time: float
    generation_time: float


class SimpleRAGGenerator:
    """
    Simple RAG engine using template-based generation.
    No external LLM API needed.
    """
    
    def __init__(self):
        self.name = "SimpleRAG"
    
    def generate(self, query: str, context: str) -> str:
        """
        Generate response using templates and context extraction.
        
        Args:
            query: User query
            context: Retrieved context chunks
            
        Returns:
            Generated response
        """
        # Extract key information from context
        context_lines = [line.strip() for line in context.split('\n') if line.strip()]
        
        if not context_lines:
            return f"I don't have enough information to answer '{query}'."
        
        # Simple template-based generation
        response_parts = []
        
        # Opening
        response_parts.append(f"Based on the available information:")
        response_parts.append("")
        
        # Add context information
        for i, line in enumerate(context_lines[:3], 1):  # Use top 3 context chunks
            clean_line = line.replace("[DOCUMENT]", "").replace("[TABLE]", "").replace("[CODE]", "").strip()
            if len(clean_line) > 200:
                clean_line = clean_line[:200] + "..."
            if clean_line:
                response_parts.append(f"• {clean_line}")
        
        # Closing
        response_parts.append("")
        response_parts.append("This information is derived from the document collection.")
        
        return "\n".join(response_parts)


class RAGEngine:
    """
    Retrieval Augmented Generation engine.
    Combines document retrieval + generation for Q&A.
    """
    
    def __init__(self, retriever: Retriever, generator=None):
        """
        Initialize RAG engine.
        
        Args:
            retriever: Retriever instance with indexed documents
            generator: Optional generator (uses simple template if None)
        """
        self.retriever = retriever
        self.generator = generator or SimpleRAGGenerator()
        
        logger.info(f"RAG Engine initialized with {generator.__class__.__name__ if generator else 'SimpleRAGGenerator'}")
    
    def query(self, question: str, top_k: int = 5,
             return_sources: bool = True) -> RAGResponse:
        """
        Answer question using RAG.
        
        Args:
            question: User question
            top_k: Number of context chunks to retrieve
            return_sources: Whether to return source information
            
        Returns:
            RAGResponse with answer and sources
        """
        import time
        
        logger.info(f"Processing query: {question[:100]}")
        
        # Retrieve relevant context
        retrieval_start = time.time()
        context = self.retriever.retrieve(question, top_k=top_k)
        retrieval_time = time.time() - retrieval_start
        
        if not context.results:
            logger.warning("No relevant documents found")
            return RAGResponse(
                query=question,
                response="Sorry, I couldn't find relevant information to answer your question.",
                context="",
                sources=[],
                confidence=0.0,
                retrieval_time=retrieval_time,
                generation_time=0.0
            )
        
        # Generate response
        generation_start = time.time()
        response = self.generator.generate(question, context.context_text)
        generation_time = time.time() - generation_start
        
        # Extract sources
        sources = []
        if return_sources:
            sources = [
                {
                    "chunk_id": result.chunk_id,
                    "doc_id": result.doc_id,
                    "text": result.text_preview,
                    "similarity": round(result.similarity_score, 3),
                    "type": result.source_type
                }
                for result in context.results
            ]
        
        # Confidence score based on retrieval results
        avg_similarity = sum(r.similarity_score for r in context.results) / len(context.results)
        
        rag_response = RAGResponse(
            query=question,
            response=response,
            context=context.context_text,
            sources=sources,
            confidence=round(avg_similarity, 3),
            retrieval_time=round(retrieval_time, 3),
            generation_time=round(generation_time, 3)
        )
        
        logger.info(f"Generated response (confidence: {rag_response.confidence})")
        return rag_response
    
    def batch_query(self, questions: List[str], top_k: int = 5) -> List[RAGResponse]:
        """
        Answer multiple questions.
        
        Args:
            questions: List of questions
            top_k: Number of context chunks per query
            
        Returns:
            List of RAGResponse
        """
        responses = []
        
        for question in questions:
            response = self.query(question, top_k=top_k)
            responses.append(response)
        
        return responses
    
    def get_stats(self) -> Dict:
        """Get engine statistics"""
        return {
            "generator": self.generator.name if hasattr(self.generator, 'name') else 'Unknown',
            "retriever_stats": self.retriever.get_stats()
        }


class DocumentQA:
    """
    High-level interface for document question-answering.
    """
    
    def __init__(self, index_path: str = "data/processed/embeddings/index.faiss"):
        """
        Initialize Document QA system.
        
        Args:
            index_path: Path to FAISS index
        """
        # Load retriever with index
        self.retriever = self._load_retriever(index_path)
        
        # Initialize RAG engine
        self.engine = RAGEngine(self.retriever)
        
        logger.info("Document QA system initialized")
    
    def _load_retriever(self, index_path: str) -> Retriever:
        """Load retriever from saved index"""
        from src.embedding import create_retriever
        
        retriever = create_retriever()
        
        try:
            retriever.load_index(index_path)
            logger.info(f"Loaded index from {index_path}")
        except Exception as e:
            logger.warning(f"Could not load index: {e}")
        
        return retriever
    
    def ask(self, question: str, top_k: int = 5) -> Dict:
        """
        Ask a question and get answer with sources.
        
        Args:
            question: Question to ask
            top_k: Number of source documents to retrieve
            
        Returns:
            Dict with answer, confidence, sources, timing
        """
        response = self.engine.query(question, top_k=top_k)
        
        return {
            "question": response.query,
            "answer": response.response,
            "confidence": response.confidence,
            "sources": response.sources,
            "timing": {
                "retrieval_ms": response.retrieval_time * 1000,
                "generation_ms": response.generation_time * 1000
            }
        }
    
    def get_system_info(self) -> Dict:
        """Get system information and statistics"""
        return {
            "status": "ready",
            "engine_type": "RAG",
            "generator": "TemplateBasedGenerator",
            "stats": self.engine.get_stats()
        }
