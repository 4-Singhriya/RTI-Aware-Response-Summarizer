# RTI Response Summarization System
## Comprehensive Project Report

---

## 1. Project Overview

### 1.1 Title
**RTI Response Summarization System with PII-Aware Preprocessing and Fact-Consistency Enforcement Layer**

### 1.2 Objective
Build a fully working RTI (Right to Information) response summarization system that:
- Summarizes actual information provided in RTI replies
- Does NOT generate generic procedural explanations
- Correctly handles procedural-heavy or partially informative RTI responses
- Provides multi-level summaries for different user needs

### 1.3 Technology Stack
| Component | Technology |
|-----------|------------|
| Language | Python |
| Frontend | Streamlit |
| Summarization Engine | Google Gemini API |
| Fallback | Local NLTK-based extractive summarization |
| PDF Processing | PyMuPDF |

---

## 2. System Architecture

### 2.1 Pipeline Flow Diagram

```
┌─────────────────┐
│  USER INPUT     │
│  (PDF / Text)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 1: PREPROCESSING                     │
│  • Extract text from PDF                     │
│  • Clean headers, footers, signatures        │
│  • Sentence segmentation                     │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 2: RTI SENTENCE CLASSIFICATION       │
│  (For UI/Stats ONLY - NOT for filtering)    │
│  • Classify: Informative/Denial/Procedural   │
│  • Detect RTI Act sections (8, 9, 11, etc.) │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 3: FACT ANCHOR EXTRACTION            │
│  • Extract 2-5 most informative sentences    │
│  • Score by: dates, amounts, actions         │
│  • Prevents generic summaries                │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 4: SUMMARIZATION                     │
│  Input: Fact Anchors + FULL Cleaned Text    │
│  • Ultra-Short Summary (1-2 sentences)       │
│  • Citizen-Friendly Summary (3-5 sentences)  │
│  • Technical/Legal Summary                   │
│                                              │
│  ┌─────────────┐    ┌───────────────────┐   │
│  │ Gemini API  │───▶│ Local Fallback    │   │
│  │ (Primary)   │fail│ (NLTK Extractive) │   │
│  └─────────────┘    └───────────────────┘   │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 5: ACTIONABILITY LAYER               │
│  • Mark response: COMPLETE/PARTIAL/PROCEDURAL│
│  • Suggest: Appeal, Clarification, etc.      │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 6: STREAMLIT UI                      │
│  • PDF upload / Text paste                   │
│  • Classified sentences with color coding   │
│  • Summary cards with source badges          │
│  • Action suggestions                        │
│  • Download report                           │
└─────────────────────────────────────────────┘
```

---

## 3. Module-wise Detailed Explanation

### 3.1 Module 1: Input & Preprocessing
**File:** `modules/preprocessing.py`

**Responsibilities:**
- Accept RTI response as PDF file or pasted text
- Extract text from PDF using PyMuPDF
- Clean text by removing:
  - Headers and footers
  - Date/dispatch lines
  - Signatures and office stamps
- Perform sentence segmentation

**Output:** Cleaned RTI response text (full content preserved)

---

### 3.2 Module 2: RTI Sentence Classification
**File:** `modules/rti_semantic.py`

**Responsibilities:**
- Classify each sentence into categories:
  - **Informative** (🟢): Contains actual information
  - **Denial** (🔴): Information was denied/rejected
  - **Procedural** (🟡): Administrative procedures
  - **Evasive** (🟠): Unclear or avoiding responses
- Detect RTI Act section references (Sections 8, 9, 11, 19, etc.)
- Calculate confidence scores for each classification

**Critical Design Rule:**
> Classification is used ONLY for UI highlighting and statistics.
> It does NOT filter or restrict content sent to the summarizer.

---

### 3.3 Module 3: Fact Anchor Extraction
**File:** `modules/fact_extractor.py`

**Purpose:** Prevent generic summaries by anchoring the model to real facts.

**How it works:**
1. Score each sentence based on:
   - **Dates** (e.g., "25th October, 2024") → +2.5 points
   - **Amounts** (e.g., "Rs. 45,678/-") → +3.0 points
   - **Actions** (e.g., "processed", "credited") → +2.0 points
   - **Denials** (e.g., "Section 8 exemption") → +2.5 points
   - **Authorities** (e.g., "Ministry of Finance") → +1.0 point

2. Select top 5 highest-scoring sentences as "Fact Anchors"

**Example Output:**
```
1. Your income tax refund for Assessment Year 2023-24 amounting to Rs. 45,678/- was processed on 25th October, 2024.
2. This exemption is claimed under Section 8(1)(j) of the RTI Act, 2005.
3. Point No. 5 of your application has been transferred to the CPIO, NSDL.
```

---

### 3.4 Module 4: Summarization
**File:** `modules/summarizer.py`

**Critical Innovation:**
> Summarization input = Fact Anchors + Full Cleaned Text
> Classification labels do NOT influence summarization scope.

**Three Summary Types:**

| Type | Purpose | Length |
|------|---------|--------|
| Ultra-Short | Quick overview | 1-2 sentences |
| Citizen-Friendly | Simple language for common citizens | 3-5 sentences |
| Technical/Legal | Formal language for appeals | Detailed |

**Prompt Design (Ultra-Short Example):**
```
You are summarizing an RTI response.

Task:
- State what INFORMATION was actually provided
- Mention key activities, dates, locations, outcomes
- Do NOT generate generic explanations
- Base the summary strictly on content provided

Key Facts:
{fact_anchors}

Full RTI Response:
{full_text}
```

