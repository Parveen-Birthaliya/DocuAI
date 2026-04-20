"""
Blog 5: Merge knowledge sets from deduplicated documents

Intelligently merge knowledge extracted from duplicate documents.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MergedKnowledge:
    """Merged knowledge from duplicate documents"""
    canonical_doc_id: str
    duplicate_doc_ids: List[str]
    merged_tables: List[Dict] = field(default_factory=list)
    merged_metadata: Dict = field(default_factory=dict)
    merged_code_blocks: List[Dict] = field(default_factory=list)
    merged_sections: List[Dict] = field(default_factory=list)
    merge_confidence: float = 1.0


class MergeStrategy:
    """Base class for merge strategies"""
    
    def merge_metadata(self, metadata_list: List[Dict]) -> Dict:
        """Merge metadata from multiple documents"""
        raise NotImplementedError
    
    def merge_tables(self, tables_list: List[List[Dict]]) -> List[Dict]:
        """Merge tables from multiple documents"""
        raise NotImplementedError
    
    def merge_code(self, code_list: List[List[Dict]]) -> List[Dict]:
        """Merge code blocks from multiple documents"""
        raise NotImplementedError


class FirstWinMergeStrategy(MergeStrategy):
    """Always use first document's knowledge"""
    
    def merge_metadata(self, metadata_list: List[Dict]) -> Dict:
        """Keep first metadata"""
        return metadata_list[0] if metadata_list else {}
    
    def merge_tables(self, tables_list: List[List[Dict]]) -> List[Dict]:
        """Keep first tables"""
        return tables_list[0] if tables_list else []
    
    def merge_code(self, code_list: List[List[Dict]]) -> List[Dict]:
        """Keep first code blocks"""
        return code_list[0] if code_list else []


class ConsolidateMergeStrategy(MergeStrategy):
    """Consolidate all unique knowledge"""
    
    def merge_metadata(self, metadata_list: List[Dict]) -> Dict:
        """Merge metadata intelligently"""
        merged = {}
        
        # Title source preference: longest non-empty
        titles = [m.get("title") for m in metadata_list if m.get("title")]
        if titles:
            merged["title"] = max(titles, key=len)
        
        # Authors: combine and deduplicate
        all_authors = set()
        for m in metadata_list:
            if m.get("authors"):
                all_authors.update(m["authors"])
        if all_authors:
            merged["authors"] = list(all_authors)
        
        # Keywords: combine and deduplicate
        all_keywords = set()
        for m in metadata_list:
            if m.get("keywords"):
                all_keywords.update(m["keywords"])
        if all_keywords:
            merged["keywords"] = list(all_keywords)
        
        # Language: first non-empty
        language = next((m.get("language") for m in metadata_list if m.get("language")), None)
        if language:
            merged["language"] = language
        
        # Summary: use first non-empty
        summary = next((m.get("summary") for m in metadata_list if m.get("summary")), None)
        if summary:
            merged["summary"] = summary
        
        # Date: most recent
        dates = [m.get("date_published") for m in metadata_list if m.get("date_published")]
        if dates:
            merged["date_published"] = max(dates)
        
        # Entities: combine
        merged_entities = {}
        for m in metadata_list:
            if m.get("entities"):
                for entity_type, values in m["entities"].items():
                    if entity_type not in merged_entities:
                        merged_entities[entity_type] = set()
                    if isinstance(values, list):
                        merged_entities[entity_type].update(values)
        
        if merged_entities:
            merged["entities"] = {k: list(v) for k, v in merged_entities.items()}
        
        return merged
    
    def merge_tables(self, tables_list: List[List[Dict]]) -> List[Dict]:
        """Merge tables deduplicating by signature"""
        merged = {}
        
        for tables in tables_list:
            for table in tables:
                # Create signature for table
                sig = self._table_signature(table)
                
                if sig not in merged:
                    merged[sig] = table
                else:
                    # If better quality found, replace
                    if self._table_quality(table) > self._table_quality(merged[sig]):
                        merged[sig] = table
        
        return list(merged.values())
    
    def merge_code(self, code_list: List[List[Dict]]) -> List[Dict]:
        """Merge code blocks deduplicating"""
        merged = {}
        
        for code_blocks in code_list:
            for code in code_blocks:
                # Use code content as key
                code_text = code.get("code", "").strip()
                
                if code_text not in merged:
                    merged[code_text] = code
                else:
                    # Keep most informative version
                    if len(code.get("language", "")) > len(merged[code_text].get("language", "")):
                        merged[code_text] = code
        
        return list(merged.values())
    
    @staticmethod
    def _table_signature(table: Dict) -> str:
        """Create signature for table"""
        headers = tuple(table.get("headers", []))
        num_rows = table.get("num_rows", 0)
        return f"{headers}_{num_rows}"
    
    @staticmethod
    def _table_quality(table: Dict) -> float:
        """Score table quality"""
        score = 0.0
        if table.get("headers"):
            score += 0.5
        if table.get("num_rows"):
            score += min(0.5, table["num_rows"] / 100)
        return score


