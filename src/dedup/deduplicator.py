"""
Blog 5: Deduplication and Conflict Resolution

Identify and handle duplicate documents.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

from .similarity_detector import SimilarityDetector, SimilarityScore

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationResult:
    """Result of deduplication process"""
    original_count: int
    unique_count: int
    duplicate_groups: List[List[str]]  # Groups of duplicate doc IDs
    removed_docs: List[str]  # Removed duplicate IDs
    stats: Dict


class Deduplicator:
    """Identify and remove duplicate documents"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.similarity_detector = SimilarityDetector(config)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.85)

    def find_duplicates(self, documents: Dict[str, str]) -> List[List[str]]:
        """
        Find groups of duplicate documents.
        
        Args:
            documents: Dict mapping doc_id -> text
            
        Returns:
            List of duplicate groups (each group is list of doc IDs)
        """
        doc_ids = list(documents.keys())
        n_docs = len(doc_ids)
        
        # Track which documents are duplicates of which
        groups = []
        processed = set()
        
        for i, doc_id1 in enumerate(doc_ids):
            if doc_id1 in processed:
                continue
            
            group = [doc_id1]
            text1 = documents[doc_id1]
            
            for j in range(i + 1, n_docs):
                doc_id2 = doc_ids[j]
                if doc_id2 in processed:
                    continue
                
                text2 = documents[doc_id2]
                
                # Check similarity
                similarity = self.similarity_detector.detect_similarity(
                    doc_id1, text1, doc_id2, text2
                )
                
                if similarity.is_duplicate:
                    group.append(doc_id2)
                    processed.add(doc_id2)
            
            if len(group) > 1:
                groups.append(group)
                processed.update(group)
        
        return groups

    def _select_canonical(self, doc_ids: List[str], 
                         documents: Dict[str, str]) -> str:
        """
        Select the canonical (representative) document from a group.
        
        Heuristics:
        - Longest text (more complete)
        - Earliest in alphabetical order (deterministic)
        
        Args:
            doc_ids: List of duplicate doc IDs
            documents: Dict mapping doc_id -> text
            
        Returns:
            The canonical doc_id to keep
        """
        # First, find the longest document (most complete)
        longest_id = max(doc_ids, key=lambda d: len(documents[d]))
        
        # As tiebreaker, use alphabetical order
        if longest_id:
            return longest_id
        
        return sorted(doc_ids)[0]

    def deduplicate(self, documents: Dict[str, str]) -> DeduplicationResult:
        """
        Remove duplicate documents, keeping canonical versions.
        
        Args:
            documents: Dict mapping doc_id -> text
            
        Returns:
            DeduplicationResult
        """
        original_count = len(documents)
        
        # Find duplicate groups
        duplicate_groups = self.find_duplicates(documents)
        
        # Select canonical documents to remove
        removed_docs = []
        for group in duplicate_groups:
            canonical = self._select_canonical(group, documents)
            
            # Mark others for removal
            for doc_id in group:
                if doc_id != canonical:
                    removed_docs.append(doc_id)
        
        unique_count = original_count - len(removed_docs)
        
        # Compute statistics
        stats = {
            "duplicate_groups_found": len(duplicate_groups),
            "total_duplicates_detected": sum(len(g) - 1 for g in duplicate_groups),
            "removal_rate": len(removed_docs) / original_count if original_count > 0 else 0,
        }
        
        return DeduplicationResult(
            original_count=original_count,
            unique_count=unique_count,
            duplicate_groups=duplicate_groups,
            removed_docs=removed_docs,
            stats=stats
        )


def deduplicate_documents(documents: Dict[str, str],
                         config: Dict = None) -> DeduplicationResult:
    """
    Deduplicate documents.
    
    Args:
        documents: Dict mapping doc_id -> text
        config: Optional config
        
    Returns:
        DeduplicationResult
    """
    deduplicator = Deduplicator(config)
    return deduplicator.deduplicate(documents)
