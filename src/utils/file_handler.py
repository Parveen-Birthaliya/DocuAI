"""
File handling utilities for DocuAI.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Union, Any, Dict, List, Optional


def ensure_dir_exists(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if not."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent_dir(path: Union[str, Path]) -> Path:
    """Ensure parent directory exists."""
    path = Path(path)
    ensure_dir_exists(path.parent)
    return path


def get_file_size(path: Union[str, Path]) -> int:
    """Get file size in bytes."""
    return Path(path).stat().st_size


def list_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False,
) -> List[Path]:
    """
    List files in directory matching pattern.
    
    Args:
        directory: Directory path
        pattern: File pattern (e.g., "*.pdf")
        recursive: Whether to search recursively
    
    Returns:
        List of Path objects
    """
    directory = Path(directory)
    if not directory.exists():
        return []
    
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))


def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> None:
    """Copy file from src to dst."""
    ensure_parent_dir(dst)
    shutil.copy2(src, dst)


def remove_file(path: Union[str, Path]) -> None:
    """Remove file if it exists."""
    path = Path(path)
    if path.exists():
        path.unlink()


def remove_dir(path: Union[str, Path]) -> None:
    """Remove directory recursively."""
    path = Path(path)
    if path.exists():
        shutil.rmtree(path)


def get_file_extension(path: Union[str, Path]) -> str:
    """Get file extension (lowercase, without dot)."""
    return Path(path).suffix.lower()[1:]


def read_text(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Read text file."""
    return Path(path).read_text(encoding=encoding)


def write_text(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
) -> None:
    """Write text file."""
    ensure_parent_dir(path)
    Path(path).write_text(content, encoding=encoding)


def read_binary(path: Union[str, Path]) -> bytes:
    """Read binary file."""
    return Path(path).read_bytes()


def write_binary(
    path: Union[str, Path],
    content: bytes,
) -> None:
    """Write binary file."""
    ensure_parent_dir(path)
    Path(path).write_bytes(content)
