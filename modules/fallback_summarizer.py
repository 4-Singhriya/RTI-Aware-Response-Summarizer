"""
Local Fallback Summarizer for RTI Response System
Provides extractive summarization when Gemini API is unavailable.
"""

import re
from typing import List, Dict, Tuple
from collections import Counter
import string


# RTI-specific keywords for scoring
RTI_IMPORTANT_KEYWORDS = [
    'provided', 'denied', 'rejected', 'approved', 'processed',
    'transferred', 'forwarded', 'exemption', 'section', 'appeal',
    'information', 'refund', 'amount', 'credited', 'submitted',
    'sanctioned', 'ministry', 'department', 'officer', 'authority'
]


def tokenize(text: str) -> List[str]:
    """Simple word tokenizer."""
    # Remove punctuation except periods
    text = text.lower()
    text = re.sub(r'[^\w\s.]', ' ', text)
    words = text.split()
    return [w for w in words if len(w) > 2]


def get_word_frequencies(text: str) -> Counter:
    """Calculate word frequencies for scoring."""
    words = tokenize(text)
    
    # Remove common stopwords
    stopwords = {
        'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have',
        'has', 'was', 'were', 'been', 'being', 'are', 'you', 'your',
        'our', 'their', 'which', 'would', 'could', 'should', 'may',
        'will', 'can', 'not', 'but', 'also', 'any', 'all', 'such'
    }
    
    filtered = [w for w in words if w not in stopwords]
    return Counter(filtered)


def score_sentence(sentence: str, word_freq: Counter) -> float:
    """
    Score a sentence based on word frequency and RTI keywords.
    
    Args:
        sentence: Sentence to score
        word_freq: Word frequency counter from full text
        
    Returns:
        Sentence score
    """
    words = tokenize(sentence)
    if not words:
        return 0.0
    
    # Base score from word frequencies
    score = sum(word_freq.get(w, 0) for w in words) / len(words)
    
    # Boost for RTI-specific keywords
    sentence_lower = sentence.lower()
    for keyword in RTI_IMPORTANT_KEYWORDS:
        if keyword in sentence_lower:
            score += 2.0
    
    # Boost for amounts and dates
    if re.search(r'Rs\.?\s*[\d,]+', sentence, re.IGNORECASE):
        score += 3.0
    if re.search(r'\d{1,2}(?:st|nd|rd|th)?\s+\w+,?\s+\d{4}', sentence):
        score += 2.0
    
    # Slight penalty for very long sentences
    if len(words) > 40:
        score *= 0.9
    
    return score


def split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Handle abbreviations
    text = re.sub(r'(Mr|Mrs|Dr|Prof|Sr|Jr|vs|etc|i\.e|e\.g|No|Sec|Rs)\.', r'\1<DOT>', text)
    
    # Split on sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Restore dots and filter
    sentences = [s.replace('<DOT>', '.').strip() for s in sentences]
    sentences = [s for s in sentences if len(s) > 20]
    
    return sentences


def extractive_summarize(text: str, num_sentences: int = 3) -> str:
    """
    Perform extractive summarization.
    
    Args:
        text: Full text to summarize
        num_sentences: Number of sentences to extract
        
    Returns:
        Extracted summary
    """
    sentences = split_sentences(text)
    if not sentences:
        return text[:500] if len(text) > 500 else text
    
    word_freq = get_word_frequencies(text)
    
    # Score all sentences
    scored = [(s, score_sentence(s, word_freq)) for s in sentences]
    
    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Get top sentences
    top_sentences = [s for s, _ in scored[:num_sentences]]
    
    # Reorder by original position for coherence
    ordered = []
    for s in sentences:
        if s in top_sentences:
            ordered.append(s)
    
    return ' '.join(ordered)


def fallback_ultra_short(text: str) -> str:
    """
    Generate ultra-short summary (1-2 sentences) using local extraction.
    
    Args:
        text: Full RTI response text
        
    Returns:
        Ultra-short summary
    """
    summary = extractive_summarize(text, num_sentences=2)
    
    # Add prefix to indicate it's a local summary
    return summary


