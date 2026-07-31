"""ClickPost Radar Intent Scoring Engine.

This module implements the IntentScorer class responsible for converting collected
buying-intent signals into a transparent, deterministic, and explainable account ranking.
"""

from dataclasses import asdict, dataclass, field
import json
import logging
from pathlib import Path
from typing import Any, Optional
import pandas as pd

from config import OUTPUT_DIRECTORY, SIGNAL_WEIGHTS

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class CompanyScore:
    """Represents calculated intent score, priority, confidence, and 'Why Now' summary for a company."""

    company: str
    intent_score: int
    priority: str
    confidence: str
    evidence_count: int
    detected_signals: list[str]
    why_now: str

    def to_dict(self) -> dict[str, Any]:
        """Convert CompanyScore instance to dictionary format."""
        return {
            "company": self.company,
            "intent_score": self.intent_score,
            "priority": self.priority,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "detected_signals": self.detected_signals,
            "why_now": self.why_now,
        }


class IntentScorer:
    """Scorer engine for calculating explainable buying intent scores and ranking sales accounts."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize IntentScorer with output directory path.

        Args:
            output_dir: Target directory path for output files.
        """
        self.output_dir = output_dir or OUTPUT_DIRECTORY
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("IntentScorer initialized successfully.")

    def _calculate_priority(self, score: int) -> str:
        """Assign qualitative priority label based on intent score.

        Args:
            score: Capped intent score integer (0-100).

        Returns:
            str: Priority label ('High', 'Medium', 'Low').
        """
        if score >= 80:
            return "High"
        elif score >= 50:
            return "Medium"
        return "Low"

    def _aggregate_confidence(self, signals: list[dict[str, Any]]) -> str:
        """Aggregate confidence across all detected signals for an account.

        Args:
            signals: List of signal dictionaries.

        Returns:
            str: Overall company confidence level ('High', 'Medium', 'Low').
        """
        confidences = [s.get("confidence", "Low") for s in signals]
        if "High" in confidences:
            return "High"
        elif "Medium" in confidences:
            return "Medium"
        return "Low"

    def _generate_why_now(self, detected_signals: set[str]) -> str:
        """Generate a deterministic rule-based 'Why Now' SDR summary statement.

        Args:
            detected_signals: Set of unique signal types detected for the company.

        Returns:
            str: Concise SDR 'Why Now' summary (max 2 sentences).
        """
        if not detected_signals:
            return "No meaningful buying intent signals were detected from the available public sources."

        has_funding = "FUNDING" in detected_signals
        has_hiring = "HIRING" in detected_signals
        has_leadership = "LEADERSHIP_CHANGE" in detected_signals
        has_complaint = "CUSTOMER_COMPLAINT" in detected_signals
        has_competitor = "COMPETITOR_USAGE" in detected_signals
        has_expansion = "EXPANSION" in detected_signals

        # Rule-based priority template matching
        if has_funding and has_hiring:
            return "Recent funding combined with active hiring suggests operational expansion and increasing logistics complexity."
        if has_hiring and has_leadership:
            return "Leadership expansion together with active hiring indicates organizational scaling."
        if has_complaint and has_competitor:
            return "Public customer feedback and competitor technology usage indicate immediate opportunities for displacement."
        if has_complaint:
            return "Public customer feedback indicates opportunities to improve the post-purchase experience."
        if has_competitor:
            return "Existing investment in post-purchase tools suggests category awareness and potential competitive displacement."
        if has_funding and has_expansion:
            return "Recent capital infusion paired with market expansion points to rapid business growth."
        if has_funding:
            return "Recent funding allocation indicates financial backing for strategic growth initiatives."
        if has_expansion:
            return "Active operational and market expansion indicates growing scalability demands."
        if has_hiring:
            return "Active hiring expansion across key departments indicates organizational growth."
        if has_leadership:
            return "Recent C-suite and leadership additions signal upcoming strategic transformations."

        return "Public signals indicate ongoing market activity and account evaluation potential."

    def score_company(self, company_data: dict[str, Any]) -> CompanyScore:
        """Calculate explainable intent score and 'Why Now' summary for a single company.

        Args:
            company_data: Dictionary containing company name and collected signals list.

        Returns:
            CompanyScore: Calculated score and account summary object.
        """
        company_name = company_data.get("company", "Unknown")
        logger.info("Scoring company: %s", company_name)

        signals = company_data.get("signals", [])
        evidence_count = len(signals)

        if not signals:
            logger.info("Detected signals for %s: None", company_name)
            logger.info("Calculated score for %s: 0", company_name)
            logger.info("Assigned priority for %s: Low", company_name)
            logger.info("Generated Why Now summary for %s: No signals detected.", company_name)
            return CompanyScore(
                company=company_name,
                intent_score=0,
                priority="Low",
                confidence="Low",
                evidence_count=0,
                detected_signals=[],
                why_now="No meaningful buying intent signals were detected from the available public sources.",
            )

        # Extract unique detected signal categories
        detected_types: set[str] = {
            s.get("signal_type", "OTHER") for s in signals if s.get("signal_type")
        }
        sorted_detected_signals = sorted(list(detected_types))

        # Sum weights per signal category and cap at 100
        raw_score = sum(SIGNAL_WEIGHTS.get(sig_type, 0) for sig_type in detected_types)
        final_score = min(100, raw_score)

        priority = self._calculate_priority(final_score)
        confidence = self._aggregate_confidence(signals)
        why_now_summary = self._generate_why_now(detected_types)

        logger.info("Detected signals for %s: %s", company_name, sorted_detected_signals)
        logger.info("Calculated score for %s: %d", company_name, final_score)
        logger.info("Assigned priority for %s: %s", company_name, priority)
        logger.info("Generated Why Now summary for %s: %s", company_name, why_now_summary)

        return CompanyScore(
            company=company_name,
            intent_score=final_score,
            priority=priority,
            confidence=confidence,
            evidence_count=evidence_count,
            detected_signals=sorted_detected_signals,
            why_now=why_now_summary,
        )

    def rank_accounts(self, company_scores: list[CompanyScore]) -> list[CompanyScore]:
        """Rank target sales accounts by intent score (descending) and evidence count (descending).

        Args:
            company_scores: List of unsorted CompanyScore objects.

        Returns:
            list[CompanyScore]: Ranked list of CompanyScore objects.
        """
        ranked = sorted(
            company_scores,
            key=lambda cs: (cs.intent_score, cs.evidence_count),
            reverse=True,
        )
        logger.info("Ranking completed.")
        return ranked

    def export_csv(self, scored_accounts: list[CompanyScore], filepath: Path) -> None:
        """Export ranked account scores to CSV file.

        Args:
            scored_accounts: Ranked list of CompanyScore objects.
            filepath: Target CSV output path.
        """
        try:
            records = []
            for account in scored_accounts:
                rec = account.to_dict()
                rec["detected_signals"] = "; ".join(account.detected_signals)
                records.append(rec)

            df = pd.DataFrame(records)
            df.to_csv(filepath, index=False, encoding="utf-8")
            logger.info("CSV exported to %s", filepath)
        except Exception as err:
            logger.error("Failed to export CSV to %s: %s", filepath, err)

    def export_json(self, scored_accounts: list[CompanyScore], filepath: Path) -> None:
        """Export ranked account scores to JSON file.

        Args:
            scored_accounts: Ranked list of CompanyScore objects.
            filepath: Target JSON output path.
        """
        try:
            payload = [account.to_dict() for account in scored_accounts]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.info("JSON exported to %s", filepath)
        except Exception as err:
            logger.error("Failed to export JSON to %s: %s", filepath, err)

    def process_and_score_file(
        self, signals_filepath: Path | str | None = None
    ) -> list[CompanyScore]:
        """Load collected signals file, score companies, rank accounts, and export CSV/JSON outputs.

        Args:
            signals_filepath: Path to signals.json file. Defaults to outputs/signals.json.

        Returns:
            list[CompanyScore]: Ranked list of company score objects.
        """
        in_file = Path(signals_filepath or (self.output_dir / "signals.json"))
        logger.info("Loading collected signals from %s...", in_file)

        if not in_file.exists():
            logger.error("Collected signals file not found at: %s", in_file)
            return []

        try:
            with open(in_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as err:
            logger.error("Error reading signals file %s: %s", in_file, err)
            return []

        # Handle both single company object and list of company objects
        if isinstance(raw_data, dict):
            company_list = [raw_data]
        elif isinstance(raw_data, list):
            company_list = raw_data
        else:
            logger.error("Invalid JSON format in %s", in_file)
            return []

        scores: list[CompanyScore] = []
        for company_data in company_list:
            comp_score = self.score_company(company_data)
            scores.append(comp_score)

        ranked_scores = self.rank_accounts(scores)

        # Export outputs/scored_accounts.csv and outputs/scored_accounts.json
        csv_path = self.output_dir / "scored_accounts.csv"
        json_path = self.output_dir / "scored_accounts.json"

        self.export_csv(ranked_scores, csv_path)
        self.export_json(ranked_scores, json_path)

        return ranked_scores