**Fallback System:**
- **Primary:** Gemini API (gemini-2.5-flash)
- **On 429/Quota Error:** Automatic switch to local NLTK-based extractive summarization
- **Logging:** All failures logged to `logs/quota_failures.json`

---

### 3.5 Module 5: Actionability Layer
**File:** `modules/actionability.py`

**Responsibilities:**
- Analyze classification results
- Mark response as:
  - **SATISFACTORY** - Information provided
  - **PARTIAL** - Some denials
  - **UNSATISFACTORY** - Major issues found
- Suggest actions:
  - File First Appeal (with deadline)
  - Request clarification
  - Pay additional fees
  - Wait for transferred application response

---

### 3.6 Module 6: Streamlit UI
**File:** `app.py`

**Features:**
1. **Input Section:**
   - PDF file upload
   - Text paste area

2. **Analysis Display:**
   - Statistics (total sentences, category counts)
   - Fact Anchors (expandable view)
   - Summary buttons with source badges:
     - 🌐 Gemini API
     - 💻 Local Fallback

3. **Classified Sentences:**
   - Tabbed view by category
   - Color-coded highlighting

4. **Action Suggestions:**
   - Priority-based display
   - Deadlines and references

5. **Export:**
   - Download summary report as text file

---

## 4. Key Design Decisions

### 4.1 Decoupling Classification from Summarization

**Problem:** Previous approaches filtered text by classification, causing generic summaries for procedural-heavy responses.

**Solution:** Classification is used ONLY for UI/stats. Summarization always receives the full cleaned text.

### 4.2 Fact-Anchored Prompting

**Problem:** LLMs tend to generate generic or hallucinated content when given procedural text.

**Solution:** Extract key factual sentences and inject them into the prompt as "anchors" that the model must reference.

### 4.3 Automatic Fallback Switching

**Problem:** Gemini API has quota limits (429 errors).

**Solution:** 
- Detect quota errors automatically
- Switch to local NLTK extractive summarization
- Log all failures for audit trail
- Display source badge in UI

---

## 5. Configuration Options
**File:** `config.py`

```python
# Gemini API
GEMINI_MODEL = "gemini-2.5-flash"

# Fallback Settings
ENABLE_LOCAL_FALLBACK = True  # Enable local summarizer
FALLBACK_MODE = "auto"        # "auto", "local_only", "gemini_only"

# Logging
LOG_QUOTA_FAILURES = True
LOGS_DIR = "logs"

# Fact Anchors
FACT_ANCHOR_COUNT = 5
```

---

## 6. Project Files Structure

```
NLP PROJECT/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
│
├── modules/
│   ├── preprocessing.py        # Text extraction & cleaning
│   ├── rti_semantic.py         # Sentence classification
│   ├── fact_extractor.py       # Fact anchor extraction
│   ├── summarizer.py           # Gemini + fallback summarization
│   ├── fallback_summarizer.py  # Local NLTK summarization
│   └── actionability.py        # Action suggestions
│
├── utils/
│   ├── helpers.py              # Utility functions
│   └── logger.py               # Quota failure logging
│
├── sample_data/
│   └── sample_rti_response.txt # Sample RTI for testing
│
├── logs/
│   └── quota_failures.json     # API failure audit trail
│
└── docs/
    ├── architecture.md         # System architecture
    └── evaluation.md           # Evaluation metrics
```

---

## 7. Novelty Statement (For Patent)

> "The system introduces an RTI-aware NLP pipeline that decouples sentence classification from summarization and employs fact-anchored prompting to prevent generic or hallucinated summaries in procedural-heavy RTI responses."

### Novel Contributions:
1. **Fact-Anchored Prompting:** Extracting key factual sentences to anchor LLM responses
2. **Hybrid Cloud-Local Architecture:** Automatic failover from Gemini to local NLTK
3. **Classification-Summarization Decoupling:** Using classification for UI only, not for filtering
4. **RTI-Specific Semantics:** Domain-specific keyword matching for Section 8, 9, 11 detection
5. **Audit Trail Logging:** Complete logging of API failures for transparency

---

## 8. How to Run

### 8.1 Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set API key (create .env file)
echo GEMINI_API_KEY=your_key_here > .env
```

### 8.2 Run Application
```bash
streamlit run app.py
```

### 8.3 Usage
1. Open browser at `http://localhost:8501`
2. Upload PDF or paste RTI response text
3. Click "Analyze RTI Response"
4. View extracted fact anchors
5. Click summary buttons to generate
6. Download report if needed

---

## 9. Future Enhancements

1. **PII Redaction:** Add Aadhaar, PAN, phone number masking
2. **Multi-language Support:** Hindi and regional language RTI responses
3. **Fact Verification:** Cross-reference claims with government databases
4. **Batch Processing:** Handle multiple RTI responses at once
5. **Appeal Draft Generation:** Auto-generate First Appeal drafts

---

## 10. Conclusion

The RTI Response Summarization System successfully addresses the challenge of generating content-aware summaries from RTI responses. By implementing fact-anchored prompting and decoupling classification from summarization, the system produces accurate, specific summaries even for procedural-heavy documents. The hybrid architecture with automatic fallback ensures system robustness, while comprehensive logging provides an audit trail suitable for patent defensibility.

---

*Report generated: December 18, 2024*
