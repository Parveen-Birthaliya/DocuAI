"""
Blog 5: Deduplication and Consolidation Orchestrator

Main orchestrator combining deduplication, knowledge merging, and validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from tqdm import tqdm

from src.extraction.extractor import KnowledgeExtractor
from .similarity_detector import SimilarityDetector, SimilarityScore
from .deduplicator import Deduplicator, DeduplicationResult
from .merge_knowledge import KnowledgeMerger, MergedKnowledge
from .validator import CorpusValidator, ValidationReport
from src.utils.json_store import JSONStore
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Blog5Results:
    """Results from Blog 5 deduplication pipeline"""
    total_documents: int
    duplicate_groups: int
    unique_documents: int
    duplicates_removed: int
    merged_knowledge: List[Dict]
    validation_report: Dict
    statistics: Dict


class Blog5Orchestrator:
    """
    Main orchestrator for Blog 5: Deduplication and Consolidation
    
    Pipeline:
    1. Load extracted knowledge from Blog 4
    2. Detect and group duplicates
    3. Select canonical documents
    4. Merge knowledge from duplicates
    5. Validate consolidated corpus
    6. Save results
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.data_dir = Path(self.config.get("data_dir", "data/processed"))
        
        self.similarity_detector = SimilarityDetector(config)
        self.deduplicator = Deduplicator(config)
        self.merger = KnowledgeMerger()
        self.validator = CorpusValidator(config)
        
        self.json_store = JSONStore()
    
    def load_extracted_knowledge(self) -> Dict:
        """
        Load extracted knowledge from Blog 4.
        
        Returns:
            Dict mapping doc_id -> extracted knowledge
        """
        logger.info("Loading extracted knowledge from Blog 4...")
        
        knowledge_path = self.data_dir / "extracted" / "extracted_knowledge.json"
        
        if not knowledge_path.exists():
            logger.warning(f"Knowledge file not found: {knowledge_path}")
            return {}
        
        knowledge = self.json_store.load(str(knowledge_path))
        logger.info(f"Loaded knowledge for {len(knowledge)} documents")
        
        return knowledge
    
    def prepare_documents(self, knowledge: Dict) -> Dict[str, str]:
        """
        Prepare documents for deduplication.
        
        Args:
            knowledge: Dict mapping doc_id -> extracted knowledge
            
        Returns:
            Dict mapping doc_id -> combined text
        """
        documents = {}
        
        for doc_id, extracted in knowledge.items():
            # Combine all text from extracted knowledge
            text_parts = []
            
            # Add metadata
            if extracted.get("metadata"):
                meta = extracted["metadata"]
                if meta.get("title"):
                    text_parts.append(meta["title"])
                if meta.get("summary"):
                    text_parts.append(meta["summary"])
            
            # Add text
            if extracted.get("text"):
                text_parts.append(extracted["text"])
            
            # Combine into single document
            combined_text = " ".join(text_parts)
            documents[doc_id] = combined_text
        
        return documents
    
    def run_deduplication(self, documents: Dict[str, str]) -> Tuple[List[List[str]], Dict]:
        """
        Run deduplication on documents.
        
        Args:
            documents: Dict mapping doc_id -> text
            
        Returns:
            Tuple of (duplicate_groups, dedup_result)
        """
        logger.info("Running deduplication...")
        
        # Find duplicates
        dedup_result = self.deduplicator.deduplicate(documents)
        
        logger.info(f"Found {dedup_result.original_count} original documents")
        logger.info(f"Identified {dedup_result.duplicate_groups} duplicate groups")
        logger.info(f"Unique documents: {dedup_result.unique_count}")
        logger.info(f"Removal rate: {dedup_result.stats['removal_rate']:.1%}")
        
        return dedup_result.duplicate_groups, asdict(dedup_result)
    
    def merge_duplicate_knowledge(self, duplicate_groups: List[List[str]],
                                  knowledge: Dict) -> List[MergedKnowledge]:
        """
        Merge knowledge from duplicate groups.
        
        Args:
            duplicate_groups: List of duplicate document ID groups
            knowledge: Dict mapping doc_id -> extracted knowledge
            
        Returns:
            List of MergedKnowledge
        """
        logger.info("Merging duplicate knowledge...")
        
        merged = []
        
        for group in tqdm(duplicate_groups, desc="Merging duplicates"):
            try:
                merged_knowledge = self.merger.merge_duplicate_set(group, knowledge)
                merged.append(merged_knowledge)
            except Exception as e:
                logger.error(f"Error merging group {group}: {e}")
        
        logger.info(f"Merged {len(merged)} duplicate groups")
        
        return merged
    
    def validate_results(self, documents: Dict[str, str],
                        dedup_result: Dict) -> ValidationReport:
        """
        Validate deduplication results.
        
        Args:
            documents: Dict mapping doc_id -> text
            dedup_result: Deduplication results
            
        Returns:
            ValidationReport
        """
        logger.info("Validating results...")
        
        # Build format map (estimate from document sizes)
        formats = {"unknown": len(documents)}
        
        # Build document dict for validator
        doc_dict = {}
        for doc_id, text in documents.items():
            doc_dict[doc_id] = {
                "text": text,
                "metadata": {"language": "unknown"}
            }
        
        # Validate
        report = self.validator.validate_corpus(doc_dict, formats)
        logger.info(f"Validation: {report.passed} passed, {report.failed} failed, {report.warnings} warnings")
        logger.info(f"Consistency score: {report.consistency_score:.2%}")
        
        return report
    
    def save_results(self, duplicate_groups: List[List[str]],
                    merged_knowledge: List[MergedKnowledge],
                    dedup_result: Dict,
                    validation_report: ValidationReport,
                    documents: Dict[str, str]) -> Blog5Results:
        """
        Save deduplication results.
        
        Args:
            duplicate_groups: List of duplicate document ID groups
            merged_knowledge: List of merged knowledge
            dedup_result: Deduplication result dict
            validation_report: Validation report
            documents: Original documents dict
            
        Returns:
            Blog5Results
        """
        logger.info("Saving results...")
        
        output_dir = self.data_dir / "deduplicated"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save deduplicated knowledge
        merged_dicts = []
        for merged in merged_knowledge:
            merged_dicts.append({
                "canonical_doc_id": merged.canonical_doc_id,
                "duplicate_doc_ids": merged.duplicate_doc_ids,
                "merged_tables": merged.merged_tables,
                "merged_metadata": merged.merged_metadata,
                "merged_code_blocks": merged.merged_code_blocks,
                "merged_sections": merged.merged_sections,
                "merge_confidence": merged.merge_confidence
            })
        
        self.json_store.save(
            str(output_dir / "deduplicated_knowledge.json"),
            merged_dicts
        )
        logger.info(f"Saved deduplicated knowledge to deduplicated_knowledge.json")
        
        # Save deduplication statistics
        stats = {
            "deduplication": dedup_result,
            "validation": {
                "total_docs": validation_report.total_docs,
                "passed": validation_report.passed,
                "failed": validation_report.failed,
                "warnings": validation_report.warnings,
                "consistency_score": validation_report.consistency_score,
                "issues_count": len(validation_report.issues)
            },
            "summary": {
                "original_documents": len(documents),
                "duplicate_groups": len(duplicate_groups),
                "merged_sets": len(merged_knowledge),
                "unique_documents": dedup_result["unique_count"],
                "duplicates_removed": dedup_result["stats"]["duplicates_detected"],
                "removal_rate": dedup_result["stats"]["removal_rate"]
            }
        }
        
        self.json_store.save(
            str(output_dir / "dedup_stats.json"),
            stats
        )
        logger.info(f"Saved deduplication statistics to dedup_stats.json")
        
        # Create results
        results = Blog5Results(
            total_documents=len(documents),
            duplicate_groups=len(duplicate_groups),
            unique_documents=dedup_result["unique_count"],
            duplicates_removed=dedup_result["stats"]["duplicates_detected"],
            merged_knowledge=merged_dicts,
            validation_report=asdict(validation_report),
            statistics=stats["summary"]
        )
        
        logger.info("✓ Blog 5 deduplication complete")
        
        return results
    
    def run_blog5(self) -> Blog5Results:
        """
        Run complete Blog 5 pipeline.
        
        Returns:
            Blog5Results with all outputs
        """
        logger.info("=" * 60)
        logger.info("STAGE 5 - Blog 5: Deduplication & Consolidation")
        logger.info("=" * 60)
        
        try:
            # 1. Load extracted knowledge
            knowledge = self.load_extracted_knowledge()
            if not knowledge:
                raise ValueError("No extracted knowledge found")
            
            # 2. Prepare documents
            documents = self.prepare_documents(knowledge)
            logger.info(f"Prepared {len(documents)} documents for deduplication")
            
            # 3. Run deduplication
            duplicate_groups, dedup_result = self.run_deduplication(documents)
            
            # 4. Merge duplicate knowledge
            merged_knowledge = self.merge_duplicate_knowledge(duplicate_groups, knowledge)
            
            # 5. Validate results
            validation_report = self.validate_results(documents, dedup_result)
            
            # 6. Save results
            results = self.save_results(
                duplicate_groups,
                merged_knowledge,
                dedup_result,
                validation_report,
                documents
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Blog 5 failed: {e}", exc_info=True)
            raise


def run_blog5(config: Dict = None) -> Blog5Results:
    """
    Run Blog 5 deduplication pipeline.
    
    Args:
        config: Configuration dict
        
    Returns:
        Blog5Results
    """
    orchestrator = Blog5Orchestrator(config)
    return orchestrator.run_blog5()
