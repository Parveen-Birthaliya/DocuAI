"""
Blog 3: Text Cleaning & Noise Elimination

Implements 3-tier quality gating:
1. Tier 1: Heuristic filters (length, encoding, character distribution)
2. Tier 2: ML quality scoring (perplexity, coherence, diversity)
3. Boilerplate detection and format-specific cleaning
"""

from .cleaner import TextCleaner, run_cleaning, CleaningResults
from .tier1_heuristics import Tier1HeuristicFilter, apply_tier1_filter, Tier1Results
from .tier2_ml_scorer import Tier2MLScorer, apply_tier2_scorer, Tier2Results
from .boilerplate_detector import BoilerplateDetector, detect_boilerplate, BoilerplateAnalysis
from .format_cleaners import FormatCleaner, NoiseCleaner, clean_text

__all__ = [
    # Main orchestrator
    "TextCleaner",
    "run_cleaning",
    "CleaningResults",
    
    # Tier 1 heuristics
    "Tier1HeuristicFilter",
    "apply_tier1_filter",
    "Tier1Results",
    
    # Tier 2 ML scoring
    "Tier2MLScorer",
    "apply_tier2_scorer",
    "Tier2Results",
    
    # Boilerplate detection
    "BoilerplateDetector",
    "detect_boilerplate",
    "BoilerplateAnalysis",
    
    # Format-specific cleaning
    "FormatCleaner",
    "NoiseCleaner",
    "clean_text",
]