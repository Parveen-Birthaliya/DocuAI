"""
Blog 2: JSON Parser

Parses JSON documents with schema analysis and flattening.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedJSONDocument:
    """Parsed JSON document"""
    doc_id: str
    source_path: str
    raw_data: Dict[str, Any]
    flattened_text: str
    schema_depth: int
    key_count: int
    has_arrays: bool
    has_nested_objects: bool
    parsing_quality: float


class JSONParser:
    """Parse JSON documents"""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize JSON parser.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.max_depth = self.config.get("max_depth", 10)

    def flatten_json(self, obj: Any, parent_key: str = "", sep: str = ".") -> Dict[str, str]:
        """
        Flatten nested JSON structure.
        
        Args:
            obj: JSON object to flatten
            parent_key: Parent key for nested objects
            sep: Separator for nested keys
            
        Returns:
            Dictionary with flattened structure
        """
        items: List[tuple] = []
        
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                
                if isinstance(v, dict):
                    items.extend(self.flatten_json(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    # Handle lists by concatenating string representations
                    for i, item in enumerate(v):
                        list_key = f"{new_key}[{i}]"
                        if isinstance(item, (dict, list)):
                            items.extend(self.flatten_json(item, list_key, sep=sep).items())
                        else:
                            items.append((list_key, str(item)))
                else:
                    items.append((new_key, str(v)))
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_key = f"{parent_key}[{i}]"
                if isinstance(item, (dict, list)):
                    items.extend(self.flatten_json(item, new_key, sep=sep).items())
                else:
                    items.append((new_key, str(item)))
        
        else:
            items.append((parent_key, str(obj)))
        
        return dict(items)

    def calculate_depth(self, obj: Any, current_depth: int = 0) -> int:
        """
        Calculate maximum depth of JSON structure.
        
        Args:
            obj: JSON object
            current_depth: Current depth level
            
        Returns:
            Maximum depth
        """
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self.calculate_depth(v, current_depth + 1) for v in obj.values())
        
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self.calculate_depth(item, current_depth + 1) for item in obj)
        
        else:
            return current_depth

    def analyze_structure(self, obj: Any) -> Dict:
        """
        Analyze JSON structure.
        
        Args:
            obj: JSON object
            
        Returns:
            Structure analysis dictionary
        """
        analysis = {
            "depth": self.calculate_depth(obj),
            "has_arrays": self._contains_arrays(obj),
            "has_nested_objects": self._contains_nested_objects(obj),
            "key_count": self._count_keys(obj)
        }
        
        return analysis

    def _contains_arrays(self, obj: Any) -> bool:
        """Check if structure contains arrays"""
        if isinstance(obj, list):
            return True
        elif isinstance(obj, dict):
            return any(self._contains_arrays(v) for v in obj.values())
        return False

    def _contains_nested_objects(self, obj: Any, depth: int = 0) -> bool:
        """Check if structure contains nested objects"""
        if depth > 1 and isinstance(obj, dict):
            return True
        elif isinstance(obj, dict):
            return any(self._contains_nested_objects(v, depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            return any(self._contains_nested_objects(item, depth + 1) for item in obj)
        return False

    def _count_keys(self, obj: Any) -> int:
        """Count total keys in structure"""
        count = 0
        
        if isinstance(obj, dict):
            count = len(obj)
            for v in obj.values():
                count += self._count_keys(v)
        
        elif isinstance(obj, list):
            for item in obj:
                count += self._count_keys(item)
        
        return count

    def parse(self, json_path: Path, doc_id: str) -> ParsedJSONDocument:
        """
        Parse JSON document.
        
        Args:
            json_path: Path to JSON file
            doc_id: Document ID
            
        Returns:
            ParsedJSONDocument
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            logger.error(f"Error parsing JSON {json_path}: {e}")
            return ParsedJSONDocument(
                doc_id=doc_id,
                source_path=str(json_path),
                raw_data={},
                flattened_text="",
                schema_depth=0,
                key_count=0,
                has_arrays=False,
                has_nested_objects=False,
                parsing_quality=0.0
            )
        
        # Analyze structure
        structure = self.analyze_structure(raw_data)
        
        # Flatten JSON
        flattened = self.flatten_json(raw_data)
        
        # Create text representation
        flattened_text = "\n".join(
            f"{k}: {v}" for k, v in flattened.items()
        )
        
        # Calculate quality
        quality = min(structure["key_count"] / 1000, 1.0) if structure["key_count"] > 0 else 0.5
        
        return ParsedJSONDocument(
            doc_id=doc_id,
            source_path=str(json_path),
            raw_data=raw_data,
            flattened_text=flattened_text,
            schema_depth=structure["depth"],
            key_count=structure["key_count"],
            has_arrays=structure["has_arrays"],
            has_nested_objects=structure["has_nested_objects"],
            parsing_quality=quality
        )


def parse_json(json_path: Path, doc_id: str, config: Optional[Dict] = None) -> ParsedJSONDocument:
    """
    Convenience function to parse JSON.
    
    Args:
        json_path: Path to JSON file
        doc_id: Document ID
        config: Optional configuration
        
    Returns:
        ParsedJSONDocument
    """
    parser = JSONParser(config)
    return parser.parse(json_path, doc_id)
