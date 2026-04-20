"""
Utilities module for DocuAI RAG pipeline.
"""

from .logger import setup_logger, logger
from .file_handler import (
    ensure_dir_exists,
    ensure_parent_dir,
    list_files,
    remove_file,
    remove_dir,
    get_file_extension,
    read_text,
    write_text,
)
from .json_store import JSONStore, DocumentStore
from .time_tracker import TimeTracker, tracker
from .constants import (
    SUPPORTED_FORMATS,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    QUALITY_THRESHOLDS,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_TOP_K,
)

__all__ = [
    "logger",
    "setup_logger",
    "ensure_dir_exists",
    "ensure_parent_dir",
    "list_files",
    "remove_file",
    "remove_dir",
    "get_file_extension",
    "read_text",
    "write_text",
    "JSONStore",
    "DocumentStore",
    "TimeTracker",
    "tracker",
    "SUPPORTED_FORMATS",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIM",
    "QUALITY_THRESHOLDS",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_TOP_K",
]
