"""
HTML-specific audit checks.
"""

from pathlib import Path
from typing import Dict, Any
from src.utils import logger


def audit_html(file_path: Path) -> Dict[str, Any]:
    """
    Audit an HTML document.
    
    Checks:
    - Content ratio (signal vs boilerplate)
    - Heading hierarchy
    - Table density
    - CSS/JS complexity
    
    Args:
        file_path: Path to HTML
    
    Returns:
        Audit results dict
    """
    file_path = Path(file_path)
    audit = {
        "content_ratio": 0.0,
        "has_heading_hierarchy": False,
        "table_density": 0.0,
        "has_js": False,
        "errors": [],
    }
    
    try:
        import trafilatura
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("trafilatura/BeautifulSoup not installed, HTML audit skipped")
        return audit
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        # Content ratio
        extracted = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=False,
        ) or ""
        
        soup = BeautifulSoup(html_content, "lxml")
        total_text = soup.get_text(separator=" ", strip=True)
        
        if len(total_text) > 0:
            audit["content_ratio"] = round(len(extracted) / len(total_text), 3)
        
        # Heading hierarchy
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if len(headings) >= 2:
            # Check if hierarchy is consistent
            heading_levels = [int(h.name[1]) for h in headings]
            
            # Simple check: if we have H1→H2 or similar progression
            if len(set(heading_levels)) > 1:
                audit["has_heading_hierarchy"] = True
        
        # Table density
        tables = soup.find_all("table")
        if len(tables) > 0 and total_text:
            # Rough estimate: table cells / total words
            table_cells = sum(len(t.find_all("td")) for t in tables)
            audit["table_density"] = round(table_cells / (len(total_text.split()) + 1), 3)
        
        # Check for JavaScript
        scripts = soup.find_all("script")
        audit["has_js"] = len(scripts) > 0
        
        logger.debug(f"HTML audit complete: {file_path.name} → {audit}")
        return audit
    
    except Exception as e:
        audit["errors"].append(str(e))
        logger.warning(f"HTML audit failed: {e}")
        return audit


def compute_content_ratio(file_path: Path) -> float:
    """
    Measure HTML signal-to-noise ratio.
    
    Returns:
        0.0 (pure boilerplate) to 1.0 (pure content)
    """
    try:
        import trafilatura
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("trafilatura/BeautifulSoup not installed")
        return 0.5
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        extracted = trafilatura.extract(html_content) or ""
        soup = BeautifulSoup(html_content, "lxml")
        total_text = soup.get_text(separator=" ", strip=True)
        
        if len(total_text) == 0:
            return 0.0
        
        ratio = len(extracted) / len(total_text)
        logger.debug(f"HTML content ratio: {ratio:.2f}")
        return round(ratio, 3)
    
    except Exception as e:
        logger.warning(f"Content ratio computation failed: {e}")
        return 0.5