class KnowledgeMerger:
    """Merge knowledge from duplicate documents"""
    
    def __init__(self, strategy: MergeStrategy = None):
        self.strategy = strategy or ConsolidateMergeStrategy()
    
    def merge_duplicate_set(self, doc_ids: List[str],
                           knowledge_map: Dict) -> MergedKnowledge:
        """
        Merge knowledge from duplicate documents.
        
        Args:
            doc_ids: List of duplicate document IDs
            knowledge_map: Dict mapping doc_id -> extracted knowledge
            
        Returns:
            MergedKnowledge
        """
        if not doc_ids:
            raise ValueError("Empty document list")
        
        # Use first as canonical
        canonical_doc_id = doc_ids[0]
        duplicate_ids = doc_ids[1:]
        
        # Extract knowledge lists
        metadata_list = []
        tables_list = []
        code_list = []
        sections_list = []
        
        for doc_id in doc_ids:
            if doc_id in knowledge_map:
                knowledge = knowledge_map[doc_id]
                
                if knowledge.get("metadata"):
                    metadata_list.append(knowledge["metadata"])
                
                if knowledge.get("tables"):
                    tables_list.append(knowledge["tables"])
                
                if knowledge.get("code_blocks"):
                    code_list.append(knowledge["code_blocks"])
                
                if knowledge.get("sections"):
                    sections_list.append(knowledge["sections"])
        
        # Merge using strategy
        merged_metadata = self.strategy.merge_metadata(metadata_list)
        merged_tables = self.strategy.merge_tables(tables_list)
        merged_code = self.strategy.merge_code(code_list)
        
        # Consolidate sections (just combine)
        merged_sections = []
        for sections in sections_list:
            merged_sections.extend(sections)
        
        return MergedKnowledge(
            canonical_doc_id=canonical_doc_id,
            duplicate_doc_ids=duplicate_ids,
            merged_tables=merged_tables,
            merged_metadata=merged_metadata,
            merged_code_blocks=merged_code,
            merged_sections=merged_sections,
            merge_confidence=0.95  # High confidence since we're just consolidating
        )
    
    def merge_all_duplicates(self, duplicate_groups: List[List[str]],
                            knowledge_map: Dict) -> List[MergedKnowledge]:
        """
        Merge all duplicate groups.
        
        Args:
            duplicate_groups: List of duplicate document ID groups
            knowledge_map: Dict mapping doc_id -> extracted knowledge
            
        Returns:
            List of MergedKnowledge
        """
        merged = []
        
        for group in duplicate_groups:
            try:
                merged_knowledge = self.merge_duplicate_set(group, knowledge_map)
                merged.append(merged_knowledge)
                logger.info(f"Merged {len(group)} documents, canonical: {merged_knowledge.canonical_doc_id}")
            except Exception as e:
                logger.error(f"Error merging group {group}: {e}")
        
        return merged


def merge_duplicates(duplicate_groups: List[List[str]],
                    knowledge_map: Dict,
                    strategy: str = "consolidate") -> List[MergedKnowledge]:
    """
    Merge knowledge from duplicate documents.
    
    Args:
        duplicate_groups: List of duplicate document ID groups
        knowledge_map: Dict mapping doc_id -> extracted knowledge
        strategy: "first_win" or "consolidate"
        
    Returns:
        List of MergedKnowledge
    """
    if strategy == "first_win":
        merge_strategy = FirstWinMergeStrategy()
    else:
        merge_strategy = ConsolidateMergeStrategy()
    
    merger = KnowledgeMerger(merge_strategy)
    return merger.merge_all_duplicates(duplicate_groups, knowledge_map)
