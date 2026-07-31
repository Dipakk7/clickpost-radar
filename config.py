"""ClickPost Radar Configuration Constants Module.

This module defines central configuration constants used throughout the ClickPost Radar
pipeline, including directory paths, signal taxonomy lists, category weighting logic,
and outreach threshold parameters.
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
SIGNAL_WEIGHTS: dict[str, int] = {
    "CUSTOMER_COMPLAINT": 30,
    "HIRING": 25,
    "COMPETITOR_USAGE": 25,
    "FUNDING": 10,
    "EXPANSION": 10,
    "LEADERSHIP_CHANGE": 10,
    "OTHER": 0,
}

# ==============================================================================
# Target Competitors & Keyword Queries
# ==============================================================================
COMPETITORS: list[str] = [
    "AfterShip",
    "Narvar",
    "ShipStation",
    "ParcelLab",
    "Wonderment",
    "LateShipment",
    "Shippo",
    "Malomo",
]

SEARCH_QUERIES: list[str] = [
    "{company_name} hiring software engineer",
    "{company_name} funding expansion",
]

# ==============================================================================
# HTTP & Scraping Settings
# ==============================================================================
REQUEST_TIMEOUT: int = 5  # seconds
MAX_RETRIES: int = 1

# ==============================================================================
# Ranking & Export Settings
# ==============================================================================
TOP_ACCOUNTS: int = 5
SCORE_THRESHOLDS: dict[str, int] = {
    "HIGH": 30,
    "MEDIUM": 15,
}
