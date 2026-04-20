"""
Blog 5: Validation and Consistency Checks

Validate corpus consistency and integrity.
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Validation report for corpus"""
    total_docs: int
    passed: int
    failed: int
    warnings: int
    issues: List[Dict]  # List of issues found
    consistency_score: float  # 0-1.0


class CorpusValidator:
    """Validate corpus consistency"""

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def validate_document(self, doc_id: str, text: str,
                         metadata: Dict) -> Tuple[bool, List[str]]:
        """
        Validate single document.
        
        Args:
            doc_id: Document ID
            text: Document text
            metadata: Document metadata
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check text is not empty
        if not text or len(text.strip()) == 0:
            issues.append("Empty text")
        
        # Check metadata has required fields
        if metadata:
            if not metadata.get("title"):
                issues.append("Missing title")
            if not metadata.get("language"):
                issues.append("Missing language")
        
        # Check for encoding issues
        try:
            text.encode('utf-8')
        except UnicodeEncodeError:
            issues.append("Encoding error")
        
        # Check text length reasonable
        if text and len(text) > 10000000:
            issues.append("Text too long (>10MB)")
        
        is_valid = len(issues) == 0
        return is_valid, issues

    def check_language_consistency(self, documents: Dict[str, Dict]) -> List[str]:
        """
        Check if corpus has consistent language.
        
        Args:
            documents: Dict mapping doc_id -> {text, metadata}
            
        Returns:
            List of language mismatches
        """
        languages = {}
        mismatches = []
        
        for doc_id, doc in documents.items():
            metadata = doc.get("metadata", {})
            language = metadata.get("language", "unknown")
            
            languages[language] = languages.get(language, 0) + 1
        
        # Check for plurality of languages
        if len(languages) > 1:
            for lang, count in languages.items():
                if count < len(documents) * 0.1:  # Less than 10%
                    mismatches.append(f"Language {lang} only in {count} docs")
        
        return mismatches

    def check_metadata_consistency(self, documents: Dict[str, Dict]) -> List[str]:
        """
        Check if metadata is consistent across corpus.
        
        Args:
            documents: Dict mapping doc_id -> {text, metadata}
            
        Returns:
            List of consistency issues
        """
        issues = []
        
        # Check if all docs have metadata
        missing_metadata = []
        for doc_id, doc in documents.items():
            if not doc.get("metadata"):
                missing_metadata.append(doc_id)
        
        if missing_metadata:
            issues.append(f"{len(missing_metadata)} docs missing metadata")
        
        return issues

    def check_format_consistency(self, documents: Dict[str, Dict],
                                formats: Dict[str, int]) -> List[str]:
        """
        Check if format distribution is reasonable.
        
        Args:
            documents: Dict mapping doc_id -> doc data
            formats: Dict mapping format -> count
            
        Returns:
            List of format issues
        """
        issues = []
        total = sum(formats.values())
        
        # Check for unexpected format distributions
        for fmt, count in formats.items():
            ratio = count / total if total > 0 else 0
            
            # Flag if a format is >90% of corpus (unusual)
            if ratio > 0.9:
                issues.append(f"Format {fmt} dominates corpus ({ratio*100:.1f}%)")
            
            # Flag if a format is <1% of corpus (possibly error)
            if ratio < 0.01:
                issues.append(f"Format {fmt} is very rare ({ratio*100:.2f}%)")
        
        return issues

    def validate_corpus(self, documents: Dict[str, Dict],
                       formats: Dict[str, int]) -> ValidationReport:
        """
        Validate entire corpus.
        
        Args:
            documents: Dict mapping doc_id -> {text, metadata}
            formats: Dict mapping format -> count
            
        Returns:
            ValidationReport
        """
        issues = []
        passed = 0
        failed = 0
        warnings = 0
        
        # Validate each document
        for doc_id, doc in documents.items():
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            is_valid, doc_issues = self.validate_document(doc_id, text, metadata)
            
            if is_valid:
                passed += 1
            else:
                failed += 1
                for issue in doc_issues:
                    issues.append({
                        "doc_id": doc_id,
                        "issue": issue,
                        "severity": "error"
                    })
        
        # Check corpus-level consistency
        language_issues = self.check_language_consistency(documents)
        for issue in language_issues:
            issues.append({
                "doc_id": "corpus",
                "issue": issue,
                "severity": "warning"
            })
            warnings += 1
        
        metadata_issues = self.check_metadata_consistency(documents)
        for issue in metadata_issues:
            issues.append({
                "doc_id": "corpus",
                "issue": issue,
                "severity": "error"
            })
        
        format_issues = self.check_format_consistency(documents, formats)
        for issue in format_issues:
            issues.append({
                "doc_id": "corpus",
                "issue": issue,
                "severity": "warning"
            })
            warnings += 1
        
        # Compute consistency score
        total_issues = len([i for i in issues if i["severity"] == "error"])
        consistency_score = 1.0 - (total_issues / max(len(documents), 1))
        consistency_score = max(0.0, min(1.0, consistency_score))
        
        return ValidationReport(
            total_docs=len(documents),
            passed=passed,
            failed=failed,
            warnings=warnings,
            issues=issues,
            consistency_score=consistency_score
        )


def validate_corpus(documents: Dict[str, Dict],
                   formats: Dict[str, int],
                   config: Dict = None) -> ValidationReport:
    """
    Validate corpus.
    
    Args:
        documents: Dict mapping doc_id -> doc data
        formats: Dict mapping format -> count
        config: Optional config
        
    Returns:
        ValidationReport
    """
    validator = CorpusValidator(config)
    return validator.validate_corpus(documents, formats)
