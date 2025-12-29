"""
Module 3: Fact Anchor Extraction
Extracts the most informative sentences from RTI responses for fact-anchored summarization.
"""

import re
from typing import List, Tuple
from collections import Counter


# Fact anchor scoring keywords
FACT_KEYWORDS = {
    # Actions performed
    'actions': [
        'provided', 'processed', 'credited', 'transferred', 'completed',
        'approved', 'sanctioned', 'issued', 'granted', 'received',
        'dispatched', 'forwarded', 'deposited', 'verified', 'confirmed'
    ],
    # Denial indicators
    'denials': [
        'denied', 'rejected', 'cannot be provided', 'not available',
        'exemption', 'section 8', 'confidential', 'not maintained'
    ],
    # Monetary indicators
    'amounts': [
        r'Rs\.?\s*[\d,]+', r'₹\s*[\d,]+', r'INR\s*[\d,]+',
        r'\d+\s*(?:lakh|crore|thousand)', r'amount(?:ing)?\s+(?:of|to)'
    ],
    # Date patterns
    'dates': [
        r'\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}',
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
        r'(?:dated?|on)\s+\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'
    ],
    # Authority references
    'authorities': [
        'ministry', 'department', 'office', 'cpio', 'pio',
        'authority', 'commissioner', 'secretary', 'officer'
    ]
}


def calculate_sentence_score(sentence: str) -> Tuple[float, dict]:
    """
    Calculate a fact-richness score for a sentence.
    
    Args:
        sentence: Single sentence to score
        
    Returns:
        Tuple of (score, details dict with matched patterns)
    """
    sentence_lower = sentence.lower()
    score = 0.0
    details = {
        'actions': [],
        'denials': [],
        'amounts': [],
        'dates': [],
        'authorities': []
    }
    
    # Score action keywords (weight: 2.0)
    for keyword in FACT_KEYWORDS['actions']:
        if keyword in sentence_lower:
            score += 2.0
            details['actions'].append(keyword)
    
    # Score denial keywords (weight: 2.5 - important for RTI)
    for keyword in FACT_KEYWORDS['denials']:
        if keyword in sentence_lower:
            score += 2.5
            details['denials'].append(keyword)
    
    # Score monetary amounts (weight: 3.0 - highly specific)
    for pattern in FACT_KEYWORDS['amounts']:
        matches = re.findall(pattern, sentence, re.IGNORECASE)
        if matches:
            score += 3.0 * len(matches)
            details['amounts'].extend(matches)
    
    # Score dates (weight: 2.5 - specific temporal info)
    for pattern in FACT_KEYWORDS['dates']:
        matches = re.findall(pattern, sentence, re.IGNORECASE)
        if matches:
            score += 2.5 * len(matches)
            details['dates'].extend(matches)
    
    # Score authority references (weight: 1.0)
    for keyword in FACT_KEYWORDS['authorities']:
        if keyword in sentence_lower:
            score += 1.0
            details['authorities'].append(keyword)
    
    # Bonus for sentence length (longer sentences often contain more info)
    word_count = len(sentence.split())
    if 15 <= word_count <= 50:
        score += 1.0
    elif word_count > 50:
        score += 0.5  # Slightly penalize very long sentences
    
    # Penalty for very short sentences
    if word_count < 5:
        score *= 0.5
    
    return score, details


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences for scoring.
    
    Args:
        text: Full RTI response text
        
    Returns:
        List of sentences
    """
    # Handle common abbreviations
    text = re.sub(r'(Mr|Mrs|Dr|Prof|Sr|Jr|vs|etc|i\.e|e\.g)\.', r'\1<DOT>', text)
    text = re.sub(r'([Ss]ec|[Nn]o)\.', r'\1<DOT>', text)
    text = re.sub(r'Rs\.', 'Rs<DOT>', text)
    
    # Split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Restore dots
    sentences = [s.replace('<DOT>', '.') for s in sentences]
    
    # Filter out empty and very short sentences
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    return sentences


def extract_fact_anchors(text: str, top_n: int = 5) -> List[str]:
    """
    Extract the top N most informative sentences as fact anchors.
    
    These sentences contain key facts like dates, amounts, specific actions,
    and outcomes that should anchor the summarization.
    
    Args:
        text: Full cleaned RTI response text
        top_n: Number of fact anchors to extract (default: 5)
        
    Returns:
        List of fact anchor sentences ordered by score
    """
    sentences = split_into_sentences(text)
    
    if not sentences:
        return []
    
    # Score each sentence
    scored_sentences = []
    for sentence in sentences:
        score, details = calculate_sentence_score(sentence)
        scored_sentences.append({
            'sentence': sentence,
            'score': score,
            'details': details
        })
    
    # Sort by score descending
    scored_sentences.sort(key=lambda x: x['score'], reverse=True)
    
    # Get top N, but ensure minimum score threshold
    min_score = 1.0
    fact_anchors = []
    
    for item in scored_sentences[:top_n]:
        if item['score'] >= min_score:
            fact_anchors.append(item['sentence'])
    
    # If no sentences meet threshold, take top 2 anyway
    if not fact_anchors and scored_sentences:
        fact_anchors = [s['sentence'] for s in scored_sentences[:2]]
    
    return fact_anchors


def extract_fact_anchors_with_scores(text: str, top_n: int = 5) -> List[dict]:
    """
    Extract fact anchors with their scores and matched patterns.
    Useful for debugging and transparency.
    
    Args:
        text: Full cleaned RTI response text
        top_n: Number of fact anchors to extract
        
    Returns:
        List of dicts with 'sentence', 'score', and 'details'
    """
    sentences = split_into_sentences(text)
    
    if not sentences:
        return []
    
    scored_sentences = []
    for sentence in sentences:
        score, details = calculate_sentence_score(sentence)
        scored_sentences.append({
            'sentence': sentence,
            'score': score,
            'details': details
        })
    
    scored_sentences.sort(key=lambda x: x['score'], reverse=True)
    
    return scored_sentences[:top_n]


def format_fact_anchors(fact_anchors: List[str]) -> str:
    """
    Format fact anchors as a bulleted list for prompt injection.
    
    Args:
        fact_anchors: List of fact anchor sentences
        
    Returns:
        Formatted string with numbered facts
    """
    if not fact_anchors:
        return "No specific facts extracted."
    
    formatted = []
    for i, anchor in enumerate(fact_anchors, 1):
        formatted.append(f"{i}. {anchor}")
    
    return "\n".join(formatted)


# Test function
if __name__ == "__main__":
    sample_text = """
    Your income tax refund for Assessment Year 2023-24 amounting to Rs. 45,678/- 
    was processed on 25th October, 2024. The refund has been credited to the bank 
    account ending with XXXX1234 as per our records. The processing was completed 
    within the stipulated time frame of 45 days from the date of filing.
    
    The detailed internal notings and file movement records of your case cannot be 
    provided as the disclosure would involve unwarranted invasion of privacy of 
    third party officials involved in the processing. This exemption is claimed 
    under Section 8(1)(j) of the RTI Act, 2005.
    
    With regard to your query about the average processing time for all refund 
    cases in your jurisdiction, we regret to inform that such consolidated 
    statistics are not maintained in the format requested by you.
    """
    
    print("=== FACT ANCHOR EXTRACTION TEST ===\n")
    
    anchors = extract_fact_anchors_with_scores(sample_text)
    for item in anchors:
        print(f"Score: {item['score']:.1f}")
        print(f"Sentence: {item['sentence'][:80]}...")
        print(f"Details: {item['details']}")
        print("-" * 50)
