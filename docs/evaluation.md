# Evaluation Approach

## Overview

This document describes the evaluation approach for the RTI Response Summarization System. Since this system uses pretrained LLMs (Gemini) without any training, evaluation focuses on qualitative assessment rather than traditional ML metrics.

## Evaluation Methodology

### 1. Comparison with Generic Summarization

| Aspect | Generic Summarization | RTI-Aware Summarization |
|--------|----------------------|------------------------|
| Structure | Unstructured text summary | Categorized (Informative/Denial/Procedural/Evasive) |
| Focus | Overall content | Citizen outcome (what was provided/denied) |
| Legal Context | None | RTI Act section references |
| Actionability | None | Next-step suggestions |

### 2. Qualitative Metrics

#### Clarity
- **Definition**: How clear and understandable is the summary?
- **Assessment**: 
  - Can a layperson understand the citizen-friendly summary?
  - Is the technical summary precise enough for legal purposes?
- **Measurement**: Manual review by domain experts

#### Completeness
- **Definition**: Does the summary capture all key aspects?
- **Assessment Criteria**:
  - ✓ Information provided is captured
  - ✓ Information denied is captured
  - ✓ Section references are identified
  - ✓ Procedural aspects are noted
- **Measurement**: Checklist-based evaluation

#### Usefulness
- **Definition**: Does the output help the citizen take action?
- **Assessment Criteria**:
  - ✓ Are action suggestions relevant?
  - ✓ Are appeal options correctly identified?
  - ✓ Are deadlines mentioned?
- **Measurement**: User feedback and expert review

### 3. Classification Accuracy

Since this is a rule-based classification system, we evaluate:

| Metric | Description |
|--------|-------------|
| Section Detection Rate | % of RTI section references correctly identified |
| Classification Precision | Spot-check accuracy of sentence categorization |
| False Positive Rate | Incorrect categorizations (e.g., neutral marked as denial) |

### 4. Test Cases

#### Test Case 1: Complete Response
- Input: RTI response with full information disclosure
- Expected: High informative ratio, "No action needed" suggestion

#### Test Case 2: Partial Denial
- Input: RTI response with Section 8 exemption
- Expected: Denial detected, First Appeal suggested

#### Test Case 3: Evasive Response
- Input: Vague RTI response with non-answers
- Expected: Evasive sentences flagged, clarification suggested

#### Test Case 4: Procedural Response
- Input: Transfer notice or fee request
- Expected: Procedural classification, appropriate wait/pay suggestion

## Limitations

1. **No Ground Truth Dataset**: No annotated RTI response corpus exists
2. **Subjective Evaluation**: Quality assessment depends on human judgment
3. **LLM Variability**: Gemini outputs may vary between runs
4. **Language Limitation**: Currently optimized for English RTI responses

## Future Improvements

1. Create annotated dataset for quantitative evaluation
2. Add inter-rater reliability measurements
3. Implement automated quality checks
4. Support Hindi and regional language RTI responses

## Conclusion

This evaluation approach focuses on practical utility rather than abstract metrics. The system is evaluated based on whether it helps citizens understand their RTI responses and take appropriate action.
