"""IntentIQ Configuration Constants Module.

This module defines central configuration constants used throughout the IntentIQ
buying intent detection and SDR outreach workflow.
"""

from pathlib import Path

# ==============================================================================
# Path Configurations
# ==============================================================================
BASE_DIR: Path = Path(__file__).resolve().parent
OUTPUT_DIRECTORY: Path = BASE_DIR / "outputs"
LOG_DIRECTORY: Path = BASE_DIR / "logs"

# ==============================================================================
# Centralized Signal Taxonomy
# ==============================================================================
SIGNAL_TYPES: dict[str, str] = {
    "HIRING": "HIRING",
    "CUSTOMER_COMPLAINT": "CUSTOMER_COMPLAINT",
    "COMPETITOR_USAGE": "COMPETITOR_USAGE",
    "FUNDING": "FUNDING",
    "EXPANSION": "EXPANSION",
    "LEADERSHIP_CHANGE": "LEADERSHIP_CHANGE",
    "OTHER": "OTHER",
}

# ==============================================================================
# Intent Signal Scoring Weights
# ==============================================================================
# TODO: Fine-tune signal weight values in Phase 3
SIGNAL_WEIGHTS: dict[str, float] = {
    "HIRING": 0.30,
    "FUNDING": 0.25,
    "EXPANSION": 0.25,
    "LEADERSHIP_CHANGE": 0.20,
    "CUSTOMER_COMPLAINT": 0.15,
    "COMPETITOR_USAGE": 0.20,
    "OTHER": 0.10,
}

# ==============================================================================
# Target Competitors & Keyword Queries
# ==============================================================================
COMPETITORS: list[str] = [
    "CompetitorA",
    "CompetitorB",
]

SEARCH_QUERIES: list[str] = [
    "{company_name} hiring software engineer",
    "{company_name} funding expansion",
]

# ==============================================================================
# HTTP & Scraping Settings
# ==============================================================================
REQUEST_TIMEOUT: int = 15  # seconds
MAX_RETRIES: int = 3

# ==============================================================================
# Ranking & Export Settings
# ==============================================================================
TOP_ACCOUNTS: int = 5
