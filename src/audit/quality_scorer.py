"""
Quality scoring for documents.
Scores: perplexity (GPT-2, NO kenlm!), language detection, encoding.
"""

import torch
import numpy as np
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from src.utils import logger


class QualityScorer:
    """Score document quality using multiple signals."""
    
    def __init__(self):
        """Initialize scorer with GPT-2 model for perplexity."""
        try:
            from transformers import GPT2Tokenizer, GPT2LMHeadModel
            
            self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            self.model = GPT2LMHeadModel.from_pretrained("gpt2")
            self.model.eval()
            
            # Use CPU
            self.device = torch.device("cpu")
            self.model.to(self.device)
            
            self.has_gpt2 = True
            logger.info("GPT-2 model loaded for perplexity scoring (NO kenlm!)")
        
        except Exception as e:
            logger.warning(f"GPT-2 initialization failed: {e}, perplexity disabled")
            self.has_gpt2 = False
    
    def compute_perplexity(self, text: str, max_length: int = 512) -> Optional[float]:
        """
        Compute perplexity using GPT-2.
        
        Lower perplexity = higher quality text (more linguistically coherent)
        
        Args:
            text: Input text
            max_length: Max tokens to process
        
        Returns:
            Perplexity score or None if GPT-2 unavailable
        """
        if not self.has_gpt2:
            return None
        
        if not text or len(text.strip()) < 10:
            return None
        
        try:
            # Tokenize
            encodings = self.tokenizer(
                text,
                truncation=True,
                max_length=max_length,
                return_tensors="pt"
            )
            
            input_ids = encodings["input_ids"].to(self.device)
            
            if input_ids.shape[1] < 2:
                return None
            
            # Compute loss
            with torch.no_grad():
                outputs = self.model(input_ids, labels=input_ids)
                loss = outputs.loss
            
            # Perplexity = exp(loss)
            perplexity = float(torch.exp(loss).item())
            
            # Cap at reasonable maximum (avoid numerical issues)
            perplexity = min(perplexity, 10000.0)
            
            logger.debug(f"Perplexity computed: {perplexity:.2f}")
            return round(perplexity, 2)
        
        except Exception as e:
            logger.debug(f"Perplexity computation failed: {e}")
            return None
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language using FastText or langdetect.
        
        Args:
            text: Input text
        
        Returns:
            (language_code, confidence) - e.g., ("en", 0.95)
        """
        if not text or len(text.strip()) < 10:
            return ("unknown", 0.0)
        
        # Try langdetect first (simpler, no model download)
        try:
            from langdetect import detect, detect_langs, LangDetectException
            
            results = detect_langs(text)
            if results:
                best = results[0]
                lang_code = best.lang
                confidence = best.prob
                
                logger.debug(f"Language detected: {lang_code} ({confidence:.2f})")
                return (lang_code, round(confidence, 2))
        
        except Exception as e:
            logger.debug(f"langdetect failed: {e}")
        
        # Fallback: check for common patterns
        text_lower = text.lower()
        
        # Simple heuristics (not accurate, but better than nothing)
        if any(word in text_lower for word in ["the", "and", "is", "to", "of"]):
            return ("en", 0.5)  # Probably English
        elif any(word in text_lower for word in ["le", "de", "et", "la"]):
            return ("fr", 0.5)  # Probably French
        elif any(word in text_lower for word in ["der", "und", "das", "die"]):
            return ("de", 0.5)  # Probably German
        
        return ("unknown", 0.3)
    
    def score_quality(
        self,
        text: str,
        language: Optional[str] = None,
        language_confidence: Optional[float] = None,
    ) -> float:
        """
        Combine signals into 0-1.0 quality score.
        
        Signals:
        - Word count (50-100k is good range)
        - Mean word length (3-10 chars is good)
        - Perplexity (lower is better, inverted to 0-1)
        - Language confidence (0-1)
        
        Args:
            text: Input text
            language: Language code (optional)
            language_confidence: Language confidence (optional)
        
        Returns:
            Quality score 0.0-1.0
        """
        if not text or len(text.strip()) < 50:
            return 0.0
        
        scores = []
        
        # Signal 1: Word count (optimal: 50-100k words)
        words = text.split()
        word_count = len(words)
        
        if 50 <= word_count <= 100_000:
            word_score = 1.0
        elif word_count < 50:
            word_score = max(0.0, word_count / 50)
        else:
            word_score = max(0.0, 1.0 - (word_count - 100_000) / 100_000)
        
        scores.append(word_score)
        logger.debug(f"Word count score: {word_score:.2f} (words={word_count})")
        
        # Signal 2: Mean word length (optimal: 3-10 chars)
        if words:
            mean_word_len = np.mean([len(w) for w in words])
            
            if 3 <= mean_word_len <= 10:
                len_score = 1.0
            elif mean_word_len < 3:
                len_score = max(0.0, mean_word_len / 3)
            else:
                len_score = max(0.0, 1.0 - (mean_word_len - 10) / 10)
            
            scores.append(len_score)
            logger.debug(f"Mean word length score: {len_score:.2f} (len={mean_word_len:.1f})")
        
        # Signal 3: Perplexity (lower is better)
        perplexity = self.compute_perplexity(text[:5000])  # Sample first 5k chars
        
        if perplexity is not None:
            # Normalize: <50 perplexity = 1.0, >300 perplexity = 0.0
            perp_score = max(0.0, 1.0 - (perplexity - 50) / 250)
            scores.append(perp_score)
            logger.debug(f"Perplexity score: {perp_score:.2f} (perplexity={perplexity:.1f})")
        
        # Signal 4: Language confidence
        if language_confidence is not None:
            scores.append(language_confidence)
            logger.debug(f"Language confidence score: {language_confidence:.2f}")
        
        # Combine: average all signals
        quality_score = float(np.mean(scores)) if scores else 0.5
        
        logger.debug(f"Overall quality score: {quality_score:.2f}")
        return round(quality_score, 3)
    
    def score_document(self, text: str) -> Dict[str, Any]:
        """
        Score complete document including all signals.
        
        Returns:
            {
                "perplexity": float,
                "language": str,
                "language_confidence": float,
                "char_count": int,
                "word_count": int,
                "quality_score": float (0-1)
            }
        """
        if not text:
            return {
                "perplexity": None,
                "language": "unknown",
                "language_confidence": 0.0,
                "char_count": 0,
                "word_count": 0,
                "quality_score": 0.0,
            }
        
        # Language detection
        language, lang_conf = self.detect_language(text)
        
        # Compute perplexity
        perplexity = self.compute_perplexity(text)
        
        # Quality score
        quality_score = self.score_quality(text, language, lang_conf)
        
        return {
            "perplexity": perplexity,
            "language": language,
            "language_confidence": lang_conf,
            "char_count": len(text),
            "word_count": len(text.split()),
            "quality_score": quality_score,
        }


# Global instance
_scorer: Optional[QualityScorer] = None


def get_scorer() -> QualityScorer:
    """Get singleton quality scorer."""
    global _scorer
    if _scorer is None:
        _scorer = QualityScorer()
    return _scorer
