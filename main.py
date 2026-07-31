"""IntentIQ Main Application Entry Point.

This module serves as the primary entry point for the IntentIQ pipeline.
It sets up logging, reads target companies, initializes core pipeline classes,
and provides a clean structure for executing Phase 2-5 workflows.
"""

import logging
from pathlib import Path
import pandas as pd

from collector import SignalCollector
from config import LOG_DIRECTORY, OUTPUT_DIRECTORY
from exporter import Exporter
from generator import OutreachGenerator
from scorer import IntentScorer


def setup_logging() -> None:
    """Configure system-wide logging to console and log file."""
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    log_file = LOG_DIRECTORY / "intentiq.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def load_companies(file_path: Path) -> list[str]:
    """Load target company names from a CSV file.

    Args:
        file_path: Path to the target companies CSV file.

    Returns:
        list[str]: List of target company names.
    """
    if not file_path.exists():
        logging.error("Companies file not found at: %s", file_path)
        return []

    df = pd.read_csv(file_path)
    if "company" in df.columns:
        companies = df["company"].dropna().str.strip().tolist()
        logging.info("Loaded %d companies from %s", len(companies), file_path.name)
        return companies

    logging.warning("No 'company' column found in %s", file_path.name)
    return []


def main() -> None:
    """Main application execution flow."""
    setup_logging()
    logger = logging.getLogger("main")

    logger.info("==================================================")
    logger.info("IntentIQ — AI-Powered Buying Intent Detection & SDR Outreach")
    logger.info("Phase 1: Project Foundation & Infrastructure Ready")
    logger.info("==================================================")

    # 1. Load target companies
    companies_file = Path("companies.csv")
    companies = load_companies(companies_file)
    print(f"\n[IntentIQ] Target Companies Loaded: {companies}")

    # 2. Initialize pipeline components
    logger.info("Initializing IntentIQ core modules...")
    collector = SignalCollector()
    scorer = IntentScorer()
    generator = OutreachGenerator()
    exporter = Exporter(output_dir=OUTPUT_DIRECTORY)

    print("\n[IntentIQ] All components successfully initialized:")
    print(f"  - Collector: {collector.__class__.__name__}")
    print(f"  - Scorer: {scorer.__class__.__name__}")
    print(f"  - Generator: {generator.__class__.__name__}")
    print(f"  - Exporter: {exporter.__class__.__name__}")

    # ==============================================================================
    # Pipeline Execution
    # ==============================================================================
    # Phase 2: Signal Collection Engine
    logger.info("Executing Phase 2 Signal Collection Engine...")
    raw_signals = collector.collect_all(companies)
    print(f"\n[IntentIQ] Phase 2 Collection Completed: {len(raw_signals)} company signal sets collected.")

    # TODO Phase 3: scored_accounts = scorer.rank_accounts(scorer.score_company(s) for s in raw_signals)
    # TODO Phase 4: outreach_briefs = [generator.generate_research_brief(a) for a in scored_accounts]
    # TODO Phase 5: exporter.export_scores(scored_accounts, OUTPUT_DIRECTORY / "scores.csv")
    # ==============================================================================

    print("\n[IntentIQ] Startup completed successfully. Ready for business logic implementation.\n")


if __name__ == "__main__":
    main()
