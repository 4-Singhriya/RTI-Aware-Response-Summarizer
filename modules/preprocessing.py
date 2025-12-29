"""
Module 1: Backend & Preprocessing
Handles PDF text extraction and text cleaning for RTI documents.
"""

import re
import io
from typing import Union, Optional

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not installed. PDF extraction will not work.")


def extract_text_from_pdf(pdf_file: Union[bytes, io.BytesIO]) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_file: PDF file as bytes or BytesIO object
        
    Returns:
        Extracted text content as string
    """
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF is required for PDF extraction. Install with: pip install pymupdf")
    
    # Handle BytesIO or bytes
    if isinstance(pdf_file, io.BytesIO):
        pdf_bytes = pdf_file.read()
        pdf_file.seek(0)  # Reset for potential re-reading
    else:
        pdf_bytes = pdf_file
    
    # Open PDF from bytes
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    text_content = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        text_content.append(text)
    
    doc.close()
    
    return '\n\n'.join(text_content)


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing noise, headers, footers, and artifacts.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove common PDF artifacts
    text = re.sub(r'\x00', '', text)  # Null characters
    text = re.sub(r'\f', '\n', text)  # Form feeds
    
    # Remove page numbers
    text = re.sub(r'(?i)page\s*\d+\s*(of\s*\d+)?', '', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'-\s*\d+\s*-', '', text)
    
    # Remove common header/footer patterns in RTI documents
    header_patterns = [
        r'(?i)government\s+of\s+india',
        r'(?i)भारत\s+सरकार',  # Hindi header
        r'(?i)right\s+to\s+information',
        r'(?i)public\s+information\s+officer',
        r'(?i)central\s+public\s+information\s+officer',
        r'(?i)^\s*cpio\s*$',
        r'(?i)^\s*pio\s*$',
    ]
    
    for pattern in header_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE)
    
    # Remove file numbers and dates from headers
    text = re.sub(r'(?i)file\s*no\.?\s*:?\s*[\w/-]+', '', text)
    text = re.sub(r'(?i)ref\.?\s*no\.?\s*:?\s*[\w/-]+', '', text)
    text = re.sub(r'(?i)dated?\s*:?\s*\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}', '', text)
    
    # Remove email addresses and URLs (often in headers/footers)
    text = re.sub(r'\S+@\S+\.\S+', '', text)
    text = re.sub(r'(?i)https?://\S+', '', text)
    
    # Remove phone/fax numbers
    text = re.sub(r'(?i)(tel|fax|phone)\.?\s*:?\s*[\d\s+-]+', '', text)
    
    return text


def normalize_text(text: str) -> str:
    """
    Normalize text formatting for consistent processing.
    
    Args:
        text: Cleaned text
        
    Returns:
        Normalized text with consistent spacing and formatting
    """
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks
    
    # Fix common OCR/extraction issues
    text = re.sub(r'(\w)\s*-\s*\n\s*(\w)', r'\1\2', text)  # Rejoin hyphenated words
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Normalize section references
    text = re.sub(r'[Ss]ec\.\s*', 'Section ', text)
    text = re.sub(r'[Ss]ection\s+', 'Section ', text)
    
    # Clean up excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def preprocess_pipeline(input_source: Union[str, bytes, io.BytesIO], is_pdf: bool = False) -> str:
    """
    Main preprocessing pipeline that handles both PDF and text input.
    
    Args:
        input_source: Either raw text string or PDF file (bytes/BytesIO)
        is_pdf: Whether the input is a PDF file
        
    Returns:
        Cleaned and normalized RTI response text
    """
    if is_pdf:
        # Extract text from PDF
        raw_text = extract_text_from_pdf(input_source)
    else:
        # Input is already text
        raw_text = input_source if isinstance(input_source, str) else input_source.decode('utf-8')
    
    # Apply cleaning pipeline
    cleaned_text = clean_text(raw_text)
    normalized_text = normalize_text(cleaned_text)
    
    return normalized_text


def get_text_stats(text: str) -> dict:
    """
    Get statistics about the processed text.
    
    Args:
        text: Processed text
        
    Returns:
        Dictionary with text statistics
    """
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    
    return {
        'character_count': len(text),
        'word_count': len(words),
        'sentence_count': len([s for s in sentences if s.strip()]),
        'paragraph_count': len(paragraphs),
    }
