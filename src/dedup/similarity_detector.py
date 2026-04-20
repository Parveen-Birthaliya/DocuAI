"""
Blog 5: Similarity Detection

Detect similar and duplicate documents using multiple similarity metrics.
"""

import logging
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
import hashlib
import re

logger = logging.getLogger(__name__)


@dataclass
class SimilarityScore:
    """Similarity between two documents"""
    doc1_id: str
    doc2_id: str
    text_hash_match: bool
    content_hash_match: bool
    cosine_similarity: float
    jaccard_similarity: float
    levenshtein_ratio: float
    overall_similarity: float  # Weighted average
    is_duplicate: bool


class SimilarityDetector:
    """Detect similarity between documents"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.hash_threshold = self.config.get("hash_threshold", 0.95)
        self.cosine_threshold = self.config.get("cosine_threshold", 0.85)
        self.jaccard_threshold = self.config.get("jaccard_threshold", 0.80)
        self.overall_threshold = self.config.get("overall_threshold", 0.85)

    def compute_text_hash(self, text: str) -> str:
        """Compute SHA256 hash of full text"""
        return hashlib.sha256(text.encode()).hexdigest()

    def compute_content_hash(self, text: str) -> str:
        """Compute hash of normalized content (order-independent)"""
        # Normalize: lowercase, remove punctuation, split into words
        words = re.findall(r'\w+', text.lower())
        # Sort for order-independence
        words.sort()
        normalized = ' '.join(words)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def compute_cosine_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        Uses word frequencies as vectors.
        """
        def get_word_vector(text: str) -> Dict[str, int]:
            words = re.findall(r'\w+', text.lower())
            vector = {}
            for word in words:
                vector[word] = vector.get(word, 0) + 1
            return vector
        
        vec1 = get_word_vector(text1)
        vec2 = get_word_vector(text2)
        
        # Compute dot product
        common_words = set(vec1.keys()) & set(vec2.keys())
        dot_product = sum(vec1[w] * vec2[w] for w in common_words)
        
        # Compute magnitudes
        mag1 = sum(v**2 for v in vec1.values()) ** 0.5
        mag2 = sum(v**2 for v in vec2.values()) ** 0.5
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        cosine = dot_product / (mag1 * mag2)
        return max(0.0, min(1.0, cosine))

    def compute_jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        Compute Jaccard similarity (set intersection over union).
        """
        def get_word_set(text: str) -> set:
            words = re.findall(r'\w+', text.lower())
            return set(words)
        
        set1 = get_word_set(text1)
        set2 = get_word_set(text2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        return intersection / union

    def compute_levenshtein_ratio(self, text1: str, text2: str) -> float:
        """
        Compute Levenshtein distance ratio (normalized).
        Lower distance = higher similarity.
        """
        # Use simplified version (only check length ratio)
        # Full Levenshtein is O(n*m) which is expensive for documents
        
        len1 = len(text1)
        len2 = len(text2)
        
        if len1 == 0 and len2 == 0:
            return 1.0
        
        max_len = max(len1, len2)
        len_diff = abs(len1 - len2)
        
        # Length-based similarity
        length_ratio = 1.0 - (len_diff / max_len)
        
        # Check substring match for a quick estimate
        if len1 > len2:
            text1, text2 = text2, text1
        
        # Check if shorter text appears in longer text
        if text1 in text2:
            return 0.95
        
        return length_ratio

    def detect_similarity(self, doc1_id: str, text1: str,
                         doc2_id: str, text2: str) -> SimilarityScore:
        """
        Compute similarity between two documents.
        
        Args:
            doc1_id: First document ID
            text1: First document text
            doc2_id: Second document ID
            text2: Second document text
            
        Returns:
            SimilarityScore
        """
        # Compute hashes
        text_hash_match = self.compute_text_hash(text1) == self.compute_text_hash(text2)
        content_hash_match = self.compute_content_hash(text1) == self.compute_content_hash(text2)
        
        # Compute similarity metrics
        cosine = self.compute_cosine_similarity(text1, text2)
        jaccard = self.compute_jaccard_similarity(text1, text2)
        levenshtein = self.compute_levenshtein_ratio(text1, text2)
        
        # Weighted overall similarity
        overall = (cosine * 0.4 + jaccard * 0.35 + levenshtein * 0.25)
        
        # Decide if duplicate
        is_duplicate = (text_hash_match or 
                       content_hash_match or 
                       overall >= self.overall_threshold)
        
        return SimilarityScore(
            doc1_id=doc1_id,
            doc2_id=doc2_id,
            text_hash_match=text_hash_match,
            content_hash_match=content_hash_match,
            cosine_similarity=cosine,
            jaccard_similarity=jaccard,
            levenshtein_ratio=levenshtein,
            overall_similarity=overall,
            is_duplicate=is_duplicate
        )


def detect_similarity(doc1_id: str, text1: str, 
                     doc2_id: str, text2: str,
                     config: Dict = None) -> SimilarityScore:
    """Detect similarity between documents"""
    detector = SimilarityDetector(config)
    return detector.detect_similarity(doc1_id, text1, doc2_id, text2)
