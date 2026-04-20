"""
Blog 7: Gradio UI - Interactive Web Interface for RAG System

Provides a user-friendly interface for document querying.
"""

import logging
from typing import Tuple, List
import time

try:
    import gradio as gr
    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

from src.utils.logger import setup_logger
from src.rag.rag_engine import DocumentQA

logger = setup_logger(__name__)


class RAGInterface:
    """Gradio interface wrapper for RAG system"""
    
    def __init__(self, index_path: str = "data/processed/embeddings/index.faiss"):
        """
        Initialize RAG interface.
        
        Args:
            index_path: Path to FAISS index
        """
        logger.info("Initializing RAG interface...")
        
        try:
            self.qa_system = DocumentQA(index_path)
            self.ready = True
            logger.info("RAG system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.qa_system = None
            self.ready = False
    
    def answer_question(self, question: str, top_k: int = 5) -> Tuple[str, str, float, str]:
        """
        Answer a question and return formatted output.
        
        Args:
            question: User question
            top_k: Number of source documents
            
        Returns:
            Tuple of (answer, sources_text, confidence, timing_text)
        """
        if not self.ready:
            return ("System not initialized", "", 0.0, "")
        
        if not question or len(question.strip()) == 0:
            return ("Please enter a question", "", 0.0, "")
        
        try:
            result = self.qa_system.ask(question, top_k=top_k)
            
            # Format sources
            sources_text = "## Sources\n\n"
            if result["sources"]:
                for i, source in enumerate(result["sources"], 1):
                    sources_text += f"**Source {i}** ({source['type']})\n"
                    sources_text += f"- Document: {source['doc_id']}\n"
                    sources_text += f"- Similarity: {source['similarity']:.1%}\n"
                    sources_text += f"- Text: {source['text'][:150]}...\n\n"
            else:
                sources_text += "No sources found"
            
            # Format timing
            timing_text = (
                f"Retrieval: {result['timing']['retrieval_ms']:.1f}ms | "
                f"Generation: {result['timing']['generation_ms']:.1f}ms"
            )
            
            return (
                result["answer"],
                sources_text,
                result["confidence"],
                timing_text
            )
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return (f"Error: {str(e)}", "", 0.0, "")
    
    def update_top_k(self, value: int):
        """Update top_k parameter"""
        return f"Retrieving {value} top documents"
    
    def clear_all():
        """Clear all inputs"""
        return "", "", 0.0, ""


def create_interface() -> gr.Blocks:
    """
    Create Gradio interface.
    
    Returns:
        Gradio Blocks interface
    """
    if not HAS_GRADIO:
        raise ImportError("Gradio not installed. Install: pip install gradio")
    
    # Initialize RAG system
    rag = RAGInterface()
    
    with gr.Blocks(title="DocuAI RAG System", theme=gr.themes.Soft()) as demo:
        
        gr.Markdown("""
        # 🤖 DocuAI - Document Q&A System
        
        Ask questions about your documents. The system will retrieve relevant information
        and provide answers based on the document collection.
        
        ---
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Ask a Question")
                
                question = gr.Textbox(
                    label="Your Question",
                    placeholder="e.g., What are the main topics covered?",
                    lines=3
                )
                
                top_k = gr.Slider(
                    minimum=1,
                    maximum=20,
                    value=5,
                    step=1,
                    label="Number of Sources"
                )
                
                with gr.Row():
                    btn_submit = gr.Button("🔍 Search", variant="primary")
                    btn_clear = gr.Button("Clear")
            
            with gr.Column(scale=2):
                gr.Markdown("### Answer")
                
                answer = gr.Markdown(
                    value="*Ask a question to get started*"
                )
            
        with gr.Row():
            confidence = gr.Number(
                label="Confidence Score",
                interactive=False,
                value=0.0
            )
            
            timing = gr.Textbox(
                label="Response Time",
                interactive=False,
                value=""
            )
        
        gr.Markdown("---")
        
        with gr.Row():
            sources = gr.Markdown(
                value="## Sources\n\nSources will appear here",
                label="Sources"
            )
        
        # Event handlers
        def submit(q, k):
            answer_text, sources_text, conf, timing_text = rag.answer_question(q, int(k))
            return answer_text, sources_text, conf, timing_text
        
        def clear():
            return "", "", 0.0, ""
        
        btn_submit.click(
            fn=submit,
            inputs=[question, top_k],
            outputs=[answer, sources, confidence, timing]
        )
        
        btn_clear.click(
            fn=clear,
            outputs=[question, answer, confidence, timing]
        )
        
        # Allow Enter key to submit
        question.submit(
            fn=submit,
            inputs=[question, top_k],
            outputs=[answer, sources, confidence, timing]
        )
        
        gr.Markdown("""
        ---
        
        ### How It Works
        
        1. **Retrieval**: Your question is converted to embeddings and matched against document chunks
        2. **Context Gathering**: The most similar document sections are retrieved
        3. **Generation**: An answer is generated based on the retrieved context
        4. **Source Attribution**: Relevant sources are displayed with similarity scores
        
        ### Tips
        
        - Ask specific questions for better results
        - Use keywords from the documents
        - Adjust the number of sources to include more/less context
        
        **System Status**: {"🟢 Ready" if rag.ready else "🔴 Not Ready"}
        """)
    
    return demo


def launch_interface(share: bool = False, server_name: str = "0.0.0.0", 
                    server_port: int = 7860):
    """
    Launch the Gradio interface.
    
    Args:
        share: Whether to create a public share link
        server_name: Server address
        server_port: Server port
    """
    interface = create_interface()
    
    logger.info(f"Launching Gradio interface on {server_name}:{server_port}")
    
    interface.launch(
        share=share,
        server_name=server_name,
        server_port=server_port,
        show_error=True
    )


if __name__ == "__main__":
    launch_interface(share=True)
