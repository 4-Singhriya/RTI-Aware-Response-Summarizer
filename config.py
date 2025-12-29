"""
Configuration settings for RTI Response Summarization System
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# Text Processing Settings
MAX_CHUNK_SIZE = 4000  # Maximum characters per chunk for Gemini
MIN_CHUNK_SIZE = 500   # Minimum chunk size

# RTI Act Section Patterns
RTI_SECTIONS = {
    "section_8": r"[Ss]ection\s*8|[Ss]ec\.\s*8|exemption|exempt",
    "section_9": r"[Ss]ection\s*9|[Ss]ec\.\s*9|reject|rejection",
    "section_11": r"[Ss]ection\s*11|[Ss]ec\.\s*11|third\s*party",
    "section_19": r"[Ss]ection\s*19|[Ss]ec\.\s*19|appeal",
    "section_7": r"[Ss]ection\s*7|[Ss]ec\.\s*7|time\s*limit|30\s*days",
}

# Classification Keywords
DENIAL_KEYWORDS = [
    "cannot be provided", "denied", "rejected", "exempt", "exemption",
    "not available", "refused", "decline", "not possible", "section 8",
    "confidential", "classified", "sensitive", "national security"
]

INFORMATIVE_KEYWORDS = [
    "information is", "details are", "as per records", "enclosed",
    "attached", "provided herewith", "following information", "data shows"
]

PROCEDURAL_KEYWORDS = [
    "transferred to", "forwarded to", "fee required", "please deposit",
    "time extension", "additional time", "competent authority", "CPIO"
]

EVASIVE_KEYWORDS = [
    "no such information", "not maintained", "not available",
    "beyond scope", "voluminous", "vague", "clarify", "resubmit"
]

# UI Color Codes
COLORS = {
    "informative": "#28a745",  # Green
    "denial": "#dc3545",       # Red
    "procedural": "#ffc107",   # Yellow
    "evasive": "#fd7e14",      # Orange
}

# App Settings
APP_TITLE = "RTI Response Summarization System"
APP_SUBTITLE = "RTI-Aware Semantic Processing with Multi-Level Summaries"

# Fallback Settings
ENABLE_LOCAL_FALLBACK = True  # Enable local summarizer when Gemini fails
FALLBACK_MODE = "auto"  # "auto" = try Gemini first, fallback on error
                        # "local_only" = always use local
                        # "gemini_only" = never use fallback

# Logging Settings
LOG_QUOTA_FAILURES = True
LOGS_DIR = "logs"

# Fact Anchor Settings
FACT_ANCHOR_COUNT = 5  # Number of fact anchors to extract
