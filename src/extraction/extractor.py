"""
Blog 4: Structured Knowledge Extraction Orchestrator

Main orchestrator that extracts tables, metadata, code, and structure.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
from tqdm import tqdm

from src.utils.json_store import JSONStore
from src.utils.logger import setup_logger
from src.config import get_config

from .table_extractor import extract_tables, ExtractedTable
from .metadata_extractor import extract_metadata, ExtractedMetadata
from .structure_extractor import (
    extract_code_blocks, extract_sections, 
    extract_paragraphs, extract_lists,
    ExtractedCode, ExtractedSection
)

logger = setup_logger(__name__)
config = get_config()


@dataclass
class ExtractedKnowledge:
    """Extracted knowledge from document"""
    doc_id: str
    format_type: str
    metadata: Dict
    tables: List[Dict]
    code_blocks: List[Dict]
    sections: List[Dict]
    paragraphs: List[str]
    lists: List[List[str]]
    total_tables: int
    total_code_blocks: int
    total_sections: int


class KnowledgeExtractor:
    """
    Main knowledge extraction orchestrator.
    
    Extracts structured information: tables, metadata, code, sections.
    """

    def __init__(self, config_dict: Optional[Dict] = None):
        """Initialize extractor"""
        self.config = config_dict or {}
        self.json_store = JSONStore()

    def extract_knowledge(self, doc_id: str, text: str, 
                         format_type: str = "") -> ExtractedKnowledge:
        """
        Extract all knowledge from document.
        
        Args:
            doc_id: Document ID
            text: Clean document text
            format_type: Document format
            
        Returns:
            ExtractedKnowledge
        """
        # Extract metadata
        metadata_obj = extract_metadata(text, doc_id)
        metadata_dict = asdict(metadata_obj)
        
        # Extract tables
        tables_list = extract_tables(text)
        tables_dict = [asdict(t) for t in tables_list]
        
        # Extract code blocks
        code_blocks_list = extract_code_blocks(text)
        code_dict = [asdict(c) for c in code_blocks_list]
        
        # Extract sections
        sections_list = extract_sections(text)
        sections_dict = [asdict(s) for s in sections_list]
        
        # Extract paragraphs
        paragraphs = extract_paragraphs(text)
        
        # Extract lists
        lists_result = extract_lists(text)
        
        return ExtractedKnowledge(
            doc_id=doc_id,
            format_type=format_type,
            metadata=metadata_dict,
            tables=tables_dict[:10],  # Limit to 10
            code_blocks=code_dict[:5],  # Limit to 5
            sections=sections_dict[:10],  # Limit to 10
            paragraphs=paragraphs[:20],  # Limit to 20
            lists=lists_result[:10],  # Limit to 10
            total_tables=len(tables_list),
            total_code_blocks=len(code_blocks_list),
            total_sections=len(sections_list)
        )

    def extract_corpus(self) -> Dict[str, Any]:
        """
        Extract knowledge from entire corpus.
        
        Returns:
            Summary dictionary
        """
        logger.info("Starting Knowledge Extraction (Blog 4)...")
        
        # Load accepted documents from Blog 3
        try:
            cleaned_file = Path(config.processed_path) / "cleaned" / "accepted_documents.json"
            accepted_docs = self.json_store.load_list(str(cleaned_file))
        except Exception as e:
            logger.error(f"Error loading accepted documents: {e}")
            accepted_docs = []
        
        if not accepted_docs:
            logger.error("No accepted documents found. Run Blog 3 first.")
            return {"status": "error", "message": "No accepted documents"}
        
        logger.info(f"Loaded {len(accepted_docs)} accepted documents")
        
        # Extract knowledge from all documents
        extracted_docs = []
        stats = {
            "total": len(accepted_docs),
            "extracted": 0,
            "by_format": {},
            "total_tables": 0,
            "total_code_blocks": 0,
            "total_sections": 0,
            "avg_tables_per_doc": 0,
            "avg_code_blocks_per_doc": 0,
        }
        
        for doc in tqdm(accepted_docs, desc="Extracting knowledge"):
            doc_id = doc["doc_id"]
            text = doc["cleaned_text"]
            format_type = doc.get("format_type", "unknown")
            
            # Extract knowledge
            knowledge = self.extract_knowledge(doc_id, text, format_type)
            extracted_docs.append(knowledge)
            
            # Update statistics
            if format_type not in stats["by_format"]:
                stats["by_format"][format_type] = {
                    "extracted": 0,
                    "tables": 0,
                    "code_blocks": 0
                }
            
            stats["by_format"][format_type]["extracted"] += 1
            stats["by_format"][format_type]["tables"] += knowledge.total_tables
            stats["by_format"][format_type]["code_blocks"] += knowledge.total_code_blocks
            
            stats["extracted"] += 1
            stats["total_tables"] += knowledge.total_tables
            stats["total_code_blocks"] += knowledge.total_code_blocks
            stats["total_sections"] += knowledge.total_sections
        
        # Calculate averages
        if extracted_docs:
            stats["avg_tables_per_doc"] = stats["total_tables"] / len(extracted_docs)
            stats["avg_code_blocks_per_doc"] = stats["total_code_blocks"] / len(extracted_docs)
        
        # Save results
        self._save_results(extracted_docs, stats)
        
        logger.info(f"Extraction complete: {stats['extracted']} documents, "
                   f"{stats['total_tables']} tables, "
                   f"{stats['total_code_blocks']} code blocks")
        
        return stats

    def _save_results(self, extracted_docs: List[ExtractedKnowledge], stats: Dict):
        """Save extracted knowledge"""
        output_dir = Path(config.processed_path) / "extracted"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save full extraction results
        results_data = [asdict(doc) for doc in extracted_docs]
        results_file = output_dir / "extracted_knowledge.json"
        self.json_store.save_list(results_data, str(results_file))
        logger.info(f"Saved extraction results to {results_file}")
        
        # Save statistics
        stats_file = output_dir / "extraction_stats.json"
        self.json_store.save_single(stats, str(stats_file))
        logger.info(f"Saved statistics to {stats_file}")


def run_extraction(sample_size: Optional[int] = None) -> Dict:
    """
    Run Blog 4 knowledge extraction.
    
    Args:
        sample_size: Optional limit
        
    Returns:
        Summary dictionary
    """
    extractor = KnowledgeExtractor()
    return extractor.extract_corpus()
