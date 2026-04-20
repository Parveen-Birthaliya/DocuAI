"""
Blog 3: Boilerplate Detection

Identifies and flags common boilerplate patterns:
- Navigation menus, headers, footers
- Copyright statements, legal text
- Repeated content blocks
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class BoilerplateAnalysis:
    """Results from boilerplate detection"""
    is_boilerplate: bool
    boilerplate_ratio: float  # 0-1.0
    detected_types: List[str]  # Types of boilerplate found
    scores: Dict[str, float]  # Scores for each detector
    cleaned_text: str  # Text with boilerplate removed
    removal_confidence: float  # Confidence in removal


class BoilerplateDetector:
    """Detect and remove boilerplate content"""

    def __init__(self, config: Dict = None):
        """Initialize boilerplate detector"""
        self.config = config or {}
        self.copyright_threshold = self.config.get("copyright_threshold", 0.85)
        self.navigation_threshold = self.config.get("navigation_threshold", 0.7)

    def detect_navigation_menu(self, text: str) -> Tuple[float, List[str]]:
        """
        Detect navigation menu patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (score, matched lines)
        """
        nav_patterns = [
            r'^\s*(home|about|contact|products|services|blog|news)\s*$',
            r'^\s*(sign in|login|register|signup)\s*$',
            r'^\s*(menu|navigation|main|top)\s*$',
            r'^\s*[|•·]?\s*(home|about|contact).*(home|about|contact)',  # Horizontal menu
        ]
        
        lines = text.split('\n')
        matched_lines = []
        
        for line in lines[:30]:  # Check first 30 lines
            for pattern in nav_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    matched_lines.append(line.strip())
        
        # Calculate score
        if matched_lines:
            nav_ratio = len(matched_lines) / max(len(lines), 1)
            score = min(1.0, len(matched_lines) * 0.2)  # Each nav item increases score
        else:
            score = 0.0
        
        return score, matched_lines

    def detect_footer(self, text: str) -> Tuple[float, List[str]]:
        """
        Detect footer patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (score, matched lines)
        """
        footer_patterns = [
            r'©|copyright|®|™',
            r'all rights reserved',
            r'privacy policy|terms of service|terms & conditions',
            r'contact us|company|address|phone',
            r'\d{4}\s*(©|\(c\))',  # Year with copyright
            r'follow us on|follow @|social media',
        ]
        
        lines = text.split('\n')
        matched_lines = []
        
        # Check last lines for footer
        for line in lines[-20:]:
            for pattern in footer_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    matched_lines.append(line.strip())
        
        score = min(1.0, len(matched_lines) * 0.25)
        return score, matched_lines

    def detect_copyright_text(self, text: str) -> Tuple[float, str]:
        """
        Detect copyright and legal boilerplate.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (score, matched text)
        """
        # Copyright pattern
        copyright_pattern = r'©.*?(?:\d{4}|all rights|reserved).*?(?:\.|$)'
        matches = re.findall(copyright_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if matches:
            matched_text = ' '.join(matches)
            # Shorter copyright statements are more common
            score = min(1.0, len(matches) * 0.3)
            return score, matched_text
        
        return 0.0, ""

    def detect_repeated_blocks(self, text: str, min_length: int = 50) -> Tuple[float, List[str]]:
        """
        Detect repeated text blocks (common in boilerplate).
        
        Args:
            text: Text to analyze
            min_length: Minimum block length
            
        Returns:
            Tuple of (score, repeated blocks)
        """
        lines = text.split('\n')
        
        # Look for repeated sequences
        repeated = []
        seen = {}
        
        for line in lines:
            if len(line) >= min_length:
                # Check if we've seen similar lines
                line_words = set(line.split())
                for seen_line in seen:
                    seen_words = set(seen_line.split())
                    # Calculate Jaccard similarity
                    intersection = len(line_words & seen_words)
                    union = len(line_words | seen_words)
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity > 0.7:  # 70% similar
                        repeated.append(line[:100])  # Store first 100 chars
                        break
            
            seen[line] = seen.get(line, 0) + 1
        
        score = min(1.0, len(repeated) * 0.1)
        return score, repeated[:10]  # Return top 10

    def detect_link_heavy_text(self, text: str) -> Tuple[float, Dict]:
        """
        Detect text that's mostly links (likely navigation/menu).
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (score, analysis dict)
        """
        lines = text.split('\n')
        
        # Patterns that suggest links/menu
        url_pattern = r'https?://|www\.|/[a-z]+'
        menu_pattern = r'^\s*[•·|→]\s*'
        bracket_pattern = r'^\s*\[.*?\]\s*$'
        
        link_lines = 0
        for line in lines:
            if re.search(url_pattern, line) or re.match(menu_pattern, line) or re.match(bracket_pattern, line):
                link_lines += 1
        
        link_ratio = link_lines / max(len(lines), 1)
        score = 1.0 if link_ratio > 0.5 else 0.0
        
        return score, {"link_ratio": link_ratio, "link_lines": link_lines}

    def clean_boilerplate(self, text: str) -> str:
        """
        Remove detected boilerplate patterns.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        nav_patterns = [
            r'^\s*(home|about|contact|products|services|blog|news)\s*$',
            r'^\s*(sign in|login|register|signup)\s*$',
        ]
        
        footer_patterns = [
            r'©|copyright|®|™',
            r'all rights reserved',
            r'privacy policy|terms of service|terms & conditions',
        ]
        
        for line in lines:
            # Skip navigation lines
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in nav_patterns):
                continue
            
            # Skip footer lines
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in footer_patterns):
                continue
            
            # Keep other lines
            if line.strip():
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def analyze(self, text: str) -> BoilerplateAnalysis:
        """
        Analyze text for boilerplate content.
        
        Args:
            text: Text to analyze
            
        Returns:
            BoilerplateAnalysis with detailed results
        """
        scores = {}
        detected_types = []
        
        # Run all detectors
        nav_score, nav_lines = self.detect_navigation_menu(text)
        scores["navigation"] = nav_score
        if nav_score > 0.3:
            detected_types.append("navigation")
        
        footer_score, footer_lines = self.detect_footer(text)
        scores["footer"] = footer_score
        if footer_score > 0.3:
            detected_types.append("footer")
        
        copyright_score, copyright_text = self.detect_copyright_text(text)
        scores["copyright"] = copyright_score
        if copyright_score > 0.1:
            detected_types.append("copyright")
        
        repeat_score, repeated_blocks = self.detect_repeated_blocks(text)
        scores["repeated"] = repeat_score
        if repeat_score > 0.2:
            detected_types.append("repeated_blocks")
        
        link_score, link_analysis = self.detect_link_heavy_text(text)
        scores["link_heavy"] = link_score
        if link_score > 0.5:
            detected_types.append("link_heavy")
        
        # Calculate overall boilerplate ratio
        boilerplate_ratio = sum(scores.values()) / len(scores)
        is_boilerplate = boilerplate_ratio > 0.4
        
        # Clean text
        cleaned_text = self.clean_boilerplate(text) if is_boilerplate else text
        removal_confidence = boilerplate_ratio
        
        return BoilerplateAnalysis(
            is_boilerplate=is_boilerplate,
            boilerplate_ratio=boilerplate_ratio,
            detected_types=detected_types,
            scores=scores,
            cleaned_text=cleaned_text,
            removal_confidence=removal_confidence
        )


def detect_boilerplate(text: str, config: Dict = None) -> BoilerplateAnalysis:
    """
    Convenience function to detect boilerplate.
    
    Args:
        text: Text to analyze
        config: Optional config
        
    Returns:
        BoilerplateAnalysis
    """
    detector = BoilerplateDetector(config)
    return detector.analyze(text)
