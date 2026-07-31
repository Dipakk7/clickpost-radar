"""IntentIQ Signal Collector Engine.

This module implements the SignalCollector class for gathering, extracting,
and normalizing structured public buying-intent signals across multiple public sources
including Company Careers, Company Blog, News / Press Releases, Trustpilot, and Reddit.

Refactored in Phase 2.1 to utilize qualitative confidence levels (Low, Medium, High)
and centralized signal taxonomy.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
from typing import Any, Optional
import requests
from bs4 import BeautifulSoup

from config import (
    COMPETITORS,
    MAX_RETRIES,
    OUTPUT_DIRECTORY,
    REQUEST_TIMEOUT,
    SEARCH_QUERIES,
    SIGNAL_TYPES,
)

# Configure module logger
logger = logging.getLogger(__name__)

OFFICIAL_SOURCES: set[str] = {
    "Company Careers",
    "Company Blog",
    "Press Release",
    "News / Press Releases",
}


@dataclass
class Signal:
    """Represents a single structured buying intent signal."""

    company: str
    signal_type: str
    title: str
    evidence: str
    source: str
    url: str
    date: str
    confidence: str  # "Low", "Medium", "High"

    def to_dict(self) -> dict[str, Any]:
        """Convert Signal instance to dictionary format."""
        return asdict(self)


@dataclass
class CompanySignals:
    """Represents all collected buying intent signals for a target company."""

    company: str
    signals: list[Signal] = field(default_factory=list)
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert CompanySignals instance to dictionary format."""
        return {
            "company": self.company,
            "collected_at": self.collected_at,
            "signals_count": len(self.signals),
            "signals": [s.to_dict() for s in self.signals],
        }


