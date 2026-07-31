"""ClickPost Radar Exporter Module.

This module implements the Exporter class responsible for formatting and exporting
collected signals, account intent scores, research briefs, and outreach messages
into clean CSV and JSON deliverables.
"""

import json
import logging
from pathlib import Path
from typing import Any
import pandas as pd

from config import OUTPUT_DIRECTORY

# Configure module logger
logger = logging.getLogger(__name__)


class Exporter:
    """Exporter class for saving pipeline results to file storage."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize Exporter with output directory path.

        Args:
            output_dir: Target directory path for exported files.
        """
        self.output_dir = output_dir or OUTPUT_DIRECTORY
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Exporter initialized with directory: %s", self.output_dir)

    def export_signals(
        self, signals_data: list[dict[str, Any]], filepath: Path | str
    ) -> None:
        """Export raw collected signals to a JSON file.

        Args:
            signals_data: List of company signal dictionaries.
            filepath: Target output file path.
        """
        target_path = Path(filepath)
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(signals_data, f, indent=2, ensure_ascii=False)
            logger.info("Exported raw signals to %s", target_path)
        except Exception as err:
            logger.error("Failed to export signals to %s: %s", target_path, err)

    def export_scores(
        self, scores_data: list[dict[str, Any]], filepath: Path | str
    ) -> None:
        """Export calculated intent scores to CSV or JSON file based on suffix.

        Args:
            scores_data: List of company intent score dictionaries.
            filepath: Target output file path.
        """
        target_path = Path(filepath)
        try:
            if target_path.suffix == ".csv":
                df = pd.DataFrame(scores_data)
                df.to_csv(target_path, index=False, encoding="utf-8")
            else:
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(scores_data, f, indent=2, ensure_ascii=False)
            logger.info("Exported scores to %s", target_path)
        except Exception as err:
            logger.error("Failed to export scores to %s: %s", target_path, err)

    def export_briefs(
        self, briefs_data: list[dict[str, Any]], filepath: Path | str
    ) -> None:
        """Export generated SDR research briefs to a JSON file.

        Args:
            briefs_data: List of research brief dictionaries.
            filepath: Target output file path.
        """
        target_path = Path(filepath)
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(briefs_data, f, indent=2, ensure_ascii=False)
            logger.info("Exported research briefs to %s", target_path)
        except Exception as err:
            logger.error("Failed to export research briefs to %s: %s", target_path, err)

    def export_outreach(
        self, outreach_data: list[dict[str, Any]], filepath: Path | str
    ) -> None:
        """Export generated outreach copy to a CSV file.

        Args:
            outreach_data: List of outreach payload dictionaries.
            filepath: Target output file path.
        """
        target_path = Path(filepath)
        try:
            df = pd.DataFrame(outreach_data)
            df.to_csv(target_path, index=False, encoding="utf-8")
            logger.info("Exported outreach copy to %s", target_path)
        except Exception as err:
            logger.error("Failed to export outreach to %s: %s", target_path, err)
