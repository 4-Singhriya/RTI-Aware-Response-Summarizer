"""
Module 4: Summarization using Gemini API with Fact-Anchored Prompting
Generates multi-level summaries from RTI responses using fact anchors + full text.

CRITICAL DESIGN RULE: Classification is for UI/stats ONLY.
Summarization always uses full cleaned text + fact anchors.
"""

import os
import sys
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import google.generativeai as genai
from config import (
    GEMINI_API_KEY, GEMINI_MODEL, MAX_CHUNK_SIZE,
    ENABLE_LOCAL_FALLBACK, FALLBACK_MODE, LOG_QUOTA_FAILURES
)
from modules.fact_extractor import extract_fact_anchors, format_fact_anchors
from modules.fallback_summarizer import FallbackSummarizer
from utils.logger import log_quota_failure, log_fallback_activation, log_api_success


@dataclass
class SummaryResult:
    """Result of summarization with metadata."""
    text: str
    source: str  # "gemini" or "local_fallback"
    timestamp: str
    summary_type: str
    

def setup_gemini(api_key: str = None) -> bool:
    """
    Initialize the Gemini API client.
    
    Args:
        api_key: Optional API key (uses config if not provided)
        
    Returns:
        True if setup successful, False otherwise
    """
    key = api_key or GEMINI_API_KEY
    if not key:
        return False
    
    genai.configure(api_key=key)
    return True


def get_model():
    """Get the Gemini model instance."""
    return genai.GenerativeModel(GEMINI_MODEL)


def chunk_text(text: str, max_size: int = MAX_CHUNK_SIZE) -> List[str]:
    """
    Split long text into chunks for processing.
    
    Args:
        text: Text to split
        max_size: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_size:
        return [text]
    
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_size:
            current_chunk += para + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + '\n\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


# ============================================================================
# FACT-ANCHORED PROMPT TEMPLATES
# These prompts use {fact_anchors} + {full_text} to prevent generic summaries
# ============================================================================

ULTRA_SHORT_PROMPT = """You are summarizing an RTI response.

Task:
- State what INFORMATION was actually provided by the public authority.
- Mention key activities, dates, locations, and outcomes.
- If procedural or appeal-related information exists, mention it briefly at the end.
- Do NOT generate generic explanations.
- Do NOT repeat template phrases.
- Base the summary strictly on the content provided.

Key Facts:
{fact_anchors}

Full RTI Response:
{full_text}

ULTRA-SHORT SUMMARY (1-2 sentences only):"""


CITIZEN_FRIENDLY_PROMPT = """Explain the RTI response in simple English for a common citizen.

Clearly explain:
- What work or information was shared
- When and where it happened
- Which authority provided the information
- What the applicant can do next (only if appeal is mentioned)

Avoid legal jargon unless necessary.
Avoid generic procedural descriptions.
Use facts from the response.

Key Facts:
{fact_anchors}

Full RTI Response:
{full_text}

CITIZEN-FRIENDLY SUMMARY (3-5 sentences):"""


TECHNICAL_LEGAL_PROMPT = """Provide a formal RTI-style summary.

Include:
- Actions taken by the public authority
- Relevant dates, scope, and subject matter
- Procedural rights such as appeal, if explicitly mentioned

Do NOT assume denial unless stated.
Do NOT produce generic procedural summaries.

Key Facts:
{fact_anchors}

Full RTI Response:
{full_text}

