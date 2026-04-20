"""
Main corpus auditor orchestrator for Blog 1.
Coordinates format detection, quality scoring, and routing table generation.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from tqdm import tqdm

from src.utils import logger, JSONStore, DocumentStore, tracker, ensure_dir_exists
from src.models import DocumentQualityScore
from src.config import get_config

from .format_detector import get_detector
from .quality_scorer import get_scorer
from .pdf_auditor import audit_pdf, check_ocr_quality
from .html_auditor import audit_html, compute_content_ratio


class CorpusAuditor:
    """Main auditor for Blog 1: Corpus Audit & Quality Baselining."""
    
    def __init__(self):
        """Initialize auditor."""
        self.config = get_config()
        self.detector = get_detector()
        self.scorer = get_scorer()
        
        self.raw_corpus_path = Path(self.config.get("paths.raw_corpus", "data/raw_corpus"))
        self.audit_log_path = Path(self.config.get("paths.processed", "data/processed")) / "audit_logs"
        self.metadata_path = Path(self.config.get("paths.metadata", "data/metadata"))
        
        ensure_dir_exists(self.audit_log_path)
        ensure_dir_exists(self.metadata_path)
        
        self.quality_scores: List[DocumentQualityScore] = []
        self.routing_table: Dict[str, Dict[str, Any]] = {}
        
        logger.info("CorpusAuditor initialized")
    
    def discover_documents(self) -> List[Path]:
        """
        Discover all documents in raw_corpus directory.
        
        Returns:
            List of file paths
        """
        if not self.raw_corpus_path.exists():
            logger.warning(f"Raw corpus path not found: {self.raw_corpus_path}")
            return []
        
        files = list(self.raw_corpus_path.rglob("*"))
        files = [f for f in files if f.is_file() and not f.name.startswith(".")]
        
        logger.info(f"Discovered {len(files)} documents in corpus")
        return sorted(files)
    
    def audit_document(self, file_path: Path) -> Optional[DocumentQualityScore]:
        """
        Audit a single document.
        
        Args:
            file_path: Path to document
        
        Returns:
            DocumentQualityScore or None if failed
        """
        try:
            # Generate unique doc_id
            doc_id = file_path.stem  # filename without extension
            
            # Detect format
            format_type = self.detector.detect_format(file_path)
            if format_type is None:
                logger.warning(f"Could not determine format: {file_path}")
                return None
            
            # Read file
            try:
                if format_type == "pdf":
                    # PDFs: don't read full text here, audit metadata
                    text = f"[PDF: {file_path.name}]"
                    text_content = ""
                elif format_type in ["html", "json", "txt", "md", "py", "csv"]:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text_content = f.read(100_000)  # First 100k chars
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text_content = f.read(100_000)
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")
                return None
            
            # Generate quality scores
            quality_info = self.scorer.score_document(text_content)
            
            # Format-specific audits
            format_info = self._audit_format_specific(file_path, format_type, text_content)
            
            # Determine routing tag
            routing_tag = self._determine_routing_tag(format_type, format_info)
            
            # Create quality score object
            doc_quality = DocumentQualityScore(
                doc_id=doc_id,
                source_path=str(file_path),
                format_type=format_type,
                language=quality_info.get("language", "unknown"),
                language_confidence=quality_info.get("language_confidence", 0.0),
                perplexity=quality_info.get("perplexity"),
                char_count=quality_info.get("char_count", 0),
                word_count=quality_info.get("word_count", 0),
                quality_score=quality_info.get("quality_score", 0.0),
                layout_complexity=format_info.get("layout_complexity"),
                content_ratio=format_info.get("content_ratio"),
                ocr_quality=format_info.get("ocr_quality"),
                schema_drift_flag=format_info.get("schema_drift_flag", False),
                estimated_retrieval_utility=self._estimate_retrieval_utility(quality_info, format_info),
                requires_special_handling=self._requires_special_handling(format_type, format_info),
                routing_tag=routing_tag,
                blog_stages_passed=[1],
            )
            
            logger.debug(f"Audited document: {doc_id} (format={format_type}, quality={doc_quality.quality_score:.2f})")
            return doc_quality
        
        except Exception as e:
            logger.error(f"Audit failed for {file_path}: {e}", exc_info=True)
            return None
    
    def _audit_format_specific(
        self,
        file_path: Path,
        format_type: str,
        text_content: str,
    ) -> Dict[str, Any]:
        """Run format-specific audit checks."""
        format_info = {
            "layout_complexity": None,
            "content_ratio": None,
            "ocr_quality": None,
            "schema_drift_flag": False,
        }
        
        try:
            if format_type == "pdf":
                # PDF audit
                pdf_audit = audit_pdf(file_path)
                format_info["layout_complexity"] = pdf_audit.get("layout_complexity", "simple")
                
                # Check OCR quality if text extracted
                if pdf_audit.get("has_text"):
                    ocr_qual = check_ocr_quality(text_content)
                    format_info["ocr_quality"] = ocr_qual
            
            elif format_type == "html":
                # HTML audit
                html_audit = audit_html(file_path)
                format_info["content_ratio"] = html_audit.get("content_ratio", 0.5)
                format_info["layout_complexity"] = "simple"  # HTML is structured
            
            elif format_type == "json":
                # JSON audit: check schema drift
                try:
                    import json as json_lib
                    with open(file_path, 'r') as f:
                        json_lib.load(f)
                    format_info["schema_drift_flag"] = False
                except:
                    format_info["schema_drift_flag"] = True
            
            elif format_type == "csv":
                # CSV audit: structured format
                format_info["layout_complexity"] = "simple"
                format_info["schema_drift_flag"] = False
        
        except Exception as e:
            logger.warning(f"Format-specific audit failed: {e}")
        
        return format_info
    
    def _determine_routing_tag(self, format_type: str, format_info: Dict[str, Any]) -> str:
        """Determine which parsing sub-pipeline to use."""
        
        if format_type == "pdf":
            if format_info.get("layout_complexity") == "multi_column":
                return "pdf_text_multicolumn"
            elif format_info.get("layout_complexity") in ["table_heavy", "diagram_heavy"]:
                return "pdf_text_complex"
            else:
                return "pdf_text"
        
        elif format_type == "html":
            ratio = format_info.get("content_ratio", 0.5)
            if ratio < 0.2:
                return "html_boilerplate_heavy"
            else:
                return "html"
        
        else:
            return format_type  # Direct format name
    
    def _estimate_retrieval_utility(
        self,
        quality_info: Dict[str, Any],
        format_info: Dict[str, Any],
    ) -> float:
        """Estimate how useful this document will be for retrieval."""
        
        quality_score = quality_info.get("quality_score", 0.5)
        content_ratio = format_info.get("content_ratio", 1.0)
        
        # Lower utility if boilerplate-heavy HTML
        if content_ratio is not None and content_ratio < 0.2:
            quality_score *= 0.5
        
        return round(quality_score, 3)
    
    def _requires_special_handling(self, format_type: str, format_info: Dict[str, Any]) -> bool:
        """Check if document needs special parsing."""
        
        if format_type == "pdf":
            # Scanned PDFs or complex layouts need special handling
            layout = format_info.get("layout_complexity", "simple")
            return layout in ["multi_column", "table_heavy", "diagram_heavy"]
        
        elif format_type == "html":
            # Boilerplate-heavy HTML needs aggressive cleaning
            ratio = format_info.get("content_ratio", 0.5)
            return ratio < 0.2
        
        return False
    
    def audit_corpus(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Audit entire corpus.
        
        Args:
            sample_size: If set, only audit first N documents
        
        Returns:
            Summary statistics
        """
        tracker.start("blog1_audit")
        
        # Discover documents
        files = self.discover_documents()
        
        if sample_size:
            files = files[:sample_size]
        
        logger.info(f"Auditing {len(files)} documents...")
        
        # Audit each document
        for file_path in tqdm(files, desc="Blog 1: Auditing corpus"):
            doc_quality = self.audit_document(file_path)
            
            if doc_quality:
                self.quality_scores.append(doc_quality)
                self.routing_table[doc_quality.doc_id] = {
                    "source_path": doc_quality.source_path,
                    "format_type": doc_quality.format_type,
                    "routing_tag": doc_quality.routing_tag,
                    "quality_score": doc_quality.quality_score,
                }
        
        tracker.end("blog1_audit", len(self.quality_scores))
        
        # Save outputs
        self._save_results()
        
        # Return summary
        summary = self._generate_summary()
        return summary
    
    def _save_results(self) -> None:
        """Save audit results to JSON files."""
        
        # Save quality scores
        quality_scores_list = [q.to_dict() for q in self.quality_scores]
        quality_scores_path = self.metadata_path / "quality_scores.json"
        JSONStore.save_list(quality_scores_list, quality_scores_path)
        logger.info(f"Saved {len(quality_scores_list)} quality scores: {quality_scores_path}")
        
        # Save routing table
        routing_path = self.metadata_path / "routing_table.json"
        JSONStore.save_single(self.routing_table, routing_path)
        logger.info(f"Saved routing table: {routing_path}")
        
        # Save audit logs (per-document)
        store = DocumentStore(self.audit_log_path)
        for doc_quality in self.quality_scores:
            store.save_document(doc_quality.doc_id, doc_quality.to_dict(), stage="audit")
        logger.info(f"Saved {len(self.quality_scores)} audit logs to {self.audit_log_path}")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate audit summary statistics."""
        
        if not self.quality_scores:
            return {
                "status": "no_documents",
                "total_documents": 0,
            }
        
        format_counts = {}
        quality_distribution = {"high": 0, "medium": 0, "low": 0}
        
        for doc in self.quality_scores:
            # Format counts
            fmt = doc.format_type
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
            
            # Quality distribution
            if doc.quality_score >= 0.7:
                quality_distribution["high"] += 1
            elif doc.quality_score >= 0.4:
                quality_distribution["medium"] += 1
            else:
                quality_distribution["low"] += 1
        
        avg_quality = sum(d.quality_score for d in self.quality_scores) / len(self.quality_scores)
        
        return {
            "status": "success",
            "total_documents": len(self.quality_scores),
            "format_distribution": format_counts,
            "quality_distribution": quality_distribution,
            "average_quality": round(avg_quality, 3),
            "routing_tags": set(rt["routing_tag"] for rt in self.routing_table.values()),
        }


def run_audit(sample_size: Optional[int] = None) -> Dict[str, Any]:
    """Run corpus audit from pipeline."""
    auditor = CorpusAuditor()
    return auditor.audit_corpus(sample_size=sample_size)
