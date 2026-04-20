"""
Blog 2: Plain Text, Markdown, and Code Parsers

Handles plain text, Markdown, and Python code files.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import ast
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedPlainTextDocument:
    """Parsed plain text document"""
    doc_id: str
    source_path: str
    content: str
    line_count: int
    word_count: int
    avg_line_length: float
    parsing_quality: float


@dataclass
class ParsedMarkdownDocument:
    """Parsed Markdown document"""
    doc_id: str
    source_path: str
    content: str
    headings: List[Dict]  # {level, text}
    code_blocks: int
    links: int
    tables: int
    line_count: int
    parsing_quality: float


@dataclass
class ParsedCodeDocument:
    """Parsed Python code document"""
    doc_id: str
    source_path: str
    content: str
    functions: List[str]
    classes: List[str]
    imports: List[str]
    docstring: str
    line_count: int
    parsing_quality: float


class PlainTextParser:
    """Parse plain text documents"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

    def parse(self, txt_path: Path, doc_id: str) -> ParsedPlainTextDocument:
        """Parse plain text document"""
        try:
            with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading text file {txt_path}: {e}")
            return ParsedPlainTextDocument(
                doc_id=doc_id,
                source_path=str(txt_path),
                content="",
                line_count=0,
                word_count=0,
                avg_line_length=0.0,
                parsing_quality=0.0
            )
        
        lines = content.split("\n")
        line_count = len(lines)
        word_count = len(content.split())
        avg_line_length = sum(len(line) for line in lines) / max(line_count, 1)
        
        # Quality score based on content
        quality = min(word_count / 1000, 1.0) if word_count > 0 else 0.0
        
        return ParsedPlainTextDocument(
            doc_id=doc_id,
            source_path=str(txt_path),
            content=content,
            line_count=line_count,
            word_count=word_count,
            avg_line_length=avg_line_length,
            parsing_quality=quality
        )


class MarkdownParser:
    """Parse Markdown documents"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

    def extract_headings(self, content: str) -> List[Dict]:
        """Extract Markdown headings"""
        headings = []
        for line in content.split("\n"):
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                text = line.lstrip("#").strip()
                if text:
                    headings.append({"level": level, "text": text})
        return headings

    def parse(self, md_path: Path, doc_id: str) -> ParsedMarkdownDocument:
        """Parse Markdown document"""
        try:
            with open(md_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading markdown file {md_path}: {e}")
            return ParsedMarkdownDocument(
                doc_id=doc_id,
                source_path=str(md_path),
                content="",
                headings=[],
                code_blocks=0,
                links=0,
                tables=0,
                line_count=0,
                parsing_quality=0.0
            )
        
        # Extract structure
        headings = self.extract_headings(content)
        code_blocks = content.count("```")
        links = content.count("](")
        tables = content.count("|")
        line_count = len(content.split("\n"))
        
        # Quality score
        quality = min(line_count / 100, 1.0) if line_count > 0 else 0.0
        
        return ParsedMarkdownDocument(
            doc_id=doc_id,
            source_path=str(md_path),
            content=content,
            headings=headings,
            code_blocks=code_blocks,
            links=links,
            tables=tables,
            line_count=line_count,
            parsing_quality=quality
        )


class PythonCodeParser:
    """Parse Python code documents"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}

    def extract_ast_info(self, content: str) -> Dict:
        """Extract information from Python AST"""
        info = {
            "functions": [],
            "classes": [],
            "imports": [],
            "docstring": ""
        }
        
        try:
            tree = ast.parse(content)
            
            # Module docstring
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                info["docstring"] = module_docstring
            
            # Top-level definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    info["functions"].append(node.name)
                elif isinstance(node, ast.ClassDef):
                    info["classes"].append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        info["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        info["imports"].append(f"{module}.{alias.name}")
        
        except SyntaxError as e:
            logger.warning(f"Could not parse Python AST: {e}")
        
        return info

    def parse(self, py_path: Path, doc_id: str) -> ParsedCodeDocument:
        """Parse Python code document"""
        try:
            with open(py_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading Python file {py_path}: {e}")
            return ParsedCodeDocument(
                doc_id=doc_id,
                source_path=str(py_path),
                content="",
                functions=[],
                classes=[],
                imports=[],
                docstring="",
                line_count=0,
                parsing_quality=0.0
            )
        
        # Extract AST info
        ast_info = self.extract_ast_info(content)
        
        line_count = len(content.split("\n"))
        
        # Quality score
        quality = 1.0 if ast_info["functions"] or ast_info["classes"] else 0.5
        
        return ParsedCodeDocument(
            doc_id=doc_id,
            source_path=str(py_path),
            content=content,
            functions=ast_info["functions"],
            classes=ast_info["classes"],
            imports=ast_info["imports"],
            docstring=ast_info["docstring"],
            line_count=line_count,
            parsing_quality=quality
        )


# Convenience functions
def parse_plaintext(txt_path: Path, doc_id: str, config: Optional[Dict] = None) -> ParsedPlainTextDocument:
    """Parse plain text document"""
    parser = PlainTextParser(config)
    return parser.parse(txt_path, doc_id)


def parse_markdown(md_path: Path, doc_id: str, config: Optional[Dict] = None) -> ParsedMarkdownDocument:
    """Parse Markdown document"""
    parser = MarkdownParser(config)
    return parser.parse(md_path, doc_id)


def parse_python(py_path: Path, doc_id: str, config: Optional[Dict] = None) -> ParsedCodeDocument:
    """Parse Python code document"""
    parser = PythonCodeParser(config)
    return parser.parse(py_path, doc_id)
