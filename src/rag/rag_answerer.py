"""
Blog 7: RAG Answerer

Generate answers to questions using retriever context.
Implements Retrieval-Augmented Generation with flexible LLM backends.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RAGAnswer:
    """RAG-generated answer with sources"""
    query: str
    answer: str
    sources: List[str]  # Retrieved chunk IDs used for context
    confidence: float  # 0-1, based on context relevance
    context: str  # Full context used for generation
    metadata: Dict = None


class PromptTemplate:
    """Manages RAG prompts for different scenarios"""
    
    # Default system prompt for RAG
    SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on \
provided context. Always cite your sources and be clear about what information comes \
from the provided context vs. general knowledge."""
    
    # RAG prompt template
    RAG_TEMPLATE = """Based on the following context, answer the question. \
If the context doesn't contain relevant information, say so clearly.

Context:
{context}

Question: {question}

Answer:"""
    
    # Extractive QA template (for simpler extraction without LLM)
    EXTRACTIVE_TEMPLATE = """Question: {question}

Relevant context passages:
{context}

Please extract the most relevant information to answer the question."""
    
    @staticmethod
    def format_rag_prompt(question: str, context: str) -> str:
        """Format RAG prompt with question and context"""
        return PromptTemplate.RAG_TEMPLATE.format(
            question=question,
            context=context
        )
    
    @staticmethod
    def format_extractive_prompt(question: str, context: str) -> str:
        """Format extractive QA prompt"""
        return PromptTemplate.EXTRACTIVE_TEMPLATE.format(
            question=question,
            context=context
        )


class LLMBackend:
    """
    Flexible LLM backend interface for RAG.
    Can be swapped for different models (OpenAI, HuggingFace, etc.)
    """
    
    def __init__(self, model_name: str = "mock"):
        """
        Initialize LLM backend.
        
        Args:
            model_name: Name of LLM model to use
        """
        self.model_name = model_name
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """Initialize LLM model"""
        if self.model_name == "mock":
            logger.info("Using mock LLM (no actual model loaded)")
            self.model = None
        else:
            logger.warning(f"LLM model '{self.model_name}' not available. Using mock.")
            self.model = None
    
    def generate(self, prompt: str, max_tokens: int = 500,
                temperature: float = 0.7) -> str:
        """
        Generate response from prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            
        Returns:
            Generated text
        """
        if self.model is None:
            # Mock generation: extract answer from prompt
            return self._mock_generate(prompt)
        else:
            try:
                # Real LLM generation would go here
                return self._mock_generate(prompt)
            except Exception as e:
                logger.error(f"Error generating with LLM: {e}")
                return self._mock_generate(prompt)
    
    def _mock_generate(self, prompt: str) -> str:
        """Mock LLM generation for testing"""
        # Simple mock: extract relevant parts
        lines = prompt.split('\n')
        
        # Find the "Answer:" line and extract following content
        answer_idx = None
        for i, line in enumerate(lines):
            if "Answer:" in line:
                answer_idx = i
                break
        
        if answer_idx is not None and answer_idx < len(lines) - 1:
            answer = '\n'.join(lines[answer_idx+1:]).strip()
        else:
            answer = "Based on the provided context, I can answer your question about the relevant information."
        
        return answer[:500]  # Limit to max_tokens


class RAGAnswerer:
    """
    Retrieval-Augmented Generation answerer.
    Combines retriever context with LLM for question answering.
    """
    
    def __init__(self, retriever, llm_backend: Optional[LLMBackend] = None):
        """
        Initialize RAG answerer.
        
        Args:
            retriever: Retriever instance for context retrieval
            llm_backend: LLM backend for answer generation
        """
        self.retriever = retriever
        self.llm_backend = llm_backend or LLMBackend("mock")
    
    def answer(self, question: str, top_k: int = 5,
              extract_only: bool = False) -> RAGAnswer:
        """
        Answer a question using RAG.
        
        Args:
            question: Question to answer
            top_k: Number of context chunks to retrieve
            extract_only: If True, return context without LLM generation
            
        Returns:
            RAGAnswer with answer and sources
        """
        logger.info(f"Answering question: {question[:100]}")
        
        # Retrieve context
        retrieval_context = self.retriever.retrieve(question, top_k=top_k)
        
        if not retrieval_context.results:
            logger.warning("No relevant context found")
            return RAGAnswer(
                query=question,
                answer="I couldn't find relevant information in the knowledge base to answer your question.",
                sources=[],
                confidence=0.0,
                context="",
                metadata={"error": "no_context_found"}
            )
        
        # Extract sources and build context
        sources = [r.chunk_id for r in retrieval_context.results]
        context_text = retrieval_context.context_text
        
        if extract_only:
            # Return context without LLM generation
            answer = context_text
            confidence = 0.5
        else:
            # Generate answer using LLM
            prompt = PromptTemplate.format_rag_prompt(question, context_text)
            answer = self.llm_backend.generate(prompt)
            
            # Calculate confidence based on retrieved relevance scores
            avg_similarity = sum(r.similarity_score for r in retrieval_context.results) / len(retrieval_context.results)
            confidence = avg_similarity
        
        rag_answer = RAGAnswer(
            query=question,
            answer=answer,
            sources=sources,
            confidence=confidence,
            context=context_text,
            metadata={
                "num_sources": len(sources),
                "avg_similarity": avg_similarity if not extract_only else 0.0
            }
        )
        
        logger.info(f"Generated answer with {len(sources)} sources (confidence: {confidence:.2f})")
        return rag_answer
    
    def answer_batch(self, questions: List[str],
                    top_k: int = 5) -> List[RAGAnswer]:
        """
        Answer multiple questions.
        
        Args:
            questions: List of questions
            top_k: Number of context chunks per question
            
        Returns:
            List of RAGAnswers
        """
        answers = []
        
        for question in questions:
            try:
                answer = self.answer(question, top_k=top_k)
                answers.append(answer)
            except Exception as e:
                logger.error(f"Error answering question: {e}")
                answers.append(RAGAnswer(
                    query=question,
                    answer=f"Error processing question: {str(e)}",
                    sources=[],
                    confidence=0.0,
                    context="",
                    metadata={"error": str(e)}
                ))
        
        return answers


def create_rag_answerer(retriever, model_name: str = "mock") -> RAGAnswerer:
    """
    Create RAG answerer instance.
    
    Args:
        retriever: Retriever instance
        model_name: LLM model to use
        
    Returns:
        RAGAnswerer instance
    """
    llm = LLMBackend(model_name)
    return RAGAnswerer(retriever, llm)
