"""
Blog 3: Format-Specific Cleaners

Remove markup, normalize spacing, and handle encoding issues
specific to each document format.
"""

import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FormatCleaner:
    """Base class for format-specific cleaning"""

    def clean(self, text: str, format_type: str) -> str:
        """
        Apply format-specific cleaning.
        
        Args:
            text: Text to clean
            format_type: one of pdf, html, json, csv, txt, md, py
            
        Returns:
            Cleaned text
        """
        if format_type == "pdf":
            return self.clean_pdf(text)
        elif format_type == "html":
            return self.clean_html(text)
        elif format_type == "json":
            return self.clean_json(text)
        elif format_type == "csv":
            return self.clean_csv(text)
        elif format_type == "md":
            return self.clean_markdown(text)
        elif format_type == "py":
            return self.clean_python(text)
        else:
            return self.clean_generic(text)

    @staticmethod
    def clean_pdf(text: str) -> str:
        """Clean extracted PDF text"""
        # Remove page break markers
        text = re.sub(r'\[PAGE_BREAK\]|\n---\n|\f', '\n\n', text)
        
        # Fix broken words at line breaks (common in PDFs)
        text = re.sub(r'([a-z])\s*\n\s*([a-z])', r'\1\2', text)
        
        # Remove repetitive footer/header text
        lines = text.split('\n')
        cleaned_lines = []
        prev_line = ""
        
        for line in lines:
            # Skip if identical to previous line (likely header/footer repetition)
            if line.strip() and line.strip() != prev_line:
                cleaned_lines.append(line)
                prev_line = line.strip()
        
        text = '\n'.join(cleaned_lines)
        
        # Normalize whitespace
        return FormatCleaner._normalize_whitespace(text)

    @staticmethod
    def clean_html(text: str) -> str:
        """Clean extracted HTML text"""
        # Remove HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        
        # Remove HTML tags that might remain
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove common HTML boilerplate
        text = re.sub(r'skip to (main )?content', '', text, flags=re.IGNORECASE)
        text = re.sub(r'javascript|script', '', text, flags=re.IGNORECASE)
        
        # Remove multiple spaces from HTML rendering
        text = re.sub(r' {2,}', ' ', text)
        
        # Normalize whitespace
        return FormatCleaner._normalize_whitespace(text)

    @staticmethod
    def clean_json(text: str) -> str:
        """Clean flattened JSON text"""
        # JSON is already flattened, just normalize
        lines = text.split('\n')
        cleaned = []
        
        for line in lines:
            # Remove lines that are just keys with empty values
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2 and parts[1].strip():
                    cleaned.append(line)
            elif line.strip():
                cleaned.append(line)
        
        return '\n'.join(cleaned)

    @staticmethod
    def clean_csv(text: str) -> str:
        """Clean CSV preview text"""
        # CSV is already a preview, minimal cleaning needed
        # Just remove excessive empty lines
        lines = text.split('\n')
        cleaned = [line for line in lines if line.strip()]
        return '\n'.join(cleaned)

    @staticmethod
    def clean_markdown(text: str) -> str:
        """Clean Markdown text"""
        # Normalize markdown heading levels
        text = re.sub(r'^#{7,}', '###', text, flags=re.MULTILINE)
        
        # Remove zero-width characters
        text = text.replace('\u200b', '')  # Zero-width space
        text = text.replace('\u200c', '')  # Zero-width non-joiner
        text = text.replace('\u200d', '')  # Zero-width joiner
        
        # Normalize emphasis markers
        text = re.sub(r'\*{3,}', '**', text)  # Multiple asterisks to double
        text = re.sub(r'_{3,}', '__', text)   # Multiple underscores to double
        
        # Normalize whitespace
        return FormatCleaner._normalize_whitespace(text)

    @staticmethod
    def clean_python(text: str) -> str:
        """Clean Python code text"""
        # Normalize indentation to 4 spaces
        lines = text.split('\n')
        cleaned = []
        
        for line in lines:
            # Convert tabs to spaces
            line = line.replace('\t', '    ')
            
            # Remove trailing whitespace
            line = line.rstrip()
            
            cleaned.append(line)
        
        # Remove multiple blank lines
        result = []
        blank_count = 0
        
        for line in cleaned:
            if not line.strip():
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        
        return '\n'.join(result)

    @staticmethod
    def clean_generic(text: str) -> str:
        """Generic text cleaning"""
        return FormatCleaner._normalize_whitespace(text)

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalize whitespace across all formats"""
        # Fix line endings
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        # Remove multiple consecutive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Fix spacing around punctuation
        text = re.sub(r' +([.,!?;:])', r'\1', text)
        
        return text


class NoiseCleaner:
    """Remove encoding and noise artifacts"""

    @staticmethod
    def fix_encoding_issues(text: str) -> str:
        """Fix common encoding problems"""
        # Fix smart quotes encoded wrong
        text = text.replace('â€™', "'")      # UTF-8 encoded '
        text = text.replace('â€œ', '"')      # UTF-8 encoded "
        text = text.replace('â€\x9d', '"')   # UTF-8 encoded close quote
        text = text.replace('â€\x9c', '"')   # UTF-8 encoded open quote
        
        # Fix non-breaking spaces
        text = text.replace('\xa0', ' ')
        text = text.replace('\u00a0', ' ')
        
        # Fix em dashes and en dashes
        text = text.replace('\u2014', ' - ')  # Em dash
        text = text.replace('\u2013', '-')    # En dash
        
        return text

    @staticmethod
    def remove_control_characters(text: str) -> str:
        """Remove problematic control characters"""
        # Keep only printable characters and whitespace
        cleaned = []
        
        for char in text:
            code = ord(char)
            # Keep printable ASCII, newline, tab, and high unicode
            if (32 <= code <= 126 or  # Printable ASCII
                code in (9, 10, 13) or  # Tab, newline, carriage return
                code > 127):  # High unicode (keep accented chars, etc.)
                cleaned.append(char)
        
        return ''.join(cleaned)

    @staticmethod
    def remove_excessive_punctuation(text: str) -> str:
        """Remove excessive punctuation and symbols"""
        # Remove repeated punctuation
        text = re.sub(r'[!?]{2,}', '!', text)      # Multiple !! → !
        text = re.sub(r'\.{2,}(?!\.{3})', '.', text)  # Multiple .. → .
        text = re.sub(r'-{2,}', '-', text)        # Multiple -- → -
        
        # Remove lines that are mostly special characters (likely noise)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Count special characters
            special_count = sum(1 for c in line if not c.isalnum() and not c.isspace())
            if special_count / max(len(line), 1) < 0.5:  # Less than 50% special chars
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)


def clean_text(text: str, format_type: str = "txt") -> str:
    """
    Apply comprehensive text cleaning.
    
    Args:
        text: Text to clean
        format_type: Document format (pdf, html, json, csv, txt, md, py)
        
    Returns:
        Cleaned text
    """
    # Step 1: Fix encoding issues
    text = NoiseCleaner.fix_encoding_issues(text)
    
    # Step 2: Remove control characters
    text = NoiseCleaner.remove_control_characters(text)
    
    # Step 3: Format-specific cleaning
    cleaner = FormatCleaner()
    text = cleaner.clean(text, format_type)
    
    # Step 4: Remove excessive punctuation
    text = NoiseCleaner.remove_excessive_punctuation(text)
    
    return text
