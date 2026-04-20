"""
Blog 3: Text Cleaning & Noise Elimination Orchestrator

Implements 3-tier quality gating:
1. Tier 1: Fast heuristic filters
2. Tier 2: ML-based quality scoring
3. Boilerplate detection and removal
4. Format-specific cleaning
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
from tqdm import tqdm

from src.utils.json_store import JSONStore
from src.utils.logger import get_logger
from src.utils.tracker import PerformanceTracker
from src.utils.config import config

from .tier1_heuristics import Tier1HeuristicFilter, Tier1Results
from .tier2_ml_scorer import Tier2MLScorer, Tier2Results
from .boilerplate_detector import BoilerplateDetector, BoilerplateAnalysis
from .format_cleaners import clean_text

logger = get_logger(__name__)


@dataclass
class CleaningResults:
    """Results from comprehensive text cleaning"""
    doc_id: str
    original_length: int
    cleaned_length: int
    tier1_result: Dict  # Pass/fail
    tier2_result: Dict  # Quality score
    boilerplate_removed: bool
    boilerplate_ratio: float
    final_status: str  # "accept", "review", "reject"
    cleaned_text: str
    metadata: Dict


class TextCleaner:
    """
    Main text cleaning orchestrator.
    
    Implements 3-tier quality gating for comprehensive document cleaning.
    """

    def __init__(self, config_dict: Optional[Dict] = None):
        """Initialize cleaner"""
        self.config = config_dict or {}
        self.json_store = JSONStore()
        self.tracker = PerformanceTracker()
        
        # Initialize tier processors
        self.tier1_filter = Tier1HeuristicFilter(self.config.get("tier1", {}))
        self.tier2_scorer = Tier2MLScorer(self.config.get("tier2", {}))
        self.boilerplate_detector = BoilerplateDetector(self.config.get("boilerplate", {}))

    def clean_document(self, doc_id: str, text: str, format_type: str) -> CleaningResults:
        """
        Apply comprehensive cleaning pipeline.
        
        Args:
            doc_id: Document ID
            text: Raw extracted text
            format_type: Document format (pdf, html, json, etc.)
            
        Returns:
            CleaningResults with cleaned text and metadata
        """
        original_length = len(text)
        
        # TIER 1: Fast heuristic filtering
        tier1_result = self.tier1_filter.evaluate(text)
        
        if not tier1_result.passed:
            logger.warning(f"Document {doc_id} failed Tier 1: {tier1_result.failures}")
            return CleaningResults(
                doc_id=doc_id,
                original_length=original_length,
                cleaned_length=0,
                tier1_result=asdict(tier1_result),
                tier2_result={},
                boilerplate_removed=False,
                boilerplate_ratio=0.0,
                final_status="reject",
                cleaned_text="",
                metadata={"reason": "Tier 1 rejection"}
            )
        
        # TIER 2: ML quality scoring
        tier2_result = self.tier2_scorer.evaluate(text)
        
        if tier2_result.recommendation == "reject":
            logger.warning(f"Document {doc_id} failed Tier 2: score={tier2_result.score:.2f}")
            return CleaningResults(
                doc_id=doc_id,
                original_length=original_length,
                cleaned_length=0,
                tier1_result=asdict(tier1_result),
                tier2_result=asdict(tier2_result),
                boilerplate_removed=False,
                boilerplate_ratio=0.0,
                final_status="reject",
                cleaned_text="",
                metadata={"reason": "Tier 2 rejection", "tier2_score": tier2_result.score}
            )
        
        # BOILERPLATE DETECTION
        boilerplate_analysis = self.boilerplate_detector.analyze(text)
        
        # Start with text, remove boilerplate if needed
        cleaned_text = boilerplate_analysis.cleaned_text
        
        # FORMAT-SPECIFIC CLEANING
        cleaned_text = clean_text(cleaned_text, format_type)
        
        cleaned_length = len(cleaned_text)
        
        # FINAL DECISION LOGIC
        if tier2_result.recommendation == "review":
            final_status = "review"
        else:
            final_status = "accept"
        
        # Reject if cleaned text is too short after processing
        if cleaned_length < 100:
            final_status = "reject"
            logger.warning(f"Document {doc_id}: Cleaned text too short ({cleaned_length} chars)")
        
        return CleaningResults(
            doc_id=doc_id,
            original_length=original_length,
            cleaned_length=cleaned_length,
            tier1_result=asdict(tier1_result),
            tier2_result=asdict(tier2_result),
            boilerplate_removed=boilerplate_analysis.is_boilerplate,
            boilerplate_ratio=boilerplate_analysis.boilerplate_ratio,
            final_status=final_status,
            cleaned_text=cleaned_text,
            metadata={
                "tier1_recommendation": tier1_result.recommendation,
                "tier2_recommendation": tier2_result.recommendation,
                "boilerplate_types": boilerplate_analysis.detected_types,
                "compression_ratio": cleaned_length / max(original_length, 1),
                "tier1_avg_score": sum(tier1_result.scores.values()) / len(tier1_result.scores),
                "tier2_score": tier2_result.score,
                "format_type": format_type,
            }
        )

    def clean_corpus(self) -> Dict[str, Any]:
        """
        Clean entire corpus from parsed_results.json.
        
        Returns:
            Summary dictionary with statistics
        """
        logger.info("Starting Document Cleaning (Blog 3)...")
        
        # Load parsed results from Blog 2
        try:
            parsed_file = Path(config.get("processed_dir")) / "parsed_documents" / "parsed_results.json"
            parsed_docs = self.json_store.load_list(str(parsed_file))
        except Exception as e:
            logger.error(f"Error loading parsed results: {e}")
            parsed_docs = []
        
        if not parsed_docs:
            logger.error("No parsed documents found. Run Blog 2 first.")
            return {"status": "error", "message": "No parsed documents"}
        
        logger.info(f"Loaded {len(parsed_docs)} parsed documents")
        
        # Clean all documents
        cleaned_docs = []
        stats = {
            "total": len(parsed_docs),
            "accepted": 0,
            "reviewed": 0,
            "rejected": 0,
            "by_format": {},
            "avg_original_length": 0,
            "avg_cleaned_length": 0,
            "avg_compression": 0,
        }
        
        total_original = 0
        total_cleaned = 0
        
        with self.tracker.track("clean_corpus"):
            for parsed_doc in tqdm(parsed_docs, desc="Cleaning documents"):
                if parsed_doc["status"] != "success":
                    logger.debug(f"Skipping {parsed_doc['doc_id']}: parsing status {parsed_doc['status']}")
                    continue
                
                doc_id = parsed_doc["doc_id"]
                text = parsed_doc["extracted_text"]
                format_type = parsed_doc["format_type"]
                
                # Clean the document
                result = self.clean_document(doc_id, text, format_type)
                cleaned_docs.append(result)
                
                # Update statistics
                format_type = parsed_doc["format_type"]
                if format_type not in stats["by_format"]:
                    stats["by_format"][format_type] = {
                        "total": 0,
                        "accepted": 0,
                        "reviewed": 0,
                        "rejected": 0
                    }
                
                stats["by_format"][format_type]["total"] += 1
                
                if result.final_status == "accept":
                    stats["accepted"] += 1
                    stats["by_format"][format_type]["accepted"] += 1
                elif result.final_status == "review":
                    stats["reviewed"] += 1
                    stats["by_format"][format_type]["reviewed"] += 1
                else:
                    stats["rejected"] += 1
                    stats["by_format"][format_type]["rejected"] += 1
                
                total_original += result.original_length
                total_cleaned += result.cleaned_length
        
        # Calculate averages
        if cleaned_docs:
            stats["avg_original_length"] = total_original / len(cleaned_docs)
            stats["avg_cleaned_length"] = total_cleaned / len(cleaned_docs)
            stats["avg_compression"] = stats["avg_cleaned_length"] / max(stats["avg_original_length"], 1)
        
        # Save results
        self._save_results(cleaned_docs, stats)
        
        logger.info(
            f"Cleaning complete: {stats['accepted']} accepted, "
            f"{stats['reviewed']} reviewed, {stats['rejected']} rejected"
        )
        
        return stats

    def _save_results(self, cleaned_docs: List[CleaningResults], stats: Dict):
        """
        Save cleaned documents to storage.
        
        Args:
            cleaned_docs: List of cleaning results
            stats: Statistics dictionary
        """
        # Create output directory
        output_dir = Path(config.get("processed_dir")) / "cleaned"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save cleaned results
        results_data = [asdict(doc) for doc in cleaned_docs]
        results_file = output_dir / "cleaning_results.json"
        self.json_store.save_list(results_data, str(results_file))
        logger.info(f"Saved cleaning results to {results_file}")
        
        # Save accepted documents only (stripped of metadata for size)
        accepted_docs = [
            {
                "doc_id": doc.doc_id,
                "cleaned_text": doc.cleaned_text,
                "compression_ratio": doc.metadata.get("compression_ratio", 0),
                "format_type": doc.metadata.get("format_type", "unknown"),
            }
            for doc in cleaned_docs if doc.final_status == "accept"
        ]
        
        accepted_file = output_dir / "accepted_documents.json"
        self.json_store.save_list(accepted_docs, str(accepted_file))
        logger.info(f"Saved {len(accepted_docs)} accepted documents to {accepted_file}")
        
        # Save statistics
        stats_file = output_dir / "cleaning_stats.json"
        self.json_store.save_single(stats, str(stats_file))
        logger.info(f"Saved statistics to {stats_file}")


def run_cleaning(sample_size: Optional[int] = None) -> Dict:
    """
    Run Blog 3 text cleaning on corpus.
    
    Args:
        sample_size: Optional limit for sample processing
        
    Returns:
        Summary dictionary
    """
    cleaner = TextCleaner()
    return cleaner.clean_corpus()
