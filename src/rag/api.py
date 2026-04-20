"""
Blog 7: REST API - FastAPI/Flask Application for RAG System

Provides REST endpoints for document querying and system management.
"""

import logging
from typing import List, Optional, Dict
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from src.utils.logger import setup_logger
from src.rag.rag_engine import DocumentQA, RAGResponse

logger = setup_logger(__name__)


# Request/Response models
class QueryRequest(BaseModel):
    """Query request model"""
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    """Query response model"""
    question: str
    answer: str
    confidence: float
    sources: List[Dict]
    timing: Dict


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    system: str
    version: str


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI application instance
    """
    if not HAS_FASTAPI:
        raise ImportError("FastAPI not installed. Install: pip install fastapi uvicorn")
    
    app = FastAPI(
        title="DocuAI RAG System",
        description="Retrieval Augmented Generation for document Q&A",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize Document QA system
    qa_system = None
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize RAG system on startup"""
        nonlocal qa_system
        logger.info("Starting RAG system...")
        
        try:
            qa_system = DocumentQA()
            logger.info("RAG system started successfully")
        except Exception as e:
            logger.error(f"Failed to start RAG system: {e}")
            qa_system = None
    
    @app.get("/health", response_model=HealthResponse)
    async def health():
        """Health check endpoint"""
        return HealthResponse(
            status="ready" if qa_system else "not_ready",
            system="DocuAI RAG",
            version="1.0.0"
        )
    
    @app.get("/info")
    async def info():
        """System information endpoint"""
        if not qa_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        return {
            "system": "DocuAI RAG",
            "version": "1.0.0",
            "info": qa_system.get_system_info()
        }
    
    @app.post("/query", response_model=QueryResponse)
    async def query(request: QueryRequest):
        """
        Query the RAG system.
        
        Args:
            request: Query request with question
            
        Returns:
            Query response with answer and sources
        """
        if not qa_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        if not request.question or len(request.question.strip()) == 0:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        try:
            result = qa_system.ask(request.question, top_k=request.top_k)
            
            return QueryResponse(
                question=result["question"],
                answer=result["answer"],
                confidence=result["confidence"],
                sources=result["sources"],
                timing=result["timing"]
            )
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    @app.post("/batch_query")
    async def batch_query(requests: List[QueryRequest]):
        """
        Process multiple queries.
        
        Args:
            requests: List of query requests
            
        Returns:
            List of responses
        """
        if not qa_system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        results = []
        
        for request in requests:
            try:
                result = qa_system.ask(request.question, top_k=request.top_k)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                results.append({
                    "question": request.question,
                    "error": str(e)
                })
        
        return results
    
    return app


# For development/testing
if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    
    # Run with: python -m uvicorn src.blog7_rag.api:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
