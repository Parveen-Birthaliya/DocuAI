"""Blog 5: Deduplication, Validation & Feedback"""

from .similarity_detector import SimilarityDetector, SimilarityScore
from .deduplicator import Deduplicator, DeduplicationResult
from .merge_knowledge import KnowledgeMerger, MergedKnowledge, merge_duplicates
from .validator import CorpusValidator, ValidationReport, validate_corpus
from .orchestrator import Blog5Orchestrator, Blog5Results, run_blog5

__all__ = [
    "SimilarityDetector",
    "SimilarityScore",
    "Deduplicator",
    "DeduplicationResult",
    "KnowledgeMerger",
    "MergedKnowledge",
    "merge_duplicates",
    "CorpusValidator",
    "ValidationReport",
    "validate_corpus",
    "Blog5Orchestrator",
    "Blog5Results",
    "run_blog5",
]
