"""
JSON persistence utilities for DocuAI.
Handles saving/loading documents through the pipeline.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union, Optional
from .file_handler import ensure_dir_exists, ensure_parent_dir
from .logger import logger


class JSONStore:
    """Handle JSON persistence for pipeline data."""
    
    @staticmethod
    def save_single(
        data: Dict[str, Any],
        path: Union[str, Path],
        indent: int = 2,
        pretty: bool = True,
    ) -> None:
        """
        Save a single document/object to JSON file.
        
        Args:
            data: Dictionary to save
            path: Output file path
            indent: JSON indentation
            pretty: Whether to format nicely
        """
        ensure_parent_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(
                data,
                f,
                indent=indent if pretty else None,
                ensure_ascii=False,
                default=str,  # Handle non-serializable types
            )
        logger.debug(f"Saved JSON: {path}")
    
    @staticmethod
    def load_single(path: Union[str, Path]) -> Dict[str, Any]:
        """Load a single JSON document."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON: {path}")
        return data
    
    @staticmethod
    def save_list(
        data_list: List[Dict[str, Any]],
        path: Union[str, Path],
        indent: int = 2,
        pretty: bool = True,
    ) -> None:
        """Save list of documents to JSON file."""
        ensure_parent_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(
                data_list,
                f,
                indent=indent if pretty else None,
                ensure_ascii=False,
                default=str,
            )
        logger.debug(f"Saved JSON list with {len(data_list)} items: {path}")
    
    @staticmethod
    def load_list(path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load list from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Expected list in {path}, got {type(data)}")
        logger.debug(f"Loaded JSON list with {len(data)} items: {path}")
        return data
    
    @staticmethod
    def save_jsonl(
        data_list: List[Dict[str, Any]],
        path: Union[str, Path],
    ) -> None:
        """
        Save list as JSON Lines (one object per line).
        Better for streaming large datasets.
        """
        ensure_parent_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            for item in data_list:
                json.dump(item, f, ensure_ascii=False, default=str)
                f.write('\n')
        logger.debug(f"Saved JSONL with {len(data_list)} items: {path}")
    
    @staticmethod
    def load_jsonl(path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load JSON Lines file."""
        data_list = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data_list.append(json.loads(line))
        logger.debug(f"Loaded JSONL with {len(data_list)} items: {path}")
        return data_list
    
    @staticmethod
    def append_jsonl(
        data: Dict[str, Any],
        path: Union[str, Path],
    ) -> None:
        """Append one item to JSON Lines file."""
        ensure_parent_dir(path)
        with open(path, 'a', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=str)
            f.write('\n')
    
    @staticmethod
    def load_or_create(
        path: Union[str, Path],
        default: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Load JSON file or return default if not exists."""
        path = Path(path)
        if path.exists():
            return JSONStore.load_single(path)
        else:
            if default is None:
                default = {}
            JSONStore.save_single(default, path)
            return default


class DocumentStore:
    """
    High-level store for managing documents through pipeline stages.
    Organizes files by doc_id for easy lookup.
    """
    
    def __init__(self, base_path: Union[str, Path]):
        """
        Initialize document store.
        
        Args:
            base_path: Base directory for storing documents
        """
        self.base_path = Path(base_path)
        ensure_dir_exists(self.base_path)
    
    def save_document(
        self,
        doc_id: str,
        data: Dict[str, Any],
        stage: str = "raw",
    ) -> Path:
        """
        Save a document at a specific pipeline stage.
        
        Args:
            doc_id: Document identifier
            data: Document data
            stage: Pipeline stage name (audit, parsing, cleaning, etc.)
        
        Returns:
            Path where saved
        """
        stage_dir = ensure_dir_exists(self.base_path / stage)
        file_path = stage_dir / f"{doc_id}.json"
        JSONStore.save_single(data, file_path)
        return file_path
    
    def load_document(
        self,
        doc_id: str,
        stage: str = "raw",
    ) -> Optional[Dict[str, Any]]:
        """Load a document from a specific stage."""
        file_path = self.base_path / stage / f"{doc_id}.json"
        if file_path.exists():
            return JSONStore.load_single(file_path)
        return None
    
    def exists(self, doc_id: str, stage: str = "raw") -> bool:
        """Check if document exists at stage."""
        file_path = self.base_path / stage / f"{doc_id}.json"
        return file_path.exists()
    
    def list_documents(self, stage: str = "raw") -> List[str]:
        """List all document IDs at a stage."""
        stage_dir = self.base_path / stage
        if not stage_dir.exists():
            return []
        return [f.stem for f in stage_dir.glob("*.json")]
    
    def count_documents(self, stage: str = "raw") -> int:
        """Count documents at stage."""
        return len(self.list_documents(stage))
