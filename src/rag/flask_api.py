"""
Blog 7: Flask API for RAG

REST API endpoint for semantic search and question answering.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import asdict

try:
    from flask import Flask, request, jsonify, render_template_string
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from .rag_answerer import RAGAnswerer, create_rag_answerer

logger = logging.getLogger(__name__)


class RAGApi:
    """
    Flask API for RAG system.
    Provides REST endpoints for queries and retrieval.
    """
    
    def __init__(self, retriever, model_name: str = "mock"):
        """
        Initialize RAG API.
        
        Args:
            retriever: Retriever instance
            model_name: LLM model name
        """
        if not HAS_FLASK:
            logger.warning("Flask not installed. Install: pip install flask")
            self.app = None
            self.answerer = None
            return
        
        self.retriever = retriever
        self.answerer = create_rag_answerer(retriever, model_name)
        self.app = self._create_app()
    
    def _create_app(self) -> Flask:
        """Create Flask application"""
        app = Flask(__name__)
        
        # API endpoints
        @app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({"status": "ok", "service": "DocuAI RAG"})
        
        @app.route('/api/retrieve', methods=['POST'])
        def retrieve():
            """
            Retrieve relevant documents for query.
            
            Request: {"query": str, "top_k": int}
            Response: {"results": [...], "query": str}
            """
            try:
                data = request.get_json()
                query = data.get("query", "")
                top_k = data.get("top_k", 5)
                
                if not query:
                    return jsonify({"error": "query required"}), 400
                
                context = self.retriever.retrieve(query, top_k=top_k)
                
                results = []
                for result in context.results:
                    results.append({
                        "chunk_id": result.chunk_id,
                        "doc_id": result.doc_id,
                        "text": result.text_preview,
                        "similarity": result.similarity_score,
                        "source_type": result.source_type
                    })
                
                return jsonify({
                    "query": query,
                    "results": results,
                    "num_results": len(results)
                })
            
            except Exception as e:
                logger.error(f"Retrieval error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @app.route('/api/answer', methods=['POST'])
        def answer():
            """
            Answer a question using RAG.
            
            Request: {"question": str, "top_k": int, "extract_only": bool}
            Response: {"answer": str, "sources": [...], "confidence": float}
            """
            try:
                data = request.get_json()
                question = data.get("question", "")
                top_k = data.get("top_k", 5)
                extract_only = data.get("extract_only", False)
                
                if not question:
                    return jsonify({"error": "question required"}), 400
                
                rag_answer = self.answerer.answer(
                    question,
                    top_k=top_k,
                    extract_only=extract_only
                )
                
                return jsonify({
                    "question": rag_answer.query,
                    "answer": rag_answer.answer,
                    "sources": rag_answer.sources,
                    "confidence": rag_answer.confidence,
                    "context_length": len(rag_answer.context)
                })
            
            except Exception as e:
                logger.error(f"Answer error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @app.route('/api/batch', methods=['POST'])
        def batch_answer():
            """
            Answer multiple questions.
            
            Request: {"questions": [str, ...], "top_k": int}
            Response: {"answers": [...], "count": int}
            """
            try:
                data = request.get_json()
                questions = data.get("questions", [])
                top_k = data.get("top_k", 5)
                
                if not questions:
                    return jsonify({"error": "questions required"}), 400
                
                answers = self.answerer.answer_batch(questions, top_k=top_k)
                
                results = []
                for rag_answer in answers:
                    results.append({
                        "question": rag_answer.query,
                        "answer": rag_answer.answer,
                        "confidence": rag_answer.confidence,
                        "num_sources": len(rag_answer.sources)
                    })
                
                return jsonify({
                    "count": len(results),
                    "answers": results
                })
            
            except Exception as e:
                logger.error(f"Batch error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @app.route('/api/stats', methods=['GET'])
        def stats():
            """Get index statistics"""
            try:
                stats = self.retriever.get_stats()
                return jsonify(stats)
            except Exception as e:
                logger.error(f"Stats error: {e}")
                return jsonify({"error": str(e)}), 500
        
        return app
    
    def run(self, host: str = "0.0.0.0", port: int = 5000,
           debug: bool = False):
        """
        Run Flask API server.
        
        Args:
            host: Server host
            port: Server port
            debug: Debug mode
        """
        if self.app is None:
            logger.error("Flask not available")
            return
        
        logger.info(f"Starting RAG API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_api(retriever, model_name: str = "mock") -> Optional[RAGApi]:
    """
    Create RAG API instance.
    
    Args:
        retriever: Retriever instance
        model_name: LLM model name
        
    Returns:
        RAGApi instance or None if Flask not available
    """
    if not HAS_FLASK:
        logger.error("Flask required. Install: pip install flask")
        return None
    
    return RAGApi(retriever, model_name)