class SignalCollector:
    """Collector engine for gathering structured buying intent signals from public data sources."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize SignalCollector with configuration settings and session headers.

        Args:
            output_dir: Directory path where outputs will be saved.
        """
        self.output_dir = output_dir or OUTPUT_DIRECTORY
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        logger.info("SignalCollector initialized successfully.")

    def _determine_confidence(self, source: str, occurrences: int = 1) -> str:
        """Determine qualitative confidence level ('Low', 'Medium', 'High').

        Confidence is proportional to source authority and evidence depth:
        - High: Primary official company sources (Careers, Blog) or multiple confirmations (>=3).
        - Medium: News articles / press releases or 2 independent confirmations.
        - Low: Single unverified mentions (<=1) or community discussions.
        """
        if source in {"Company Careers", "Company Blog"} or occurrences >= 3:
            return "High"
        elif source in {"News / Press Releases", "Press Release"} or occurrences == 2:
            return "Medium"
        return "Low"

    def _map_signal_type(self, raw_type: str, text: str = "") -> str:
        """Normalize raw signal type strings into standardized SIGNAL_TYPES taxonomy.

        Args:
            raw_type: Raw signal category or tag.
            text: Title or evidence text snippet for contextual mapping.

        Returns:
            str: Standardized taxonomy key from SIGNAL_TYPES.
        """
        text_lower = text.lower()
        raw_lower = raw_type.lower()

        if (
            "competitor" in raw_lower
            or "tech_stack" in raw_lower
            or "switch" in text_lower
            or any(comp.lower() in text_lower for comp in COMPETITORS)
        ):
            return SIGNAL_TYPES["COMPETITOR_USAGE"]
        if (
            "funding" in raw_lower
            or "funding" in text_lower
            or "investment" in text_lower
            or "raises" in text_lower
            or "valuation" in text_lower
        ):
            return SIGNAL_TYPES["FUNDING"]
        if (
            "c-suite" in text_lower
            or "hires" in text_lower
            or "appointed" in text_lower
            or "executive" in text_lower
            or "ceo" in text_lower
            or "leadership" in raw_lower
        ):
            return SIGNAL_TYPES["LEADERSHIP_CHANGE"]
        if (
            "hiring" in raw_lower
            or "career" in raw_lower
            or "hiring" in text_lower
            or "jobs" in text_lower
            or "openings" in text_lower
        ):
            return SIGNAL_TYPES["HIRING"]
        if (
            "expansion" in raw_lower
            or "growth" in raw_lower
            or "opening" in text_lower
            or "expansion" in text_lower
            or "store" in text_lower
        ):
            return SIGNAL_TYPES["EXPANSION"]
        if (
            "complaint" in raw_lower
            or "review" in raw_lower
            or "sentiment" in raw_lower
            or "issue" in text_lower
            or "complaint" in text_lower
            or "delay" in text_lower
            or "shipping" in text_lower
            or "delivery" in text_lower
            or "problem" in text_lower
            or "wismo" in text_lower
        ):
            return SIGNAL_TYPES["CUSTOMER_COMPLAINT"]

        return SIGNAL_TYPES.get(raw_type.upper(), SIGNAL_TYPES["OTHER"])

    def _http_get(
        self,
        url: str,
        is_xml: bool = False,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> Optional[str]:
        """Perform an HTTP GET request with retries, timeout, and graceful failure handling.

        Args:
            url: Target URL string.
            is_xml: Flag to adjust Accept header for XML feeds.
            timeout: Timeout in seconds for the HTTP request.
            max_retries: Number of retry attempts.

        Returns:
            Optional[str]: Response text if successful, None otherwise.
        """
        headers = dict(self.headers)
        if is_xml:
            headers["Accept"] = "application/rss+xml, application/xml, text/xml"

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    return response.text
                logger.warning(
                    "HTTP %d returned while fetching %s (Attempt %d/%d)",
                    response.status_code,
                    url,
                    attempt,
                    max_retries,
                )
                if response.status_code in (404, 403, 429):
                    break
            except requests.RequestException as err:
                logger.warning(
                    "Request error fetching %s: %s (Attempt %d/%d)",
                    url,
                    err,
                    attempt,
                    max_retries,
                )
                break
        return None

    def _collect_careers(self, company_name: str) -> list[Signal]:
        """Priority 1: Collect signals from Company Careers pages.

        Args:
            company_name: Target company name.

        Returns:
            list[Signal]: Extracted career signals.
        """
        logger.info("Searching source: Company Careers...")
        signals: list[Signal] = []

        clean_name = re.sub(r"[^a-zA-Z0-9]", "", company_name.lower())
        careers_urls = [
            f"https://{clean_name}clothing.com/pages/careers",
            f"https://www.{clean_name}.com/careers",
            f"https://www.{clean_name}.com/jobs",
        ]

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for url in careers_urls:
            html = self._http_get(url, timeout=2)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                page_title = (
                    soup.title.string.strip()
                    if soup.title and soup.title.string
                    else f"{company_name} Careers"
                )
                text_content = soup.get_text()

                keywords = [
                    "hiring",
                    "careers",
                    "openings",
                    "join our team",
                    "engineering",
                    "retail",
                ]
                if any(kw in text_content.lower() for kw in keywords):
                    evidence_snippet = " ".join(text_content.split())[:250]
                    signals.append(
                        Signal(
                            company=company_name,
                            signal_type=self._map_signal_type("HIRING", page_title),
                            title=page_title,
                            evidence=evidence_snippet,
                            source="Company Careers",
                            url=url,
                            date=today_str,
                            confidence=self._determine_confidence("Company Careers"),
                        )
                    )
                    break

        return signals

    def _collect_blog(self, company_name: str) -> list[Signal]:
        """Priority 2: Collect signals from Company Blog / Journal.

        Args:
            company_name: Target company name.

        Returns:
            list[Signal]: Extracted company blog signals.
        """
        logger.info("Searching source: Company Blog...")
        signals: list[Signal] = []

        clean_name = company_name.lower().replace(" ", "")
        blog_urls = [
            f"https://{clean_name}clothing.com/blogs/journal",
            f"https://www.{clean_name}.com/blog",
        ]

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for url in blog_urls:
            html = self._http_get(url, timeout=2)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                page_title = (
                    soup.title.string.strip()
                    if soup.title and soup.title.string
                    else f"{company_name} Journal"
                )
                text_content = soup.get_text()
                evidence_snippet = " ".join(text_content.split())[:250]

                signals.append(
                    Signal(
                        company=company_name,
                        signal_type=self._map_signal_type("EXPANSION", page_title),
                        title=page_title,
                        evidence=evidence_snippet,
                        source="Company Blog",
                        url=url,
                        date=today_str,
                        confidence=self._determine_confidence("Company Blog"),
                    )
                )
                break

        return signals

    def _collect_news(self, company_name: str) -> list[Signal]:
        """Priority 3: Collect signals from News & Press Releases via RSS search queries.

        Args:
            company_name: Target company name.

        Returns:
            list[Signal]: Extracted news signals.
        """
        logger.info("Searching source: News / Press Releases...")
        signals: list[Signal] = []

        queries = [
            f"{company_name} hiring growth expansion",
            f"{company_name} funding investment logistics",
            f"{company_name} shipping delays customer complaint issue",
            f"{company_name} AfterShip Narvar tracking software",
        ]

        seen_titles: set[str] = set()

        for query in queries:
            rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"
            xml_text = self._http_get(rss_url, timeout=3, is_xml=True)
            if not xml_text:
                continue

            try:
                soup = BeautifulSoup(xml_text, "xml")
                items = soup.find_all("item")
                for item in items[:3]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    date_elem = item.find("pubDate")
                    desc_elem = item.find("description")

                    title = (
                        title_elem.text.strip() if title_elem else "News Article"
                    )
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)

                    link = link_elem.text.strip() if link_elem else rss_url
                    pub_date = (
                        date_elem.text.strip()
                        if date_elem
                        else datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    )
                    raw_desc = desc_elem.text.strip() if desc_elem else title
                    clean_desc = BeautifulSoup(raw_desc, "html.parser").get_text()

                    mapped_type = self._map_signal_type("NEWS", title)

                    signals.append(
                        Signal(
                            company=company_name,
                            signal_type=mapped_type,
                            title=title,
                            evidence=clean_desc[:250],
                            source="News / Press Releases",
                            url=link,
                            date=pub_date,
                            confidence=self._determine_confidence("News / Press Releases"),
                        )
                    )
            except Exception as err:
                logger.warning(
                    "Error parsing RSS feed for query '%s': %s", query, err
                )

        return signals

    def _collect_trustpilot(self, company_name: str) -> list[Signal]:
        """Priority 4: Collect signals from Trustpilot customer sentiment.

        Args:
            company_name: Target company name.

        Returns:
            list[Signal]: Extracted Trustpilot signals.
        """
        logger.info("Searching source: Trustpilot...")
        signals: list[Signal] = []

        clean_name = company_name.lower().replace(" ", "")
        url = f"https://www.trustpilot.com/review/{clean_name}clothing.com"

        html = self._http_get(url, timeout=2, max_retries=1)
        if not html:
            logger.warning(
                "Could not access Trustpilot for %s. Continuing gracefully...",
                company_name,
            )
            return signals

        try:
            soup = BeautifulSoup(html, "html.parser")
            text_content = soup.get_text()
            evidence_snippet = " ".join(text_content.split())[:250]
            signals.append(
                Signal(
                    company=company_name,
                    signal_type=self._map_signal_type("CUSTOMER_COMPLAINT", text_content),
                    title=f"{company_name} Customer Reviews on Trustpilot",
                    evidence=evidence_snippet,
                    source="Trustpilot",
                    url=url,
                    date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    confidence=self._determine_confidence("Trustpilot", occurrences=1),
                )
            )
        except Exception as err:
            logger.warning(
                "Error parsing Trustpilot data for %s: %s", company_name, err
            )

        return signals

    def _collect_reddit(self, company_name: str) -> list[Signal]:
        """Priority 5: Collect signals from Reddit community discussions.

        Args:
            company_name: Target company name.

        Returns:
            list[Signal]: Extracted Reddit signals.
        """
        logger.info("Searching source: Reddit...")
        signals: list[Signal] = []

        url = f"https://www.reddit.com/r/all/search.json?q={company_name}&limit=5"
        json_str = self._http_get(url, timeout=2, max_retries=1)

        if not json_str:
            logger.warning(
                "Could not access Reddit JSON for %s. Continuing gracefully...",
                company_name,
            )
            return signals

        try:
            data = json.loads(json_str)
            children = data.get("data", {}).get("children", [])
            for child in children[:3]:
                post = child.get("data", {})
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                permalink = post.get("permalink", "")
                full_url = (
                    f"https://www.reddit.com{permalink}" if permalink else url
                )
                created_utc = post.get("created_utc", 0)
                date_str = (
                    datetime.fromtimestamp(created_utc, timezone.utc).strftime(
                        "%Y-%m-%d"
                    )
                    if created_utc
                    else datetime.now(timezone.utc).strftime("%Y-%m-%d")
                )

                evidence = (title + " - " + selftext).strip()
                signals.append(
                    Signal(
                        company=company_name,
                        signal_type=self._map_signal_type("OTHER", title),
                        title=title,
                        evidence=evidence[:250],
                        source="Reddit",
                        url=full_url,
                        date=date_str,
                        confidence=self._determine_confidence("Reddit", occurrences=1),
                    )
                )
        except Exception as err:
            logger.warning("Error parsing Reddit JSON for %s: %s", company_name, err)

        return signals

    def collect_company(self, company_name: str) -> CompanySignals:
        """Collect public buying-intent signals for a single company across prioritized sources.

        Args:
            company_name: The target company name (e.g., 'Vuori').

        Returns:
            CompanySignals: Data object containing all gathered signals.
        """
        logger.info("Searching company: %s...", company_name)
        all_signals: list[Signal] = []

        # Priority 1: Company Careers
        all_signals.extend(self._collect_careers(company_name))

        # Priority 2: Company Blog
        all_signals.extend(self._collect_blog(company_name))

        # Priority 3: News / Press Releases
        all_signals.extend(self._collect_news(company_name))

        # Priority 4: Trustpilot
        all_signals.extend(self._collect_trustpilot(company_name))

        # Priority 5: Reddit
        all_signals.extend(self._collect_reddit(company_name))

        if all_signals:
            logger.info(
                "Signals detected: %d signals found for %s",
                len(all_signals),
                company_name,
            )
        else:
            logger.info("No signals found for %s", company_name)

        company_signals = CompanySignals(company=company_name, signals=all_signals)

        # Save to outputs/signals.json
        self._write_output_json(company_signals)
        logger.info("Collection complete for %s.", company_name)

        return company_signals

    def _write_output_json(self, company_signals: CompanySignals) -> None:
        """Write collected signals object to outputs/signals.json.

        Args:
            company_signals: Target CompanySignals object.
        """
        out_file = self.output_dir / "signals.json"
        try:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(company_signals.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info("Successfully saved outputs/signals.json")
        except Exception as err:
            logger.error("Failed writing signals.json: %s", err)

    def collect_all(self, company_list: list[str]) -> list[CompanySignals]:
        """Collect public buying intent signals for a list of target companies.

        Args:
            company_list: List of company names to process.

        Returns:
            list[CompanySignals]: List of collected company signals data objects.
        """
        results: list[CompanySignals] = []
        for company in company_list:
            comp_signals = self.collect_company(company)
            results.append(comp_signals)

        out_file = self.output_dir / "signals.json"
        try:
            combined_data = [cs.to_dict() for cs in results]
            output_payload = (
                combined_data[0] if len(combined_data) == 1 else combined_data
            )
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(output_payload, f, indent=2, ensure_ascii=False)
            logger.info("Successfully wrote combined output to %s", out_file)
        except Exception as err:
            logger.error("Failed writing signals.json in collect_all: %s", err)

        return results
