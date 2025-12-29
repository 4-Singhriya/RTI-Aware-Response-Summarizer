"""
Module 4: Actionability Layer
Suggests next steps based on RTI response analysis.
"""

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.rti_semantic import StructuredRTIResponse


class ActionType(Enum):
    """Types of suggested actions."""
    FIRST_APPEAL = "first_appeal"
    SECOND_APPEAL = "second_appeal"
    CLARIFICATION = "clarification"
    COMPLAINT = "complaint"
    NO_ACTION = "no_action"
    WAIT = "wait"
    PAY_FEE = "pay_fee"


@dataclass
class ActionSuggestion:
    """A suggested action for the citizen."""
    action_type: ActionType
    priority: str  # high, medium, low
    title: str
    description: str
    deadline: str = None
    reference: str = None


def suggest_next_steps(structured: StructuredRTIResponse) -> List[ActionSuggestion]:
    """
    Analyze structured RTI response and suggest next steps.
    
    Args:
        structured: Structured RTI response from semantic processing
        
    Returns:
        List of ActionSuggestion objects
    """
    suggestions = []
    stats = structured.get_stats()
    
    # Rule 1: High denial ratio - suggest First Appeal
    if stats['denial_ratio'] > 0.3 or stats['denial_count'] >= 2:
        suggestions.append(ActionSuggestion(
            action_type=ActionType.FIRST_APPEAL,
            priority="high",
            title="File First Appeal",
            description=(
                "Significant information has been denied. You can file a First Appeal "
                "with the First Appellate Authority within 30 days of receiving this response. "
                "Under Section 19(1) of RTI Act, you have the right to appeal against denial."
            ),
            deadline="30 days from receipt of response",
            reference="Section 19(1) of RTI Act, 2005"
        ))
    
    # Rule 2: Evasive responses - suggest clarification or complaint
    if stats['evasive_count'] >= 2 or (stats['evasive_count'] > 0 and stats['informative_count'] == 0):
        suggestions.append(ActionSuggestion(
            action_type=ActionType.CLARIFICATION,
            priority="high",
            title="Request Clarification",
            description=(
                "The response contains vague or evasive statements that don't adequately "
                "answer your query. You can write to the PIO requesting specific clarification "
                "or file an appeal citing inadequate response."
            ),
            reference="Section 7(8) of RTI Act, 2005"
        ))
    
    # Rule 3: Section 8 exemptions cited - suggest appeal with grounds
    if 'section_8' in structured.section_references:
        suggestions.append(ActionSuggestion(
            action_type=ActionType.FIRST_APPEAL,
            priority="high",
            title="Challenge Exemption Claim",
            description=(
                "The PIO has cited Section 8 exemptions to deny information. You can file an appeal "
                "challenging whether the exemption genuinely applies. The burden is on the PIO to "
                "prove that the exemption is justified."
            ),
            deadline="30 days from receipt",
            reference="Section 8, Section 19 of RTI Act, 2005"
        ))
    
    # Rule 4: Procedural issues (fee, transfer)
    if stats['procedural_count'] > 0:
        # Check for fee-related content
        procedural_texts = ' '.join([s.text.lower() for s in structured.procedural_sentences])
        
        if 'fee' in procedural_texts or 'deposit' in procedural_texts or 'payment' in procedural_texts:
            suggestions.append(ActionSuggestion(
                action_type=ActionType.PAY_FEE,
                priority="medium",
                title="Pay Additional Fee",
                description=(
                    "The PIO has requested additional fees. Pay the fee within the specified "
                    "timeline to receive the information. Keep the receipt as proof."
                ),
                reference="Section 7 of RTI Act, 2005"
            ))
        
        if 'transfer' in procedural_texts or 'forward' in procedural_texts:
            suggestions.append(ActionSuggestion(
                action_type=ActionType.WAIT,
                priority="low",
                title="Application Transferred",
                description=(
                    "Your application has been transferred to another department. "
                    "Wait for a response from the concerned PIO. The transfer should not "
                    "reset your timeline."
                ),
                reference="Section 6(3) of RTI Act, 2005"
            ))
    
    # Rule 5: Good response - no action needed
    if stats['informative_ratio'] > 0.6 and stats['denial_count'] == 0:
        suggestions.append(ActionSuggestion(
            action_type=ActionType.NO_ACTION,
            priority="low",
            title="Response Complete",
            description=(
                "The RTI response appears to adequately address your query. "
                "No further action is required unless you find the information incomplete."
            )
        ))
    
    # Rule 6: If no clear action, suggest review
    if not suggestions:
        suggestions.append(ActionSuggestion(
            action_type=ActionType.NO_ACTION,
            priority="low",
            title="Review Response Carefully",
            description=(
                "Review the response to determine if all your queries have been addressed. "
                "If unsatisfied, you may file a First Appeal within 30 days."
            ),
            deadline="30 days if appeal needed",
            reference="Section 19 of RTI Act, 2005"
        ))
    
    # Sort by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    suggestions.sort(key=lambda x: priority_order.get(x.priority, 3))
    
    return suggestions


