"""
Main pipeline orchestrator for DocuAI RAG system.
Coordinates all 5 blog stages and embedding/retrieval.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from src.utils import logger, TimeTracker, DocumentStore, JSONStore
from src.config import get_config


class RAGPipeline:
    """
    Main pipeline: orchestrates Blog 1-5 + embedding + retrieval.
    Run stages sequentially or individually.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize pipeline.
        
        Args:
            config_path: Path to config.yaml
        """
        self.config = get_config()
        self.tracker = TimeTracker()
        
        # Initialize document stores for each stage
        self.audit_store = DocumentStore(
            Path(self.config.processed_path) / "audit_logs"
        )
        self.parsed_store = DocumentStore(
            Path(self.config.processed_path) / "parsed"
        )
        self.cleaned_store = DocumentStore(
            Path(self.config.processed_path) / "cleaned"
        )
        self.extracted_store = DocumentStore(
            Path(self.config.processed_path) / "extracted"
        )
        self.dedup_store = DocumentStore(
            Path(self.config.processed_path) / "deduplicated"
        )
        
        logger.info("RAGPipeline initialized")
    
    def run_stage_1_audit(self) -> Dict[str, Any]:
        """
        Blog 1: Corpus Audit & Quality Baselining
        Detects formats, scores quality, creates routing table.
        
        Returns:
            Summary of audit results
        """
        logger.info("=" * 60)
        logger.info("STAGE 1: Corpus Audit & Quality Baselining")
        logger.info("=" * 60)
        
        try:
            from src.audit import CorpusAuditor
            
            auditor = CorpusAuditor()
            summary = auditor.audit_corpus()
            
            logger.info(f"Blog 1 complete: {summary}")
            
            return {
                "stage": "audit",
                "status": "success",
                "summary": summary,
            }
        
        except Exception as e:
            logger.error(f"Blog 1 failed: {e}", exc_info=True)
            raise
    
    def run_stage_2_parsing(self) -> Dict[str, Any]:
        """
        Blog 2: Format-Aware Parsing
        Parses each document format correctly using routing table from Blog 1.
        
        Returns:
            Summary of parsing results
        """
        logger.info("=" * 60)
        logger.info("STAGE 2: Format-Aware Parsing")
        logger.info("=" * 60)
        
        self.tracker.start("parsing")
        
        try:
            from src.parsing import FormatAwareParser
            
            parser = FormatAwareParser()
            summary = parser.parse_corpus()
            
            logger.info(f"Blog 2 complete: {summary}")
            self.tracker.end("parsing", summary.get("total", 0))
            
            return {
                "stage": "parsing",
                "status": "success",
                "summary": summary,
            }
        
        except Exception as e:
            logger.error(f"Blog 2 failed: {e}", exc_info=True)
            raise
    
    def run_stage_3_cleaning(self) -> Dict[str, Any]:
        """
        Blog 3: Text Cleaning & Noise Elimination
        
        3-tier quality gating:
        1. Tier 1: Heuristic filters (length, encoding, character distribution)
        2. Tier 2: ML quality scoring (perplexity, coherence, diversity)
        3. Boilerplate & format-specific cleaning
        
        Returns:
            Summary of cleaning results
        """
        logger.info("=" * 60)
        logger.info("STAGE 3: Text Cleaning & Noise Elimination")
        logger.info("=" * 60)
        
        self.tracker.start("cleaning")
        
        try:
            from src.cleaning import TextCleaner
            
            cleaner = TextCleaner()
            summary = cleaner.clean_corpus()
            
            logger.info(f"Blog 3 complete: {summary}")
            self.tracker.end("cleaning", summary.get("total", 0))
            
            return {
                "stage": "cleaning",
                "status": "success",
                "summary": summary,
            }
        
        except Exception as e:
            logger.error(f"Blog 3 failed: {e}", exc_info=True)
            raise
    
    def run_stage_4_extraction(self) -> Dict[str, Any]:
        """
        Blog 4: Structured Knowledge Extraction
        Extracts tables, metadata, code blocks, document structure.
        
        Returns:
            Summary of extraction results
        """
        logger.info("=" * 60)
        logger.info("STAGE 4: Structured Knowledge Extraction")
        logger.info("=" * 60)
        
        self.tracker.start("extraction")
        
        try:
            from src.extraction import run_extraction
            
            results = run_extraction()
            
            logger.info(f"Blog 4 complete: {results}")
            self.tracker.end("extraction", results.get("extracted", 0))
            
            return {
                "stage": "extraction",
                "status": "success",
                "total_documents": results.get("total", 0),
                "extracted_documents": results.get("extracted", 0),
                "extraction_stats": results,
            }
        
        except Exception as e:
            logger.error(f"Blog 4 failed: {e}", exc_info=True)
            raise
    
    def run_stage_5_dedup(self) -> Dict[str, Any]:
        """
        Blog 5: Deduplication & Consolidation
        Detects duplicates using multiple similarity metrics.
        Merges knowledge from duplicate documents.
        Validates consolidated corpus.
        
        Returns:
            Summary of dedup results
        """
        logger.info("=" * 60)
        logger.info("STAGE 5: Deduplication & Consolidation")
        logger.info("=" * 60)
        
        self.tracker.start("dedup")
        
        try:
            from src.dedup import run_blog5
            
            results = run_blog5(self.config.__dict__)
            
            logger.info(f"Blog 5 complete: {results.statistics}")
            self.tracker.end("dedup", results.unique_documents)
            
            return {
                "stage": "dedup",
                "status": "success",
                "total_documents": results.total_documents,
                "unique_documents": results.unique_documents,
                "duplicates_removed": results.duplicates_removed,
                "dedup_stats": results.statistics,
            }
        
        except Exception as e:
            logger.error(f"Blog 5 failed: {e}", exc_info=True)
            raise
    
    def run_stage_6_embedding(self) -> Dict[str, Any]:
        """
        Blog 6: Embedding & Retrieval
        Generate embeddings and build vector index for semantic search.
        
        Returns:
            Summary of embedding results
        """
        logger.info("=" * 60)
        logger.info("STAGE 6: Embedding & Retrieval")
        logger.info("=" * 60)
        
        self.tracker.start("embedding")
        
        try:
            from src.embedding import run_blog6
            
            results = run_blog6(self.config.__dict__)
            
            logger.info(f"Blog 6 complete: {results.statistics}")
            self.tracker.end("embedding", results.total_chunks)
            
            return {
                "stage": "embedding",
                "status": "success",
                "total_documents": results.total_documents,
                "total_chunks": results.total_chunks,
                "embeddings_created": results.embeddings_created,
                "embedding_dimension": results.embedding_dimension,
                "embedding_stats": results.statistics,
            }
        
        except Exception as e:
            logger.error(f"Blog 6 failed: {e}", exc_info=True)
            raise
    
    def run_stage_7_rag(
        self,
        mode: str = "cli",
        llm_model: str = "mock",
        host: str = "0.0.0.0",
        port: int = 5000,
    ) -> Dict[str, Any]:
        """
        Blog 7: RAG System - User Interface & Deployment
        Provides CLI, REST API, and Streamlit interfaces for Q&A.
        
        Args:
            mode: Interface mode ("cli", "api", "streamlit", "api+streamlit")
            llm_model: LLM model ("mock", "gpt-3.5-turbo", etc.)
            host: API server host (for API mode)
            port: API server port (for API mode)
        
        Returns:
            Summary of RAG deployment
        """
        logger.info("=" * 60)
        logger.info("STAGE 7: RAG System - User Interface & Deployment")
        logger.info("=" * 60)
        
        self.tracker.start("blog7_rag")
        
        try:
            from src.embedding import load_retriever
            from src.rag import run_blog7_rag
            
            # Load the retriever from Blog 6
            logger.info(f"Loading retriever for {mode} mode...")
            retriever = load_retriever(self.config.__dict__)
            
            logger.info(f"Starting RAG system in {mode} mode with {llm_model} LLM")
            
            # Run the appropriate interface
            run_blog7_rag(
                retriever=retriever,
                mode=mode,
                llm_model=llm_model,
                host=host,
                port=port,
            )
            
            self.tracker.end("blog7_rag", 1)
            
            return {
                "stage": "rag",
                "status": "running",
                "mode": mode,
                "llm_model": llm_model,
                "api_host": host if mode in ["api", "api+streamlit"] else None,
                "api_port": port if mode in ["api", "api+streamlit"] else None,
            }
        
        except Exception as e:
            logger.error(f"Blog 7 failed: {e}", exc_info=True)
            raise
    
    def run_all(self) -> Dict[str, Any]:
        """Run all stages sequentially (Blog 1-6, not Blog 7 which is interactive)."""
        results = {
            "blog1": self.run_stage_1_audit(),
            "blog2": self.run_stage_2_parsing(),
            "blog3": self.run_stage_3_cleaning(),
            "blog4": self.run_stage_4_extraction(),
            "blog5": self.run_stage_5_dedup(),
            "blog6": self.run_stage_6_embedding(),
        }
        
        self.tracker.print_summary()
        return results


def run_pipeline(
    stage: str = "all",
    config_path: Optional[str] = None,
    **kwargs
) -> None:
    """
    Run pipeline from CLI.
    
    Args:
        stage: Which stage to run (all, blog1, blog2, ..., blog7)
        config_path: Path to config.yaml
        **kwargs: Additional arguments for blog7 (mode, llm_model, host, port)
    """
    pipeline = RAGPipeline(config_path)
    
    if stage == "all":
        pipeline.run_all()
    elif stage == "blog1":
        pipeline.run_stage_1_audit()
    elif stage == "blog2":
        pipeline.run_stage_2_parsing()
    elif stage == "blog3":
        pipeline.run_stage_3_cleaning()
    elif stage == "blog4":
        pipeline.run_stage_4_extraction()
    elif stage == "blog5":
        pipeline.run_stage_5_dedup()
    elif stage == "blog6":
        pipeline.run_stage_6_embedding()
    elif stage == "blog7":
        pipeline.run_stage_7_rag(
            mode=kwargs.get("mode", "cli"),
            llm_model=kwargs.get("llm_model", "mock"),
            host=kwargs.get("host", "0.0.0.0"),
            port=kwargs.get("port", 5000),
        )
    else:
        logger.error(f"Unknown stage: {stage}")
