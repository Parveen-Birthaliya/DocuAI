"""
Configuration loader for DocuAI pipeline.
Reads config.yaml and provides access to all settings.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """
    Configuration manager for DocuAI.
    Loads config.yaml and provides typed access to settings.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to config.yaml (default: ./config.yaml)
        """
        # Load environment variables first
        load_dotenv()
        
        # Find config file
        if config_path is None:
            config_path = "config.yaml"
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # Load YAML
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation key.
        
        Example:
            config.get("blog1_audit.pdf.ocr_quality_threshold")
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire config section."""
        return self._config.get(section, {})
    
    @property
    def raw_corpus_path(self) -> str:
        return self.get("paths.raw_corpus", "data/raw_corpus")
    
    @property
    def processed_path(self) -> str:
        return self.get("paths.processed", "data/processed")
    
    @property
    def metadata_path(self) -> str:
        return self.get("paths.metadata", "data/metadata")
    
    @property
    def embeddings_path(self) -> str:
        return self.get("paths.embeddings", "data/processed/embeddings.faiss")
    
    def __repr__(self) -> str:
        return f"Config(sections: {list(self._config.keys())})"


# Global config instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get global config instance (singleton pattern).
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def load_config(path: str) -> Config:
    """
    Load config from a specific path and set as global instance.
    """
    global _config_instance
    _config_instance = Config(path)
    return _config_instance
