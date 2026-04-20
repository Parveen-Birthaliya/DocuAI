"""
Blog 1: Corpus Audit & Quality Baselining

Implements:
- Format detection (PDF, HTML, JSON, CSV, TXT, Markdown, Python)
- Quality scoring (perplexity via GPT-2, language detection)
- Format-specific auditing (PDF layout, HTML content ratio)
- Routing table generation for Blog 2
"""

from .auditor import CorpusAuditor, run_audit
from .format_detector import FormatDetector, get_detector
from .quality_scorer import QualityScorer, get_scorer

__all__ = [
    "CorpusAuditor",
    "run_audit",
    "FormatDetector",
    "get_detector",
    "QualityScorer",
    "get_scorer",
]