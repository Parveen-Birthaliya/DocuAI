"""
Blog 3: Tier 1 Heuristic Filters

Basic text quality checks using simple rules.
Fast, deterministic, no ML required.
"""

import logging
import re
from typing import Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Tier1Results:
    """Results from Tier 1 heuristic filtering"""
    passed: bool
    scores: Dict[str, float]  # Individual scores 0-1.0
    failures: list  # Why it failed
    recommendation: str  # "accept", "review", "reject"


class Tier1HeuristicFilter:
    """Apply basic heuristic quality checks"""

    def __init__(self, config: Dict = None):
        """
        Initialize Tier 1 filter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Quality thresholds
        self.min_length = self.config.get("min_length", 100)
        self.max_length = self.config.get("max_length", 1000000)
        self.min_word_count = self.config.get("min_word_count", 20)
        self.max_word_count = self.config.get("max_word_count", 200000)
        self.min_unicode_ratio = self.config.get("min_unicode_ratio", 0.8)
        self.max_control_ratio = self.config.get("max_control_ratio", 0.1)
        self.max_number_ratio = self.config.get("max_number_ratio", 0.5)
        self.max_special_ratio = self.config.get("max_special_ratio", 0.2)

    def check_length(self, text: str) -> Tuple[float, str]:
        """Check text length is within reasonable bounds"""
        length = len(text)
        
        if length < self.min_length:
            return 0.0, f"Too short: {length} < {self.min_length}"
        elif length > self.max_length:
            return 0.3, f"Too long: {length} > {self.max_length}"
        else:
            return 1.0, "Length OK"

    def check_word_count(self, text: str) -> Tuple[float, str]:
        """Check word count is reasonable"""
        words = len(text.split())
        
        if words < self.min_word_count:
            return 0.0, f"Too few words: {words} < {self.min_word_count}"
        elif words > self.max_word_count:
            return 0.3, f"Too many words: {words} > {self.max_word_count}"
        else:
            return 1.0, "Word count OK"

    def check_character_distribution(self, text: str) -> Tuple[float, str]:
        """Check for reasonable character distribution"""
        if not text:
            return 0.0, "Empty text"
        
        # Count character types
        ascii_count = sum(1 for c in text if ord(c) < 128)
        unicode_count = sum(1 for c in text if ord(c) >= 128)
        control_count = sum(1 for c in text if ord(c) < 32 and c not in '\n\t\r')
        
        # Calculate ratios
        total = len(text)
        unicode_ratio = ascii_count / total if total > 0 else 0
        control_ratio = control_count / total if total > 0 else 0
        
        issues = []
        score = 1.0
        
        if unicode_ratio < self.min_unicode_ratio:
            issues.append(f"Low ASCII: {unicode_ratio:.2f}")
            score -= 0.2
        
        if control_ratio > self.max_control_ratio:
            issues.append(f"High control chars: {control_ratio:.2f}")
            score -= 0.3
        
        reason = ", ".join(issues) if issues else "Character distribution OK"
        return max(0.0, score), reason

    def check_number_ratio(self, text: str) -> Tuple[float, str]:
        """Check text isn't mostly numbers (likely a table/data dump)"""
        if not text:
            return 0.0, "Empty text"
        
        digit_count = sum(1 for c in text if c.isdigit())
        digit_ratio = digit_count / len(text)
        
        if digit_ratio > self.max_number_ratio:
            return 0.3, f"Too many numbers: {digit_ratio:.2f}"
        else:
            return 1.0, "Number ratio OK"

    def check_whitespace_distribution(self, text: str) -> Tuple[float, str]:
        """Check for pathological whitespace patterns"""
        lines = text.split('\n')
        
        # Check for crazy line counts (likely list dump)
        if len(lines) > 10000:
            return 0.2, f"Too many short lines: {len(lines)}"
        
        # Check average line length
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        
        if avg_line_length < 5:
            return 0.2, f"Too short avg line: {avg_line_length:.1f}"
        elif avg_line_length > 500:
            return 0.8, f"Very long avg line: {avg_line_length:.1f}"
        
        return 1.0, "Whitespace distribution OK"

    def check_language_signals(self, text: str) -> Tuple[float, str]:
        """Check for language patterns"""
        if not text:
            return 0.0, "Empty text"
        
        # Check for common English patterns
        words = text.split()
        
        # Common English words
        common_words = {'the', 'a', 'and', 'to', 'of', 'in', 'is', 'it', 'for', 'that'}
        found_common = sum(1 for w in words[:100] if w.lower() in common_words)
        
        # Check for repeated sequences (likely gibberish)
        repeats = len(re.findall(r'(.)\1{4,}', text))  # 5+ repeated chars
        
        issues = []
        score = 1.0
        
        if found_common < 2 and len(words) > 50:
            issues.append("Few common words")
            score -= 0.1
        
        if repeats > 5:
            issues.append(f"High repetition: {repeats}")
            score -= 0.2
        
        reason = ", ".join(issues) if issues else "Language signals OK"
        return max(0.0, score), reason

    def check_encoding_quality(self, text: str) -> Tuple[float, str]:
        """Check for encoding issues"""
        # Look for common encoding corruption patterns
        bad_patterns = [
            r'[^\x20-\x7E\n\t\r]',  # Non-printable ASCII
            r'â€™',  # Curly quote encoding error
            r'â€œ',  # Quote encoding error
            r'Â\xa0',  # Non-breaking space corruption
        ]
        
        issues_found = 0
        for pattern in bad_patterns:
            issues_found += len(re.findall(pattern, text))
        
        if issues_found > 10:
            return 0.5, f"Encoding issues: {issues_found}"
        elif issues_found > 0:
            return 0.8, f"Minor encoding issues: {issues_found}"
        else:
            return 1.0, "Encoding quality OK"

    def evaluate(self, text: str) -> Tier1Results:
        """
        Evaluate text against all Tier 1 heuristics.
        
        Args:
            text: Text to evaluate
            
        Returns:
            Tier1Results with pass/fail and detailed scores
        """
        scores = {}
        reasons = []
        
        # Run all checks
        checks = [
            ("length", self.check_length),
            ("word_count", self.check_word_count),
            ("character_dist", self.check_character_distribution),
            ("number_ratio", self.check_number_ratio),
            ("whitespace", self.check_whitespace_distribution),
            ("language", self.check_language_signals),
            ("encoding", self.check_encoding_quality),
        ]
        
        for name, check_fn in checks:
            score, reason = check_fn(text)
            scores[name] = score
            if score < 0.5:
                reasons.append(f"{name}: {reason}")
        
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores)
        
        # Decision logic
        if scores["length"] < 0.5 or scores["word_count"] < 0.5:
            passed = False
            recommendation = "reject"
        elif overall_score < 0.4:
            passed = False
            recommendation = "reject"
        elif overall_score < 0.7:
            passed = True
            recommendation = "review"
        else:
            passed = True
            recommendation = "accept"
        
        return Tier1Results(
            passed=passed,
            scores=scores,
            failures=reasons,
            recommendation=recommendation
        )


def apply_tier1_filter(text: str, config: Dict = None) -> Tier1Results:
    """
    Convenience function to apply Tier 1 filter.
    
    Args:
        text: Text to filter
        config: Optional config
        
    Returns:
        Tier1Results
    """
    filter_obj = Tier1HeuristicFilter(config)
    return filter_obj.evaluate(text)