def check_appeal_eligibility(structured: StructuredRTIResponse) -> Dict[str, any]:
    """
    Check if the response qualifies for appeal.
    
    Args:
        structured: Structured RTI response
        
    Returns:
        Dictionary with appeal eligibility details
    """
    stats = structured.get_stats()
    
    reasons = []
    
    # Check for denial
    if stats['denial_count'] > 0:
        reasons.append("Information was denied")
    
    # Check for Section 8 exemptions
    if 'section_8' in structured.section_references:
        reasons.append("Section 8 exemptions were cited")
    
    # Check for evasive responses
    if stats['evasive_count'] > 0:
        reasons.append("Response contains evasive/unclear statements")
    
    # Check for inadequate response
    if stats['informative_count'] == 0 and stats['neutral_count'] > 3:
        reasons.append("Response does not adequately address the query")
    
    return {
        'eligible': len(reasons) > 0,
        'reasons': reasons,
        'appeal_type': 'First Appeal under Section 19(1)',
        'deadline': '30 days from receipt of response',
        'authority': 'First Appellate Authority (FAA)'
    }


def flag_evasive_responses(structured: StructuredRTIResponse) -> List[Dict]:
    """
    Identify and flag evasive or problematic responses.
    
    Args:
        structured: Structured RTI response
        
    Returns:
        List of flagged issues
    """
    flags = []
    
    # Flag evasive sentences
    for sentence in structured.evasive_sentences:
        flags.append({
            'type': 'evasive',
            'severity': 'medium',
            'text': sentence.text,
            'reason': 'Response is vague or non-committal'
        })
    
    # Flag denials without proper justification
    for sentence in structured.denial_sentences:
        if 'section' not in sentence.text.lower():
            flags.append({
                'type': 'denial_without_reason',
                'severity': 'high',
                'text': sentence.text,
                'reason': 'Denial without citing specific exemption clause'
            })
    
    return flags


def generate_action_report(structured: StructuredRTIResponse) -> Dict:
    """
    Generate a complete action report for the RTI response.
    
    Args:
        structured: Structured RTI response
        
    Returns:
        Complete action report dictionary
    """
    suggestions = suggest_next_steps(structured)
    appeal_check = check_appeal_eligibility(structured)
    flags = flag_evasive_responses(structured)
    
    return {
        'suggestions': [
            {
                'action': s.action_type.value,
                'priority': s.priority,
                'title': s.title,
                'description': s.description,
                'deadline': s.deadline,
                'reference': s.reference
            }
            for s in suggestions
        ],
        'appeal_eligibility': appeal_check,
        'flags': flags,
        'overall_assessment': _get_overall_assessment(structured)
    }


def _get_overall_assessment(structured: StructuredRTIResponse) -> str:
    """Generate an overall assessment of the response."""
    stats = structured.get_stats()
    
    if stats['informative_ratio'] > 0.6:
        return "SATISFACTORY - Response adequately addresses most queries"
    elif stats['denial_ratio'] > 0.4:
        return "UNSATISFACTORY - Significant information denied, consider appeal"
    elif stats['evasive_count'] > stats['informative_count']:
        return "INADEQUATE - Response is vague and non-committal"
    else:
        return "PARTIAL - Some information provided, review for completeness"
