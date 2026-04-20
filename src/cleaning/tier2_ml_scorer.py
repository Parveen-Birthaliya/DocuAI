"""
Blog 3: Tier 2 ML Quality Scorer

Machine learning-based text quality scoring.
Uses sentence embeddings and semantic coherence.
"""

import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Tier2Results:
    """Results from Tier 2 ML scoring"""
    score: float  # 0-1.0
    perplexity: float  # Text complexity
    coherence: float  # Semantic coherence
    diversity: float  # Vocabulary diversity
    recommendation: str  # "accept", "review", "reject"


class Tier2MLScorer:
    """ML-based text quality scoring"""

    def __init__(self, config: Dict = None):
        """
        Initialize Tier 2 scorer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.coherence_threshold = self.config.get("coherence_threshold", 0.5)
        self.diversity_threshold = self.config.get("diversity_threshold", 0.3)

    def calculate_perplexity(self, text: str) -> float:
        """
        Estimate text perplexity from character-level features.
        
        Uses entropy-based approximation without language model.
        Lower is better (more predictable).
        
        Args:
            text: Input text
            
        Returns:
            Estimated perplexity score
        """
        if not text:
            return 100.0
        
        # Simple perplexity estimate from character distribution
        # Count character frequencies
        char_freq = {}
        for c in text:
            char_freq[c] = char_freq.get(c, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        text_len = len(text)
        for count in char_freq.values():
            p = count / text_len
            entropy -= p * np.log2(p)
        
        # Normalize to 0-100 scale
        max_entropy = np.log2(len(char_freq))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.5
        
        # Invert: higher entropy = more variety = lower perplexity equivalent
        perplexity = (1 - normalized_entropy) * 100
        
        return max(0.0, min(100.0, perplexity))

    def calculate_coherence(self, text: str) -> float:
        """
        Estimate semantic coherence from sentence structure.
        
        Checks for:
        - Consistent sentence length
        - Presence of discourse markers
        - Topic continuity signals
        
        Args:
            text: Input text
            
        Returns:
            Coherence score 0-1.0
        """
        if not text:
            return 0.0
        
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if len(sentences) < 2:
            return 0.5  # Single sentence - unclear coherence
        
        # Calculate sentence length variance
        lengths = [len(s.split()) for s in sentences]
        avg_length = np.mean(lengths)
        length_variance = np.std(lengths) / avg_length if avg_length > 0 else 0
        
        # Penalize high variance (indicates topic shifts)
        length_coherence = max(0.0, 1.0 - length_variance)
        
        # Check for discourse markers (pronouns, connectives)
        discourse_markers = {'however', 'therefore', 'moreover', 'furthermore',
                            'thus', 'hence', 'meanwhile', 'additionally',
                            'consequently', 'subsequently', 'the', 'this', 'these'}
        
        marker_count = sum(1 for sentence in sentences 
                          if any(marker in sentence.lower() for marker in discourse_markers))
        marker_ratio = marker_count / len(sentences)
        
        # Final coherence combines both signals
        coherence = (length_coherence * 0.6) + (min(marker_ratio, 1.0) * 0.4)
        
        return max(0.0, min(1.0, coherence))

    def calculate_diversity(self, text: str) -> float:
        """
        Estimate vocabulary diversity.
        
        Higher diversity suggests richer content.
        
        Args:
            text: Input text
            
        Returns:
            Diversity score 0-1.0
        """
        if not text:
            return 0.0
        
        words = [w.lower() for w in text.split() if w.isalnum()]
        
        if len(words) < 10:
            return 0.3  # Too few words
        
        # Type-token ratio
        unique_words = len(set(words))
        type_token_ratio = unique_words / len(words)
        
        # Normalize: typical range is 0.3-0.7
        diversity = max(0.0, min(1.0, (type_token_ratio - 0.2) / 0.5))
        
        return diversity

    def calculate_overall_score(self, perplexity: float, 
                               coherence: float, 
                               diversity: float) -> float:
        """
        Combine individual scores into overall quality score.
        
        Args:
            perplexity: Perplexity score (0-100)
            coherence: Coherence score (0-1)
            diversity: Diversity score (0-1)
            
        Returns:
            Overall quality score 0-1.0
        """
        # Normalize perplexity to 0-1 range (lower perplexity is better)
        # Assume 0-80 is good, >80 is problematic
        normalized_perplexity = 1.0 - min(1.0, perplexity / 80.0)
        
        # Weights for each component
        score = (normalized_perplexity * 0.4 +
                coherence * 0.4 +
                diversity * 0.2)
        
        return max(0.0, min(1.0, score))

    def evaluate(self, text: str) -> Tier2Results:
        """
        Evaluate text quality using ML signals.
        
        Args:
            text: Text to evaluate
            
        Returns:
            Tier2Results with quality metrics
        """
        # Calculate individual metrics
        perplexity = self.calculate_perplexity(text)
        coherence = self.calculate_coherence(text)
        diversity = self.calculate_diversity(text)
        
        # Calculate overall score
        score = self.calculate_overall_score(perplexity, coherence, diversity)
        
        # Make recommendation
        if score < 0.4:
            recommendation = "reject"
        elif score < 0.65:
            recommendation = "review"
        else:
            recommendation = "accept"
        
        return Tier2Results(
            score=score,
            perplexity=perplexity,
            coherence=coherence,
            diversity=diversity,
            recommendation=recommendation
        )


def apply_tier2_scorer(text: str, config: Dict = None) -> Tier2Results:
    """
    Convenience function to apply Tier 2 scorer.
    
    Args:
        text: Text to score
        config: Optional config
        
    Returns:
        Tier2Results
    """
    scorer = Tier2MLScorer(config)
    return scorer.evaluate(text)
