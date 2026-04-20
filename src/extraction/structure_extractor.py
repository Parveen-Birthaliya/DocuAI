"""
Blog 4: Code and Section Extraction

Extract code blocks, sections, and structured content.
"""

import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedCode:
    """Extracted code snippet"""
    code_id: str
    language: str
    code: str
    line_count: int
    context: str  # Surrounding text


@dataclass
class ExtractedSection:
    """Extracted document section"""
    section_id: str
    title: str
    level: int  # Heading level
    content: str
    subsections: List['ExtractedSection']


class CodeExtractor:
    """Extract code blocks from text"""

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def extract_fenced_code(self, text: str) -> List[ExtractedCode]:
        """Extract code from fenced blocks (```...```)"""
        codes = []
        pattern = r'```(\w+)?\n(.*?)\n```'
        
        for i, match in enumerate(re.finditer(pattern, text, re.DOTALL)):
            language = match.group(1) or "text"
            code = match.group(2)
            
            # Get context
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            
            codes.append(ExtractedCode(
                code_id=f"code_{i}",
                language=language,
                code=code,
                line_count=len(code.split('\n')),
                context=context
            ))
        
        return codes

    def extract_indented_code(self, text: str, min_indent: int = 4) -> List[ExtractedCode]:
        """Extract indented code blocks"""
        codes = []
        lines = text.split('\n')
        
        in_block = False
        block_lines = []
        
        for line in lines:
            # Check indentation
            indent = len(line) - len(line.lstrip())
            
            if indent >= min_indent and line.strip():
                if not in_block:
                    in_block = True
                    block_lines = [line]
                else:
                    block_lines.append(line)
            else:
                if in_block and block_lines:
                    code = '\n'.join(block_lines)
                    if code.strip():
                        codes.append(ExtractedCode(
                            code_id=f"code_{len(codes)}",
                            language="text",
                            code=code,
                            line_count=len(block_lines),
                            context=""
                        ))
                    in_block = False
                    block_lines = []
        
        return codes

    def extract_all_code(self, text: str) -> List[ExtractedCode]:
        """Extract all code blocks"""
        codes = []
        
        # Fenced code first
        codes.extend(self.extract_fenced_code(text))
        
        # Then indented
        indented = self.extract_indented_code(text)
        for code in indented:
            code.code_id = f"code_{len(codes)}"
            codes.append(code)
        
        return codes


class SectionExtractor:
    """Extract document sections and structure"""

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def extract_sections(self, text: str) -> List[ExtractedSection]:
        """Extract sections from heading structure"""
        sections = []
        lines = text.split('\n')
        
        current_section = None
        section_stack = []  # Stack of sections by level
        
        for i, line in enumerate(lines):
            # Check for heading
            heading_match = re.match(r'^(#+)\s+(.+)$', line)
            
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                # Create new section
                new_section = ExtractedSection(
                    section_id=f"section_{len(sections)}",
                    title=title,
                    level=level,
                    content="",
                    subsections=[]
                )
                
                # Find parent based on level
                while section_stack and section_stack[-1].level >= level:
                    section_stack.pop()
                
                if section_stack:
                    section_stack[-1].subsections.append(new_section)
                else:
                    sections.append(new_section)
                
                section_stack.append(new_section)
            
            elif section_stack:
                # Add content to current section
                section_stack[-1].content += line + "\n"
        
        return sections

    def extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs"""
        # Split on double newlines
        paragraphs = text.split('\n\n')
        
        # Filter and clean
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Remove very short paragraphs
        paragraphs = [p for p in paragraphs if len(p) > 20]
        
        return paragraphs

    def extract_lists(self, text: str) -> List[List[str]]:
        """Extract bullet/numbered lists"""
        lists = []
        lines = text.split('\n')
        
        in_list = False
        list_items = []
        
        for line in lines:
            # Check for list markers
            if re.match(r'^\s*[-•*]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
                if not in_list:
                    in_list = True
                    list_items = []
                
                # Extract item text
                item = re.sub(r'^\s*[-•*\d.]+\s+', '', line).strip()
                list_items.append(item)
            
            else:
                if in_list and list_items:
                    lists.append(list_items)
                    in_list = False
                    list_items = []
        
        if in_list and list_items:
            lists.append(list_items)
        
        return lists


def extract_code_blocks(text: str, config: Dict = None) -> List[ExtractedCode]:
    """Extract code blocks"""
    extractor = CodeExtractor(config)
    return extractor.extract_all_code(text)


def extract_sections(text: str, config: Dict = None) -> List[ExtractedSection]:
    """Extract document sections"""
    extractor = SectionExtractor(config)
    return extractor.extract_sections(text)


def extract_paragraphs(text: str, config: Dict = None) -> List[str]:
    """Extract paragraphs"""
    extractor = SectionExtractor(config)
    return extractor.extract_paragraphs(text)


def extract_lists(text: str, config: Dict = None) -> List[List[str]]:
    """Extract lists"""
    extractor = SectionExtractor(config)
    return extractor.extract_lists(text)