TECHNICAL/LEGAL SUMMARY:"""


# Initialize fallback summarizer
_fallback = FallbackSummarizer()


def _is_quota_error(error: Exception) -> bool:
    """Check if an error is a quota/rate limit error."""
    error_str = str(error).lower()
    return any(x in error_str for x in ['429', 'quota', 'rate limit', 'resource exhausted'])


def generate_ultra_short_summary(
    full_text: str, 
    api_key: str = None,
    fact_anchors: List[str] = None
) -> SummaryResult:
    """
    Generate an ultra-short (1-2 sentences) summary.
    
    Args:
        full_text: Full cleaned RTI response text (NOT filtered by classification)
        api_key: Optional Gemini API key
        fact_anchors: Pre-extracted fact anchors (extracted if not provided)
        
    Returns:
        SummaryResult with text and metadata
    """
    # Extract fact anchors if not provided
    if fact_anchors is None:
        fact_anchors = extract_fact_anchors(full_text)
    
    formatted_anchors = format_fact_anchors(fact_anchors)
    timestamp = datetime.now().isoformat()
    
    # Check fallback mode
    if FALLBACK_MODE == "local_only":
        result = _fallback.generate_ultra_short(full_text)
        return SummaryResult(
            text=result['text'],
            source="local_fallback",
            timestamp=timestamp,
            summary_type="ultra_short"
        )
    
    # Try Gemini API
    if not setup_gemini(api_key):
        if ENABLE_LOCAL_FALLBACK:
            log_fallback_activation("API key not configured", "ultra_short")
            result = _fallback.generate_ultra_short(full_text)
            return SummaryResult(
                text=result['text'],
                source="local_fallback",
                timestamp=timestamp,
                summary_type="ultra_short"
            )
        return SummaryResult(
            text="Error: Gemini API key not configured.",
            source="error",
            timestamp=timestamp,
            summary_type="ultra_short"
        )
    
    try:
        model = get_model()
        prompt = ULTRA_SHORT_PROMPT.format(
            fact_anchors=formatted_anchors,
            full_text=full_text[:MAX_CHUNK_SIZE]  # Truncate if too long
        )
        response = model.generate_content(prompt)
        
        if LOG_QUOTA_FAILURES:
            log_api_success("gemini", "ultra_short")
        
        return SummaryResult(
            text=response.text.strip(),
            source="gemini",
            timestamp=timestamp,
            summary_type="ultra_short"
        )
    except Exception as e:
        if _is_quota_error(e) and ENABLE_LOCAL_FALLBACK:
            if LOG_QUOTA_FAILURES:
                log_quota_failure(
                    error_type="429" if "429" in str(e) else "quota_error",
                    error_message=str(e),
                    endpoint="gemini",
                    context={"summary_type": "ultra_short"},
                    fallback_used=True
                )
            log_fallback_activation(str(e)[:100], "ultra_short")
            result = _fallback.generate_ultra_short(full_text)
            return SummaryResult(
                text=result['text'],
                source="local_fallback",
                timestamp=timestamp,
                summary_type="ultra_short"
            )
        
        return SummaryResult(
            text=f"Error generating summary: {str(e)}",
            source="error",
            timestamp=timestamp,
            summary_type="ultra_short"
        )


def generate_citizen_summary(
    full_text: str, 
    api_key: str = None,
    fact_anchors: List[str] = None
) -> SummaryResult:
    """
    Generate a citizen-friendly summary in simple language.
    
    Args:
        full_text: Full cleaned RTI response text
        api_key: Optional Gemini API key
        fact_anchors: Pre-extracted fact anchors
        
    Returns:
        SummaryResult with text and metadata
    """
    if fact_anchors is None:
        fact_anchors = extract_fact_anchors(full_text)
    
    formatted_anchors = format_fact_anchors(fact_anchors)
    timestamp = datetime.now().isoformat()
    
    if FALLBACK_MODE == "local_only":
        result = _fallback.generate_citizen_summary(full_text)
        return SummaryResult(
            text=result['text'],
            source="local_fallback",
            timestamp=timestamp,
            summary_type="citizen_friendly"
        )
    
    if not setup_gemini(api_key):
        if ENABLE_LOCAL_FALLBACK:
            log_fallback_activation("API key not configured", "citizen_friendly")
            result = _fallback.generate_citizen_summary(full_text)
            return SummaryResult(
                text=result['text'],
                source="local_fallback",
                timestamp=timestamp,
                summary_type="citizen_friendly"
            )
        return SummaryResult(
            text="Error: Gemini API key not configured.",
            source="error",
            timestamp=timestamp,
            summary_type="citizen_friendly"
        )
    
    try:
        model = get_model()
        prompt = CITIZEN_FRIENDLY_PROMPT.format(
            fact_anchors=formatted_anchors,
            full_text=full_text[:MAX_CHUNK_SIZE]
        )
        response = model.generate_content(prompt)
        
        if LOG_QUOTA_FAILURES:
            log_api_success("gemini", "citizen_friendly")
        
        return SummaryResult(
            text=response.text.strip(),
            source="gemini",
            timestamp=timestamp,
            summary_type="citizen_friendly"
        )
    except Exception as e:
        if _is_quota_error(e) and ENABLE_LOCAL_FALLBACK:
            if LOG_QUOTA_FAILURES:
                log_quota_failure(
                    error_type="429" if "429" in str(e) else "quota_error",
                    error_message=str(e),
                    context={"summary_type": "citizen_friendly"},
                    fallback_used=True
                )
            log_fallback_activation(str(e)[:100], "citizen_friendly")
            result = _fallback.generate_citizen_summary(full_text)
            return SummaryResult(
                text=result['text'],
                source="local_fallback",
                timestamp=timestamp,
                summary_type="citizen_friendly"
            )
        
        return SummaryResult(
            text=f"Error generating summary: {str(e)}",
            source="error",
            timestamp=timestamp,
            summary_type="citizen_friendly"
        )


def generate_technical_summary(
    full_text: str, 
    api_key: str = None,
    fact_anchors: List[str] = None
) -> SummaryResult:
    """
    Generate a technical/legal summary for official purposes.
    
    Args:
        full_text: Full cleaned RTI response text
        api_key: Optional Gemini API key
        fact_anchors: Pre-extracted fact anchors
        
    Returns:
        SummaryResult with text and metadata
    """
    if fact_anchors is None:
        fact_anchors = extract_fact_anchors(full_text)
    
    formatted_anchors = format_fact_anchors(fact_anchors)
    timestamp = datetime.now().isoformat()
    
    if FALLBACK_MODE == "local_only":
        result = _fallback.generate_technical_summary(full_text)
        return SummaryResult(
            text=result['text'],
            source="local_fallback",
            timestamp=timestamp,
            summary_type="technical"
        )
    
    if not setup_gemini(api_key):
        if ENABLE_LOCAL_FALLBACK:
            log_fallback_activation("API key not configured", "technical")
            result = _fallback.generate_technical_summary(full_text)
            return SummaryResult(
                text=result['text'],
                source="local_fallback",
                timestamp=timestamp,
                summary_type="technical"
            )
        return SummaryResult(
            text="Error: Gemini API key not configured.",
            source="error",
            timestamp=timestamp,
            summary_type="technical"
        )
    
    try:
        model = get_model()
        prompt = TECHNICAL_LEGAL_PROMPT.format(
            fact_anchors=formatted_anchors,
            full_text=full_text[:MAX_CHUNK_SIZE]
        )
        response = model.generate_content(prompt)
        
        if LOG_QUOTA_FAILURES:
            log_api_success("gemini", "technical")
        
        return SummaryResult(
            text=response.text.strip(),
            source="gemini",
            timestamp=timestamp,
            summary_type="technical"
        )
    except Exception as e:
        if _is_quota_error(e) and ENABLE_LOCAL_FALLBACK:
            if LOG_QUOTA_FAILURES:
                log_quota_failure(
                    error_type="429" if "429" in str(e) else "quota_error",
                    error_message=str(e),
                    context={"summary_type": "technical"},
                    fallback_used=True
                )
            log_fallback_activation(str(e)[:100], "technical")
            result = _fallback.generate_technical_summary(full_text)
            return SummaryResult(
                text=result['text'],
                source="local_fallback",
                timestamp=timestamp,
                summary_type="technical"
            )
        
        return SummaryResult(
            text=f"Error generating summary: {str(e)}",
            source="error",
            timestamp=timestamp,
            summary_type="technical"
        )


def summarize_all(
    full_text: str, 
    api_key: str = None
) -> Dict[str, SummaryResult]:
    """
    Generate all three types of summaries.
    
    Args:
        full_text: Full cleaned RTI response text
        api_key: Optional Gemini API key
        
    Returns:
        Dictionary with all three SummaryResults
    """
    # Extract fact anchors once for all summaries
    fact_anchors = extract_fact_anchors(full_text)
    
    return {
        'ultra_short': generate_ultra_short_summary(full_text, api_key, fact_anchors),
        'citizen_friendly': generate_citizen_summary(full_text, api_key, fact_anchors),
        'technical': generate_technical_summary(full_text, api_key, fact_anchors)
    }


def test_connection(api_key: str = None) -> bool:
    """
    Test if Gemini API connection works.
    
    Args:
        api_key: Optional API key to test
        
    Returns:
        True if connection successful
    """
    try:
        if not setup_gemini(api_key):
            return False
        model = get_model()
        response = model.generate_content("Say 'Hello' in one word.")
        return len(response.text) > 0
    except Exception:
        return False
