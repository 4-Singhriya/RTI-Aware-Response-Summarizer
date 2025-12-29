# RTI Response Summarization System - Architecture Documentation

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE (Streamlit)                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  • PDF Upload Component     • Text Paste Area                            ││
│  │  • Summary Display Cards    • Color-Coded Sentence Highlights            ││
│  │  • Action Suggestions Panel • Download Report Button                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PROCESSING PIPELINE                                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STAGE 1: Preprocessing (preprocessing.py)                          │    │
│  │  ├── extract_text_from_pdf() - PyMuPDF text extraction              │    │
│  │  ├── clean_text() - Remove noise, headers, footers                  │    │
│  │  └── normalize_text() - Consistent formatting                       │    │
│  └────────────────────────────────┬────────────────────────────────────┘    │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STAGE 2: RTI Semantic Processing (rti_semantic.py)                 │    │
│  │  ├── detect_rti_sections() - Find Section 8, 9, 11, 19 references   │    │
│  │  ├── classify_sentence() - Categorize as Informative/Denial/etc.    │    │
│  │  └── extract_structured_response() - Create structured output        │    │
│  └────────────────────────────────┬────────────────────────────────────┘    │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STAGE 3: Summarization (summarizer.py)                             │    │
│  │  ├── generate_ultra_short_summary() - 1-2 sentence summary          │    │
│  │  ├── generate_citizen_summary() - Plain language summary            │    │
│  │  └── generate_technical_summary() - Legal/formal summary            │    │
│  └────────────────────────────────┬────────────────────────────────────┘    │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STAGE 4: Actionability (actionability.py)                          │    │
│  │  ├── suggest_next_steps() - Generate action recommendations          │    │
│  │  ├── check_appeal_eligibility() - Determine appeal options           │    │
│  │  └── flag_evasive_responses() - Identify problematic responses       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
INPUT                    PROCESSING                         OUTPUT
─────                    ──────────                         ──────

┌────────┐
│  PDF   │──┐
└────────┘  │    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            ├───▶│ Preprocess   │───▶│ RTI Semantic │───▶│ Structured   │
┌────────┐  │    │ Module       │    │ Processing   │    │ Response     │
│  Text  │──┘    └──────────────┘    └──────────────┘    └──────┬───────┘
└────────┘                                                       │
                                                                 │
                    ┌────────────────────────────────────────────┼
                    │                                            │
                    ▼                                            ▼
            ┌──────────────┐                            ┌──────────────┐
            │ Gemini API   │                            │ Actionability│
            │ Summarizer   │                            │ Engine       │
            └──────┬───────┘                            └──────┬───────┘
                   │                                           │
                   ▼                                           ▼
            ┌──────────────┐                            ┌──────────────┐
            │ 3 Summaries  │                            │ Action       │
            │ - Ultra-short│                            │ Suggestions  │
            │ - Citizen    │                            │ - Appeals    │
            │ - Technical  │                            │ - Next Steps │
            └──────────────┘                            └──────────────┘
```

## Module Interactions

### 1. Preprocessing Module
**Input**: PDF bytes or raw text  
**Output**: Clean, normalized text  
**Dependencies**: PyMuPDF (fitz)

### 2. RTI Semantic Module
**Input**: Cleaned text  
**Output**: StructuredRTIResponse dataclass  
**Dependencies**: config.py (keywords, patterns)

### 3. Summarizer Module
**Input**: Structured response summary text  
**Output**: Dictionary with 3 summary types  
**Dependencies**: Google Generative AI (Gemini)

### 4. Actionability Module
**Input**: StructuredRTIResponse  
**Output**: Action report with suggestions  
**Dependencies**: rti_semantic module

## Key Data Structures

### StructuredRTIResponse
```python
@dataclass
class StructuredRTIResponse:
    original_text: str
    informative_sentences: List[ClassifiedSentence]
    denial_sentences: List[ClassifiedSentence]
    procedural_sentences: List[ClassifiedSentence]
    evasive_sentences: List[ClassifiedSentence]
    section_references: Dict[str, List[str]]
```

### ClassifiedSentence
```python
@dataclass
class ClassifiedSentence:
    text: str
    category: SentenceCategory  # INFORMATIVE, DENIAL, PROCEDURAL, EVASIVE
    confidence: float
    section_references: List[str]
    keywords_found: List[str]
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| PDF Processing | PyMuPDF |
| LLM Summarization | Google Gemini API |
| Language | Python 3.8+ |
