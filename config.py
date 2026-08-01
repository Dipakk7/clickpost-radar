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
# Official Company Domains Mapping
# ==============================================================================
OFFICIAL_DOMAINS: dict[str, str] = {
    "Chubbies": "chubbiesshorts.com",
    "Rothy's": "rothys.com",
    "Brooklinen": "brooklinen.com",
    "Solo Stove": "solostove.com",
    "Vuori": "vuori.com",
    "Outdoor Voices": "outdoorvoices.com",
    "Blueland": "blueland.com",
    "True Classic": "trueclassic.com",
    "Feastables": "feastables.com",
    "Kosas": "kosas.com",
    "Olipop": "drinkolipop.com",
    "Magic Spoon": "magicspoon.com",
    "Liquid Death": "liquiddeath.com",
    "Poppi": "drinkpoppi.com",
    "Graza": "graza.co",
    "Ridge Wallet": "ridge.com",
    "Manscaped": "manscaped.com",
    "Native Deodorant": "nativecos.com",
    "Beardbrand": "beardbrand.com",
    "Caraway": "carawayhome.com",
    "Our Place": "fromourplace.com",
    "Jones Road Beauty": "jonesroadbeauty.com",
    "Tushy": "hellotushy.com",
    "Momofuku Goods": "shop.momofuku.com",
    "Parade Underwear": "yourparade.com",
}

# ==============================================================================
# Ranking & Export Settings
# ==============================================================================
TOP_ACCOUNTS: int = 5
SCORE_THRESHOLDS: dict[str, int] = {
    "HIGH": 30,
    "MEDIUM": 15,
}
