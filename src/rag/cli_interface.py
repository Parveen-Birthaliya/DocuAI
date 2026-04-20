"""
Blog 7: Command-Line Interface

CLI for local RAG usage without web interface.
"""

import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class CLIInterface:
    """Command-line interface for RAG."""
    
    def __init__(self, answerer):
        """
        Initialize CLI interface.
        
        Args:
            answerer: RAG answerer instance
        """
        self.answerer = answerer
    
    def run_interactive(self):
        """Run interactive Q&A loop."""
        print("\n" + "=" * 70)
        print("🤖 DocuAI - Document Q&A System (CLI)")
        print("=" * 70)
        print("\nTypes 'quit' or 'exit' to exit")
        print("Type 'top_k <number>' to change context chunks (default: 5)")
        print("Type 'extract' to toggle extract-only mode")
        print("-" * 70 + "\n")
        
        top_k = 5
        extract_only = False
        
        while True:
            try:
                question = input("\n📝 Question: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ["quit", "exit"]:
                    print("\nGoodbye! 👋")
                    break
                
                # Handle settings
                if question.lower().startswith("top_k"):
                    try:
                        top_k = int(question.split()[-1])
                        print(f"✓ Context chunks set to {top_k}")
                        continue
                    except (ValueError, IndexError):
                        print("✗ Invalid format. Use: top_k <number>")
                        continue
                
                if question.lower() == "extract":
                    extract_only = not extract_only
                    mode = "extract-only" if extract_only else "full generation"
                    print(f"✓ Mode changed to: {mode}")
                    continue
                
                # Get answer
                print("\n⏳ Generating answer...")
                rag_answer = self.answerer.answer(
                    question,
                    top_k=top_k,
                    extract_only=extract_only
                )
                
                # Display results
                print("\n" + "-" * 70)
                print(f"💡 Answer:\n{rag_answer.answer}")
                print("-" * 70)
                print(f"\n📊 Confidence: {rag_answer.confidence:.0%}")
                print(f"📚 Sources: {len(rag_answer.sources)} chunk(s)")
                
                if rag_answer.context:
                    print("\n📋 Context:")
                    print("-" * 70)
                    print(rag_answer.context[:500] + ("..." if len(rag_answer.context) > 500 else ""))
                    print("-" * 70)
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Exiting... 👋")
                break
            except Exception as e:
                print(f"\n✗ Error: {str(e)}")
                logger.error(f"CLI error: {e}", exc_info=True)
    
    def answer_question(self, question: str, top_k: int = 5) -> str:
        """
        Answer single question and return formatted result.
        
        Args:
            question: Question to answer
            top_k: Number of context chunks
            
        Returns:
            Formatted answer string
        """
        try:
            rag_answer = self.answerer.answer(question, top_k=top_k)
            
            result = f"""
📝 Question: {question}

💡 Answer:
{rag_answer.answer}

📊 Confidence: {rag_answer.confidence:.0%}
📚 Sources: {len(rag_answer.sources)} chunk(s)
"""
            return result
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return f"Error: {str(e)}"


def create_cli_interface(answerer) -> CLIInterface:
    """
    Create CLI interface.
    
    Args:
        answerer: RAG answerer instance
        
    Returns:
        CLIInterface instance
    """
    return CLIInterface(answerer)
