"""
Blog 7: Chat Web Interface

Streamlit-based web interface for RAG queries.
Provides conversational chat experience.
"""

import logging
from typing import Dict, List, Optional

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

logger = logging.getLogger(__name__)


class ChatInterface:
    """
    Streamlit-based chat interface for RAG.
    """
    
    def __init__(self, answerer, title: str = "DocuAI - Document Q&A"):
        """
        Initialize chat interface.
        
        Args:
            answerer: RAG answerer instance
            title: Page title
        """
        if not HAS_STREAMLIT:
            logger.warning("Streamlit not installed. Install: pip install streamlit")
            self.answerer = None
            return
        
        self.answerer = answerer
        self.title = title
    
    def run(self):
        """Run Streamlit chat interface"""
        if not HAS_STREAMLIT:
            logger.error("Streamlit not available")
            return
        
        # Configure page
        st.set_page_config(
            page_title=self.title,
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Add title and description
        st.title("🤖 DocuAI - Document Q&A System")
        st.markdown("""
        Ask questions about your documents and get instant answers powered by semantic search.
        """)
        
        # Sidebar configuration
        with st.sidebar:
            st.header("⚙️ Settings")
            
            top_k = st.slider(
                "Number of context chunks",
                min_value=1,
                max_value=20,
                value=5,
                help="Number of relevant document chunks to retrieve"
            )
            
            extract_only = st.checkbox(
                "Extract only (no LLM)",
                value=False,
                help="Return raw context without LLM answer generation"
            )
            
            show_context = st.checkbox(
                "Show retrieved context",
                value=True,
                help="Display the context chunks used for answering"
            )
            
            st.markdown("---")
            st.markdown("**About DocuAI**")
            st.markdown("""
            DocuAI combines semantic search with language models to provide intelligent Q&A over your documents.
            
            **Features:**
            - 🔍 Semantic search across all documents
            - 💡 Context-aware answer generation
            - 📊 Relevance scoring
            - 🎯 Source attribution
            """)
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "answers" not in st.session_state:
            st.session_state.answers = {}
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                if message["role"] == "assistant" and "answer_id" in message:
                    answer_id = message["answer_id"]
                    if answer_id in st.session_state.answers:
                        answer_data = st.session_state.answers[answer_id]
                        
                        # Show confidence
                        st.markdown(f"**Confidence:** {answer_data['confidence']:.0%}")
                        
                        # Show context if enabled
                        if show_context and answer_data.get("context"):
                            with st.expander(f"📋 Context ({len(answer_data['sources'])} sources)"):
                                st.markdown(answer_data["context"])
        
        # Chat input
        if question := st.chat_input("Ask a question about your documents..."):
            # Add user message to history
            st.session_state.messages.append({
                "role": "user",
                "content": question
            })
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(question)
            
            # Generate answer
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        rag_answer = self.answerer.answer(
                            question,
                            top_k=top_k,
                            extract_only=extract_only
                        )
                        
                        # Store answer
                        answer_id = f"answer_{len(st.session_state.messages)}"
                        st.session_state.answers[answer_id] = {
                            "confidence": rag_answer.confidence,
                            "sources": rag_answer.sources,
                            "context": rag_answer.context
                        }
                        
                        # Display answer
                        st.markdown(rag_answer.answer)
                        st.markdown(f"**Confidence:** {rag_answer.confidence:.0%}")
                        
                        # Show context if enabled
                        if show_context:
                            with st.expander(f"📋 Context ({len(rag_answer.sources)} sources)"):
                                st.markdown(rag_answer.context)
                        
                        # Add to history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": rag_answer.answer,
                            "answer_id": answer_id
                        })
                    
                    except Exception as e:
                        error_msg = f"Error generating answer: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })


def create_streamlit_app(answerer) -> ChatInterface:
    """
    Create Streamlit chat application.
    
    Args:
        answerer: RAG answerer instance
        
    Returns:
        ChatInterface instance
    """
    if not HAS_STREAMLIT:
        logger.error("Streamlit not installed. Install: pip install streamlit")
        return None
    
    return ChatInterface(answerer)


def run_chat_interface(answerer):
    """
    Run Streamlit chat interface.
    
    Args:
        answerer: RAG answerer instance
    """
    if not HAS_STREAMLIT:
        logger.error("Streamlit not available")
        return
    
    chat_app = ChatInterface(answerer)
    chat_app.run()
