"""
Blog 7: RAG System - User Interface & Deployment

Components:
- rag_answerer: RAG answer generation with flexible LLM backend
- flask_api: REST API endpoints for programmatic access
- chat_interface: Streamlit web chat interface
- cli_interface: Command-line interactive Q&A
- orchestrator: Unified entry point coordinating all components
"""

from .rag_answerer import (
    RAGAnswerer,
    RAGAnswer,
    LLMBackend,
    PromptTemplate,
)

from .flask_api import (
    RAGApi,
    create_api,
)

from .chat_interface import (
    ChatInterface,
    create_streamlit_app,
    run_chat_interface,
)

from .cli_interface import (
    CLIInterface,
    create_cli_interface,
)

from .orchestrator import (
    Blog7Orchestrator,
    create_orchestrator,
    run_blog7_rag,
)

__all__ = [
    # RAG Answering
    "RAGAnswerer",
    "RAGAnswer",
    "LLMBackend",
    "PromptTemplate",
    
    # Flask API
    "RAGApi",
    "create_api",
    
    # Chat Interface
    "ChatInterface",
    "create_streamlit_app",
    "run_chat_interface",
    
    # CLI Interface
    "CLIInterface",
    "create_cli_interface",
    
    # Orchestrator
    "Blog7Orchestrator",
    "create_orchestrator",
    "run_blog7_rag",
]
