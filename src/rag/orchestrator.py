"""
Blog 7: RAG System Orchestrator

Coordinates all Blog 7 components:
- RAG answerer
- Flask REST API
- Streamlit chat interface
- CLI interface
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Literal

from .rag_answerer import RAGAnswerer, LLMBackend
from .flask_api import RAGApi, create_api
from .chat_interface import ChatInterface, create_streamlit_app
from .cli_interface import CLIInterface, create_cli_interface

logger = logging.getLogger(__name__)


class Blog7Orchestrator:
    """
    Orchestrates all Blog 7 components.
    
    Provides unified entry point for:
    - RAG answering (rag_answerer.py)
    - REST API (flask_api.py)
    - Streamlit chat (chat_interface.py)
    - CLI interface (cli_interface.py)
    """
    
    def __init__(
        self,
        retriever,
        llm_model: str = "mock",
        config: Optional[dict] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            retriever: Vector retriever instance from Blog 6
            llm_model: LLM model name ("mock", "gpt-3.5-turbo", etc.)
            config: Optional configuration dict
        """
        self.retriever = retriever
        self.llm_model = llm_model
        self.config = config or {}
        
        # Initialize LLM backend
        self.llm_backend = LLMBackend(model=llm_model)
        
        # Initialize RAG answerer
        self.answerer = RAGAnswerer(
            retriever=retriever,
            llm_backend=self.llm_backend
        )
        
        logger.info(f"Blog7Orchestrator initialized with LLM: {llm_model}")
    
    def get_answerer(self) -> RAGAnswerer:
        """Get RAG answerer instance."""
        return self.answerer
    
    def create_flask_api(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        debug: bool = False
    ) -> RAGApi:
        """
        Create Flask REST API.
        
        Args:
            host: Server host
            port: Server port
            debug: Debug mode
            
        Returns:
            RAGApi instance
        """
        api = create_api(
            retriever=self.retriever,
            llm_model=self.llm_model
        )
        logger.info(f"Flask API created: {host}:{port}")
        return api
    
    def run_flask_api(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        debug: bool = False
    ):
        """
        Start Flask REST API server.
        
        Args:
            host: Server host
            port: Server port
            debug: Debug mode
        """
        api = self.create_flask_api(host=host, port=port, debug=debug)
        logger.info(f"Starting Flask API on {host}:{port}")
        api.run(host=host, port=port, debug=debug)
    
    def create_streamlit_app(self) -> ChatInterface:
        """
        Create Streamlit chat interface.
        
        Returns:
            ChatInterface instance
        """
        chat_app = create_streamlit_app(self.answerer)
        logger.info("Streamlit app created")
        return chat_app
    
    def run_streamlit_app(self):
        """Start Streamlit chat interface."""
        chat_app = self.create_streamlit_app()
        if chat_app:
            chat_app.run()
        else:
            logger.error("Could not create Streamlit app")
    
    def create_cli_interface(self) -> CLIInterface:
        """
        Create CLI interface.
        
        Returns:
            CLIInterface instance
        """
        cli = create_cli_interface(self.answerer)
        logger.info("CLI interface created")
        return cli
    
    def run_cli_interactive(self):
        """Start interactive CLI Q&A."""
        cli = self.create_cli_interface()
        cli.run_interactive()
    
    def answer(self, question: str, top_k: int = 5, extract_only: bool = False):
        """
        Answer single question.
        
        Args:
            question: Question to answer
            top_k: Number of context chunks
            extract_only: Return context only without LLM
            
        Returns:
            RAGAnswer instance
        """
        return self.answerer.answer(
            question,
            top_k=top_k,
            extract_only=extract_only
        )
    
    def answer_batch(self, questions: list, top_k: int = 5, extract_only: bool = False):
        """
        Answer multiple questions.
        
        Args:
            questions: List of questions
            top_k: Number of context chunks
            extract_only: Return context only without LLM
            
        Returns:
            List of RAGAnswer instances
        """
        return self.answerer.answer_batch(
            questions,
            top_k=top_k,
            extract_only=extract_only
        )


def create_orchestrator(
    retriever,
    llm_model: str = "mock",
    config: Optional[dict] = None
) -> Blog7Orchestrator:
    """
    Create Blog 7 orchestrator.
    
    Args:
        retriever: Vector retriever instance
        llm_model: LLM model name
        config: Optional configuration
        
    Returns:
        Blog7Orchestrator instance
    """
    return Blog7Orchestrator(retriever, llm_model, config)


def run_blog7_rag(
    retriever,
    mode: Literal["cli", "api", "streamlit", "api+streamlit"] = "cli",
    llm_model: str = "mock",
    host: str = "0.0.0.0",
    port: int = 5000,
    **kwargs
):
    """
    Main entry point for Blog 7 RAG system.
    
    Args:
        retriever: Vector retriever from Blog 6
        mode: Execution mode
            - "cli": Interactive command-line
            - "api": Flask REST API only
            - "streamlit": Streamlit web interface only
            - "api+streamlit": Both Flask API and Streamlit
        llm_model: LLM model name
        host: API server host
        port: API server port
        **kwargs: Additional configuration
    """
    logger.info(f"Starting Blog 7 RAG system in mode: {mode}")
    
    orchestrator = create_orchestrator(retriever, llm_model)
    
    if mode == "cli":
        orchestrator.run_cli_interactive()
    
    elif mode == "api":
        orchestrator.run_flask_api(host=host, port=port)
    
    elif mode == "streamlit":
        orchestrator.run_streamlit_app()
    
    elif mode == "api+streamlit":
        # In practice, these would run in separate processes
        # For now, start with Streamlit (which blocks)
        logger.info("Starting in API+Streamlit mode")
        orchestrator.run_streamlit_app()
    
    else:
        raise ValueError(f"Unknown mode: {mode}")