def fallback_citizen_summary(text: str) -> str:
    """
    Generate citizen-friendly summary using local extraction.
    
    Args:
        text: Full RTI response text
        
    Returns:
        Citizen-friendly summary (3-5 sentences)
    """
    summary = extractive_summarize(text, num_sentences=4)
    
    # Try to simplify slightly
    summary = summary.replace('herewith', 'here')
    summary = summary.replace('aforementioned', 'mentioned above')
    summary = summary.replace('vide', 'by')
    
    return summary


def fallback_technical_summary(text: str) -> str:
    """
    Generate technical/legal summary using structured extraction.
    
    Args:
        text: Full RTI response text
        
    Returns:
        Technical summary with structure
    """
    sentences = split_sentences(text)
    word_freq = get_word_frequencies(text)
    
    # Categorize sentences
    informative = []
    denied = []
    procedural = []
    
    denial_keywords = ['denied', 'rejected', 'cannot', 'exemption', 'section 8', 'not available']
    procedural_keywords = ['transferred', 'forwarded', 'fee', 'appeal', 'days', 'applicant']
    
    for s in sentences:
        s_lower = s.lower()
        if any(k in s_lower for k in denial_keywords):
            denied.append(s)
        elif any(k in s_lower for k in procedural_keywords):
            procedural.append(s)
        else:
            score = score_sentence(s, word_freq)
            if score > 3:
                informative.append((s, score))
    
    # Build structured summary
    parts = []
    
    if informative:
        informative.sort(key=lambda x: x[1], reverse=True)
        top_info = [s for s, _ in informative[:3]]
        parts.append("INFORMATION PROVIDED: " + ' '.join(top_info))
    
    if denied:
        parts.append("INFORMATION DENIED: " + ' '.join(denied[:2]))
    
    if procedural:
        parts.append("PROCEDURAL NOTES: " + ' '.join(procedural[:2]))
    
    if not parts:
        return extractive_summarize(text, num_sentences=5)
    
    return '\n\n'.join(parts)


class FallbackSummarizer:
    """
    Fallback summarizer class for integration with main summarizer.
    """
    
    def __init__(self):
        self.source = "local_fallback"
    
    def generate_ultra_short(self, text: str) -> Dict:
        """Generate ultra-short summary with metadata."""
        return {
            'text': fallback_ultra_short(text),
            'source': self.source,
            'method': 'extractive'
        }
    
    def generate_citizen_summary(self, text: str) -> Dict:
        """Generate citizen-friendly summary with metadata."""
        return {
            'text': fallback_citizen_summary(text),
            'source': self.source,
            'method': 'extractive'
        }
    
    def generate_technical_summary(self, text: str) -> Dict:
        """Generate technical summary with metadata."""
        return {
            'text': fallback_technical_summary(text),
            'source': self.source,
            'method': 'extractive_structured'
        }


# Test
if __name__ == "__main__":
    sample = """
    Your income tax refund for Assessment Year 2023-24 amounting to Rs. 45,678/- 
    was processed on 25th October, 2024. The refund has been credited to the bank 
    account ending with XXXX1234 as per our records.
    
    The detailed internal notings and file movement records of your case cannot be 
    provided as the disclosure would involve unwarranted invasion of privacy. 
    This exemption is claimed under Section 8(1)(j) of the RTI Act, 2005.
    
    If you are not satisfied with this reply, you may file a First Appeal with 
    the First Appellate Authority within 30 days from the receipt of this letter.
    """
    
    print("=== FALLBACK SUMMARIZER TEST ===\n")
    
    print("Ultra-Short:")
    print(fallback_ultra_short(sample))
    print("\n" + "-"*50 + "\n")
    
    print("Citizen-Friendly:")
    print(fallback_citizen_summary(sample))
    print("\n" + "-"*50 + "\n")
    
    print("Technical:")
    print(fallback_technical_summary(sample))
