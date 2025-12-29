"""
Helper utility functions for RTI Response Summarization System
"""

import re
from datetime import datetime


def clean_whitespace(text: str) -> str:
    """Remove excessive whitespace while preserving paragraph structure."""
    # Replace multiple spaces with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def remove_page_numbers(text: str) -> str:
    """Remove common page number patterns."""
    patterns = [
        r'Page\s*\d+\s*of\s*\d+',
        r'Page\s*-?\s*\d+\s*-?',
        r'^\s*\d+\s*$',
        r'-\s*\d+\s*-',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
    return text


def remove_headers_footers(text: str) -> str:
    """Remove common header/footer patterns from RTI documents."""
    patterns = [
        r'(?i)government\s+of\s+india.*?\n',
        r'(?i)right\s+to\s+information\s+act.*?\n',
        r'(?i)office\s+of\s+the\s+.*?\n',
        r'(?i)ministry\s+of\s+.*?\n',
        r'(?i)file\s+no\.?\s*:?\s*[\w/-]+',
        r'(?i)dated?\s*:?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '\n', text)
    return text


def split_into_sentences(text: str) -> list:
    """Split text into sentences for classification."""
    # Split on common sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter out empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def format_date(date_str: str = None) -> str:
    """Format date for display."""
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d %B %Y")
        except:
            return date_str
    return datetime.now().strftime("%d %B %Y")


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'


def highlight_keywords(text: str, keywords: list, color: str) -> str:
    """Wrap keywords in HTML span with color for highlighting."""
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        text = pattern.sub(
            f'<span style="background-color: {color}; padding: 2px 4px; border-radius: 3px;">{keyword}</span>',
            text
        )
    return text


def export_to_text(data: dict) -> str:
    """Export summary data to plain text format."""
    lines = [
        "=" * 60,
        "RTI RESPONSE SUMMARY REPORT",
        f"Generated: {format_date()}",
        "=" * 60,
        "",
        "ULTRA-SHORT SUMMARY",
        "-" * 40,
        data.get('ultra_short', 'N/A'),
        "",
        "CITIZEN-FRIENDLY SUMMARY",
        "-" * 40,
        data.get('citizen_friendly', 'N/A'),
        "",
        "TECHNICAL/LEGAL SUMMARY",
        "-" * 40,
        data.get('technical', 'N/A'),
        "",
        "SUGGESTED ACTIONS",
        "-" * 40,
    ]
    
    actions = data.get('actions', [])
    for i, action in enumerate(actions, 1):
        lines.append(f"{i}. {action}")
    
    lines.extend([
        "",
        "=" * 60,
        "End of Report",
        "=" * 60,
    ])
    
    return '\n'.join(lines)
