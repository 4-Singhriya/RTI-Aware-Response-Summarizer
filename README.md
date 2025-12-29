# 📄 RTI Response Summarization System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)
![Gemini](https://img.shields.io/badge/Google-Gemini%20API-4285F4.svg)
![License](https://img.shields.io/badge/License-Educational-green.svg)

**An intelligent NLP pipeline for summarizing RTI (Right to Information) responses with PII-aware preprocessing and fact-consistency enforcement.**

[Features](#-features) •
[Installation](#-installation) •
[Usage](#-usage) •
[Architecture](#-architecture) •
[Documentation](#-documentation)

</div>

---

## 🌟 Features

### Core Capabilities
- **📤 Multi-Format Input** — Upload PDF files or paste RTI response text directly
- **🔍 RTI-Aware Processing** — Detects RTI Act sections (8, 9, 11, 19) and classifies sentences
- **📝 Multi-Level Summaries**:
  - 🎯 **Ultra-Short** (1-2 sentences) — Quick overview
  - 👥 **Citizen-Friendly** (3-5 sentences) — Simple language for common citizens
  - ⚖️ **Technical/Legal** — Formal language for appeals
- **✅ Action Suggestions** — Recommends next steps based on response analysis
- **🎨 Color-Coded Highlights** — Visual classification of response types

### Technical Highlights
- **Fact-Anchored Prompting** — Prevents generic summaries by anchoring to real facts
- **Hybrid Architecture** — Automatic failover from Gemini API to local NLTK summarization
- **Audit Trail Logging** — Complete logging of API failures for transparency

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Step 1: Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/RTI-Summarization-System.git
cd RTI-Summarization-System
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure API Key
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_api_key_here
```

Or set it via environment variable:
```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

---

## 🎮 Usage

### Run the Application
```bash
streamlit run app.py
```

### Open in Browser
Navigate to `http://localhost:8501`

### Quick Guide
1. **Upload** a PDF or **paste** RTI response text
2. Click **"Analyze RTI Response"**
3. View extracted **fact anchors** and **sentence classifications**
4. Generate summaries by clicking the summary buttons
5. Review **action suggestions** for next steps
6. **Download** the summary report if needed

---

## 🏗️ Architecture

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
│  • Classify: Informative/Denial/Procedural   │
│  • Detect RTI Act sections (8, 9, 11, etc.) │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 3: FACT ANCHOR EXTRACTION            │
│  • Extract 2-5 most informative sentences    │
│  • Score by: dates, amounts, actions         │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 4: SUMMARIZATION                     │
│  ┌─────────────┐    ┌───────────────────┐   │
│  │ Gemini API  │───▶│ Local Fallback    │   │
│  │ (Primary)   │fail│ (NLTK Extractive) │   │
│  └─────────────┘    └───────────────────┘   │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 5: ACTIONABILITY LAYER               │
│  • Mark response status                      │
│  • Suggest: Appeal, Clarification, etc.      │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  MODULE 6: STREAMLIT UI                      │
│  • Summary cards with source badges          │
│  • Classified sentences with color coding   │
│  • Action suggestions & Download report      │
└─────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
RTI-Summarization-System/
│
├── 📄 app.py                    # Main Streamlit application
├── ⚙️ config.py                 # Configuration settings
├── 📋 requirements.txt          # Python dependencies
├── 📖 README.md                 # Project documentation
│
├── 📦 modules/
│   ├── preprocessing.py         # PDF extraction & text cleaning
│   ├── rti_semantic.py          # RTI-aware sentence classification
│   ├── fact_extractor.py        # Fact anchor extraction
│   ├── summarizer.py            # Gemini API summarization
│   ├── fallback_summarizer.py   # Local NLTK fallback
│   └── actionability.py         # Next-step suggestions
│
├── 🔧 utils/
│   ├── helpers.py               # Utility functions
│   └── logger.py                # Quota failure logging
│
├── 📚 docs/
│   ├── architecture.md          # System architecture details
│   ├── evaluation.md            # Evaluation metrics
│   └── PROJECT_REPORT.md        # Comprehensive project report
│
├── 📊 sample_data/
│   └── sample_rti_response.txt  # Sample RTI for testing
│
└── 📝 logs/
    └── quota_failures.json      # API failure audit trail
```

---

## 🎨 Color Legend

| Color | Category | Description | Example |
|:-----:|----------|-------------|---------|
| 🟢 | **Informative** | Information provided | "Your refund was processed on 25th October" |
| 🔴 | **Denial** | Information denied | "Exempt under Section 8(1)(j)" |
| 🟡 | **Procedural** | Administrative info | "Transferred to CPIO, NSDL" |
| 🟠 | **Evasive** | Vague responses | "Information not maintained" |

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Gemini API
GEMINI_MODEL = "gemini-2.5-flash"

# Fallback Settings
ENABLE_LOCAL_FALLBACK = True  # Enable local summarizer
FALLBACK_MODE = "auto"        # "auto", "local_only", "gemini_only"

# Logging
LOG_QUOTA_FAILURES = True

# Fact Anchors
FACT_ANCHOR_COUNT = 5
```

---

## 📜 RTI Act Reference

| Section | Purpose |
|---------|---------|
| **Section 7** | Time limit for response (30 days) |
| **Section 8** | Exemptions from disclosure |
| **Section 9** | Grounds for rejection |
| **Section 11** | Third party information |
| **Section 19** | Right to appeal |

---

## 📚 Documentation

- [System Architecture](docs/architecture.md)
- [Evaluation Metrics](docs/evaluation.md)
- [Project Report](docs/PROJECT_REPORT.md)

---

## 🏆 Novelty Statement

> *"The system introduces an RTI-aware NLP pipeline that decouples sentence classification from summarization and employs fact-anchored prompting to prevent generic or hallucinated summaries in procedural-heavy RTI responses."*

### Novel Contributions
1. **Fact-Anchored Prompting** — Extracting key factual sentences to anchor LLM responses
2. **Hybrid Cloud-Local Architecture** — Automatic failover from Gemini to local NLTK
3. **Classification-Summarization Decoupling** — Using classification for UI only, not filtering
4. **RTI-Specific Semantics** — Domain-specific keyword matching for Section detection
5. **Audit Trail Logging** — Complete logging of API failures for transparency

---

## 🔮 Future Enhancements

- [ ] **PII Redaction** — Aadhaar, PAN, phone number masking
- [ ] **Multi-language Support** — Hindi and regional language RTI responses
- [ ] **Fact Verification** — Cross-reference claims with government databases
- [ ] **Batch Processing** — Handle multiple RTI responses at once
- [ ] **Appeal Draft Generation** — Auto-generate First Appeal drafts

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📝 License

This project is for **educational purposes**.

---

## 👨‍💻 Author

**RIYA SINGH**

---

<div align="center">

Made with ❤️ for RTI transparency

</div>
