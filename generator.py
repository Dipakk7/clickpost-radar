"""ClickPost Radar Outreach Generator Engine.

This module implements the OutreachGenerator class responsible for generating
SDR-ready research briefs, personalized LinkedIn outreach messages, and follow-up emails
grounded strictly in collected buying-intent evidence.

Refactored in Phase 4.1 for evidence grounding, "OTHER" category filtering,
evidence bullet extraction, and conversational non-pushy email CTAs.
"""

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import os
from typing import Any, Optional
import pandas as pd
from dotenv import load_dotenv

from config import OUTPUT_DIRECTORY, TOP_ACCOUNTS

# Load environment variables
load_dotenv()

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class ResearchBrief:
    """Represents a structured account research brief for SDRs."""

    company: str
    buying_intent_summary: str
    key_signals: list[str]
    evidence: list[str]
    why_now: str
    suggested_persona: str
    recommended_outreach_angle: str

    def to_dict(self) -> dict[str, Any]:
        """Convert ResearchBrief instance to dictionary format."""
        return asdict(self)


@dataclass
class OutreachMessage:
    """Represents SDR outreach copy including LinkedIn messages and cold email templates."""

    company: str
    linkedin_message: str
    email_subject: str
    followup_email: str

    def to_dict(self) -> dict[str, Any]:
        """Convert OutreachMessage instance to dictionary format."""
        return asdict(self)


class OutreachGenerator:
    """Generator engine for creating personalized sales research briefs and SDR outreach copy."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize OutreachGenerator with OpenAI API client setup and output directory.

        Args:
            output_dir: Directory path where generated outputs will be stored.
        """
        self.output_dir = output_dir or OUTPUT_DIRECTORY
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = None

        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=self.api_key)
                logger.info(
                    "OutreachGenerator initialized with OpenAI API client (%s).",
                    self.model,
                )
            except Exception as err:
                logger.warning(
                    "Failed to initialize OpenAI client: %s. Falling back to deterministic builder.",
                    err,
                )
        else:
            logger.info(
                "OutreachGenerator initialized in template-synthesis mode (No OpenAI API key provided)."
            )

    def _clean_signals(self, detected_signals: list[str]) -> list[str]:
        """Filter out internal 'OTHER' taxonomy from user-facing signal lists.

        Args:
            detected_signals: List of detected signal taxonomy strings.

        Returns:
            list[str]: Filtered signal list or placeholder if empty.
        """
        cleaned = [sig for sig in detected_signals if sig != "OTHER"]
        if not cleaned:
            return ["No high-confidence buying intent signals detected."]
        return cleaned

    def _format_possessive(self, company_name: str) -> str:
        """Format possessive company name cleanly (e.g., Rothy's -> Rothy's, James -> James', Nike -> Nike's)."""
        company = company_name.strip()
        if company.endswith("'s") or company.endswith("’s"):
            return company
        if company.endswith("s") or company.endswith("S"):
            return f"{company}'"
        return f"{company}'s"

    def _truncate_at_word_boundary(self, text: str, max_chars: int = 80) -> str:
        """Safely truncate text at word boundaries without cutting words or ending on dangling prepositions/conjunctions."""
        text = text.strip()
        if len(text) <= max_chars:
            res = text
        else:
            truncated = text[:max_chars]
            last_space = truncated.rfind(" ")
            if last_space > 20:
                truncated = truncated[:last_space]
            res = truncated.rstrip(".,;:-—'\" ")

        stop_words = {"to", "as", "it", "in", "at", "of", "and", "or", "the", "a", "an", "is", "for", "with", "by", "on"}
        words = res.split()
        while words and words[-1].lower().strip(".,;:-—'\"") in stop_words:
            words.pop()
        return " ".join(words).rstrip(".,;:-—'\" ")

    def _extract_evidence_bullets(
        self, signals: list[dict[str, Any]], max_bullets: int = 5
    ) -> list[str]:
        """Extract up to max_bullets concise, non-boilerplate evidence bullets directly from collected signals.

        Args:
            signals: List of collected signal dictionaries.
            max_bullets: Maximum number of evidence bullets.

        Returns:
            list[str]: Extracted evidence bullet strings.
        """
        bullets: list[str] = []
        seen: set[str] = set()

        for sig in signals:
            title = sig.get("title", "").strip()
            evidence_text = sig.get("evidence", "").strip()

            candidate = title if title else evidence_text
            if not candidate:
                continue

            # Strip website source suffixes cleanly
            clean_fact = candidate.split(" - ")[0].split(" | ")[0].strip()
            clean_lower = clean_fact.lower()

            # Filter out generic website boilerplate, navigation headers, or company name titles
            if (
                len(clean_fact) < 15
                or "accessibility statement" in clean_lower
                or "cookie policy" in clean_lower
                or "journal" in clean_lower and len(clean_fact) < 30
            ):
                continue

            if not clean_fact.endswith("."):
                clean_fact += "."

            if clean_lower not in seen:
                seen.add(clean_lower)
                bullets.append(clean_fact)
                if len(bullets) >= max_bullets:
                    break

        if not bullets:
            bullets = ["Monitored public evidence indicates ongoing market expansion."]

        return bullets

    def _call_llm(
        self, prompt: str, system_prompt: str, max_tokens: int = 300
    ) -> Optional[str]:
        """Call OpenAI LLM API if client is available.

        Args:
            prompt: User prompt string.
            system_prompt: System prompt string.
            max_tokens: Maximum response tokens.

        Returns:
            Optional[str]: LLM response text or None if unavailable/failed.
        """
        if not self.client:
            return None

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as err:
            logger.warning(
                "LLM API call failed: %s. Using evidence-grounded fallback builder.",
                err,
            )
            return None

    def generate_research_brief(
        self, company_score: dict[str, Any], signals: list[dict[str, Any]]
    ) -> ResearchBrief:
        """Generate a concise account research brief with an Evidence section (max 150 words).

        Args:
            company_score: Dictionary of company intent score and metadata.
            signals: List of collected signal dictionaries.

        Returns:
            ResearchBrief: Structured research brief object.
        """
        company = company_score.get("company", "Target Company")
        logger.info("Generating research brief for %s...", company)

        raw_key_signals = company_score.get("detected_signals", [])
        clean_key_signals = self._clean_signals(raw_key_signals)
        evidence_bullets = self._extract_evidence_bullets(signals, max_bullets=5)

        why_now = company_score.get(
            "why_now",
            "Public signals indicate operational growth and category evaluation potential.",
        )

        evidence_str = "; ".join(evidence_bullets[:3])

        system_prompt = (
            "You are a Senior SDR Strategist creating concise account research briefs. "
            "Never use the word OTHER in your output."
        )
        user_prompt = (
            f"Create a structured research brief for {company} based strictly on evidence:\n"
            f"- Key Signals: {', '.join(clean_key_signals)}\n"
            f"- Why Now: {why_now}\n"
            f"- Supporting Evidence Bullets: {evidence_str}\n\n"
            f"Respond in JSON with fields: buying_intent_summary, suggested_persona, recommended_outreach_angle. Max 150 words."
        )

        llm_resp = self._call_llm(user_prompt, system_prompt)
        if llm_resp:
            try:
                data = json.loads(llm_resp)
                return ResearchBrief(
                    company=company,
                    buying_intent_summary=data.get(
                        "buying_intent_summary",
                        f"{company} is experiencing significant market expansion.",
                    ),
                    key_signals=clean_key_signals,
                    evidence=evidence_bullets,
                    why_now=why_now,
                    suggested_persona=data.get(
                        "suggested_persona", "VP of Supply Chain & Operations"
                    ),
                    recommended_outreach_angle=data.get(
                        "recommended_outreach_angle",
                        "Post-purchase delivery tracking and logistics experience automation",
                    ),
                )
            except Exception:
                pass

        # Evidence-grounded fallback
        intent_summary = (
            f"{company} shows strong buying intent with active {', '.join(clean_key_signals[:2]).lower()} signals "
            f"and notable growth across operations."
        )
        suggested_persona = "VP of Supply Chain / Head of E-commerce Logistics"
        outreach_angle = (
            "AI-powered post-purchase tracking, carrier exception handling, "
            "and delivery experience scaling"
        )

        return ResearchBrief(
            company=company,
            buying_intent_summary=intent_summary,
            key_signals=clean_key_signals,
            evidence=evidence_bullets,
            why_now=why_now,
            suggested_persona=suggested_persona,
            recommended_outreach_angle=outreach_angle,
        )

    def _determine_primary_signal(
        self, company_score: dict[str, Any], meaningful_mention: str
    ) -> str:
        """Determine primary buying signal based on evidence mention and detected taxonomy priority."""
        text_lower = meaningful_mention.lower()

        # 1. Match against evidence headline text
        if any(w in text_lower for w in ["complaint", "delay", "issue", "problem"]):
            return "CUSTOMER_COMPLAINT"
        if any(w in text_lower for w in ["cfo", "ceo", "chief", "names", "appoint", "president", "vp"]):
            return "LEADERSHIP_CHANGE"
        if any(w in text_lower for w in ["raise", "funding", "million", "$", "capital", "series", "investment"]):
            return "FUNDING"
        if any(w in text_lower for w in ["hiring", "job", "career", "opening", "team"]):
            return "HIRING"
        if any(w in text_lower for w in ["expand", "expansion", "international", "pop-up", "retail", "store", "launch"]):
            return "EXPANSION"

        # 2. Fall back to taxonomy priority hierarchy
        detected = company_score.get("detected_signals", [])
        priority_order = [
            "CUSTOMER_COMPLAINT",
            "EXPANSION",
            "FUNDING",
            "LEADERSHIP_CHANGE",
            "HIRING",
        ]
        for sig in priority_order:
            if sig in detected:
                return sig

        return "GENERAL_GROWTH"

    def _get_signal_value_proposition(
        self, company: str, primary_signal: str
    ) -> dict[str, str]:
        """Generate signal-specific value propositions tailored to the primary buying signal."""
        possessive = self._format_possessive(company)

        if primary_signal == "CUSTOMER_COMPLAINT":
            return {
                "linkedin": (
                    f"Improving post-purchase shipping visibility and proactive exception handling can significantly "
                    f"reduce WISMO support tickets while protecting customer satisfaction."
                ),
                "email_body": (
                    f"ClickPost is an AI-powered post-purchase logistics platform designed to resolve delivery exceptions, "
                    f"reduce 'Where Is My Order?' (WISMO) support tickets by 40%, and protect customer retention."
                ),
            }
        elif primary_signal == "EXPANSION":
            return {
                "linkedin": (
                    f"Expanding into new markets and retail channels introduces logistics complexity across carriers. "
                    f"ClickPost helps high-growth retail brands automate multi-carrier shipment tracking and NDR resolution."
                ),
                "email_body": (
                    f"ClickPost is an AI-powered post-purchase logistics platform designed to streamline multi-carrier tracking, "
                    f"reduce 'Where Is My Order?' (WISMO) support tickets by 40%, and automate exception handling across expanding networks."
                ),
            }
        elif primary_signal == "FUNDING":
            return {
                "linkedin": (
                    f"Growth capital often drives rapid customer acquisition and higher shipment volumes. ClickPost helps scaling "
                    f"retail brands automate post-purchase delivery tracking without swelling support costs."
                ),
                "email_body": (
                    f"ClickPost is an AI-powered post-purchase logistics platform designed to support rapid order volume scaling, "
                    f"reduce 'Where Is My Order?' (WISMO) support tickets by 40%, and keep customer service operations lean."
                ),
            }
        elif primary_signal == "LEADERSHIP_CHANGE":
            return {
                "linkedin": (
                    f"Leadership transitions create ideal opportunities to modernize customer operations. ClickPost helps "
                    f"retail brands streamline post-purchase delivery experience and automate exception handling."
                ),
                "email_body": (
                    f"ClickPost is an AI-powered post-purchase logistics platform designed to modernize delivery tracking, "
                    f"reduce 'Where Is My Order?' (WISMO) support tickets by 40%, and establish scalable post-purchase operations."
                ),
            }
        elif primary_signal == "HIRING":
            return {
                "linkedin": (
                    f"As your team expands to support growing order volume, maintaining a seamless post-purchase experience "
                    f"is essential. ClickPost automates shipment tracking and delivery exception resolution."
                ),
                "email_body": (
                    f"ClickPost is an AI-powered post-purchase logistics platform designed to automate order tracking, "
                    f"reduce 'Where Is My Order?' (WISMO) support tickets by 40%, and empower scaling logistics operations teams."
                ),
            }
        else:
            return {
                "linkedin": (
                    f"As {possessive} customer volume scales, maintaining a seamless post-purchase delivery experience "
                    f"becomes critical for retention. ClickPost helps high-growth retail brands automate shipment tracking."
                ),
                "email_body": (
                    f"ClickPost is an AI-powered post-purchase logistics platform designed to automate order tracking, "
                    f"reduce 'Where Is My Order?' (WISMO) support tickets by 40%, and streamline delivery exception management."
                ),
            }

    def generate_linkedin_message(
        self, company_score: dict[str, Any], signals: list[dict[str, Any]]
    ) -> str:
        """Generate a personalized, natural LinkedIn outreach message (max 80 words).

        Args:
            company_score: Dictionary of company intent score and metadata.
            signals: List of collected signal dictionaries.

        Returns:
            str: Personalized LinkedIn message snippet.
        """
        company = company_score.get("company", "Target Company")
        logger.info("Generating LinkedIn message for %s...", company)

        possessive_company = self._format_possessive(company)
        raw_key_signals = company_score.get("detected_signals", [])
        clean_key_signals = self._clean_signals(raw_key_signals)

        evidence_bullets = self._extract_evidence_bullets(signals, max_bullets=2)

        meaningful_mention = ""
        for bullet in evidence_bullets:
            clean = bullet.rstrip(".")
            if len(clean) > 20 and clean.lower() != company.lower():
                meaningful_mention = self._truncate_at_word_boundary(clean, max_chars=75)
                break

        if meaningful_mention:
            intro_clause = f"noticed your recent momentum regarding {meaningful_mention}."
        else:
            intro_clause = f"noticed {possessive_company} recent operational growth and expansion milestones."

        primary_signal = self._determine_primary_signal(company_score, meaningful_mention)
        val_prop = self._get_signal_value_proposition(company, primary_signal)

        system_prompt = (
            "You are an expert B2B SDR writing short, human LinkedIn connection messages. "
            "Never use the word OTHER."
        )
        user_prompt = (
            f"Write a natural LinkedIn message for a decision maker at {company}.\n"
            f"Reference this real signal: {meaningful_mention or 'recent growth milestones'}.\n"
            f"Tie it to post-purchase delivery & shipping tracking optimization (ClickPost).\n"
            f"Constraint: Maximum 80 words. End with a soft call to connect."
        )

        llm_resp = self._call_llm(user_prompt, system_prompt, max_tokens=150)
        if llm_resp:
            return llm_resp

        # Evidence-grounded fallback snippet (max 80 words)
        return (
            f"Hi team at {company}, {intro_clause} "
            f"{val_prop['linkedin']} "
            f"Would love to connect and share a quick note on how we support scaling brands."
        )

    def generate_followup_email(
        self, company_score: dict[str, Any], signals: list[dict[str, Any]]
    ) -> dict[str, str]:
        """Generate a cold follow-up email with a conversational, evidence-driven CTA (max 150 words).

        Args:
            company_score: Dictionary of company intent score and metadata.
            signals: List of collected signal dictionaries.

        Returns:
            dict[str, str]: Dictionary containing 'subject' and 'followup_email'.
        """
        company = company_score.get("company", "Target Company")
        logger.info("Generating follow-up email for %s...", company)

        possessive_company = self._format_possessive(company)
        evidence_bullets = self._extract_evidence_bullets(signals, max_bullets=2)

        meaningful_mention = ""
        for bullet in evidence_bullets:
            clean = bullet.rstrip(".")
            if len(clean) > 20 and clean.lower() != company.lower():
                meaningful_mention = self._truncate_at_word_boundary(clean, max_chars=75)
                break

        if meaningful_mention:
            momentum_clause = f"specifically {meaningful_mention}"
        else:
            momentum_clause = "specifically your recent operational growth and expansion milestones"

        primary_signal = self._determine_primary_signal(company_score, meaningful_mention)
        val_prop = self._get_signal_value_proposition(company, primary_signal)

        system_prompt = (
            "You are an expert B2B SDR writing personalized cold outreach emails. "
            "Never use the word OTHER."
        )
        user_prompt = (
            f"Write a cold email to {company} based on this signal: {meaningful_mention or 'recent growth milestones'}.\n"
            f"Explain how ClickPost (AI post-purchase & logistics tracking platform) helps.\n"
            f"Use a conversational, non-pushy CTA: 'If improving post-purchase visibility and reducing delivery support tickets is a priority this quarter, I'd be happy to share how brands with similar growth profiles use ClickPost. Would you be open to a short conversation?'\n"
            f"Constraint: Maximum 150 words.\n"
            f"Return JSON with keys: subject, followup_email."
        )

        llm_resp = self._call_llm(user_prompt, system_prompt, max_tokens=250)
        if llm_resp:
            try:
                data = json.loads(llm_resp)
                return {
                    "subject": data.get(
                        "subject", f"Scaling {possessive_company} post-purchase experience"
                    ),
                    "followup_email": data.get("followup_email", ""),
                }
            except Exception:
                pass

        # Evidence-grounded fallback with conversational, non-pushy CTA
        subject = f"Scaling {possessive_company} post-purchase customer experience"
        email_body = (
            f"Hi {company} Team,\n\n"
            f"Following up on {possessive_company} recent momentum—{momentum_clause}. "
            f"Maintaining a flawless post-purchase customer journey is essential as customer expectations increase.\n\n"
            f"{val_prop['email_body']}\n\n"
            f"If improving post-purchase visibility and reducing delivery support tickets is a priority this quarter, "
            f"I'd be happy to share how brands with similar growth profiles use ClickPost.\n\n"
            f"Would you be open to a short conversation?\n\n"
            f"Best regards,\nSDR Team @ ClickPost"
        )

        return {"subject": subject, "followup_email": email_body}

    def process_all(
        self,
        scored_file: Path | str | None = None,
        signals_file: Path | str | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Load scored accounts and signals, generate SDR research briefs & outreach copy, and export outputs.

        Args:
            scored_file: Path to scored_accounts.json. Defaults to outputs/scored_accounts.json.
            signals_file: Path to signals.json. Defaults to outputs/signals.json.

        Returns:
            tuple[list[dict], list[dict]]: Generated briefs list and outreach messages list.
        """
        logger.info("Loading ranked accounts...")

        sc_path = Path(scored_file or (self.output_dir / "scored_accounts.json"))
        sig_path = Path(signals_file or (self.output_dir / "signals.json"))

        if not sc_path.exists():
            logger.error("Scored accounts file not found at %s", sc_path)
            return [], []

        try:
            with open(sc_path, "r", encoding="utf-8") as f:
                scored_data = json.load(f)
        except Exception as err:
            logger.error("Failed loading %s: %s", sc_path, err)
            return [], []

        # Load signals map
        signals_by_company: dict[str, list[dict[str, Any]]] = {}
        if sig_path.exists():
            try:
                with open(sig_path, "r", encoding="utf-8") as f:
                    sig_raw = json.load(f)
                sig_list = [sig_raw] if isinstance(sig_raw, dict) else sig_raw
                for item in sig_list:
                    cname = item.get("company", "")
                    signals_by_company[cname] = item.get("signals", [])
            except Exception as err:
                logger.warning("Error loading signals.json: %s", err)

        briefs_list: list[dict[str, Any]] = []
        outreach_list: list[dict[str, Any]] = []

        scored_list = [scored_data] if isinstance(scored_data, dict) else scored_data
        top_ranked_accounts = scored_list[:TOP_ACCOUNTS]

        for account in top_ranked_accounts:
            company = account.get("company", "Unknown")
            comp_signals = signals_by_company.get(company, [])

            try:
                # 1. Research Brief
                brief = self.generate_research_brief(account, comp_signals)
                briefs_list.append(brief.to_dict())

                # 2. LinkedIn Message
                linkedin_msg = self.generate_linkedin_message(account, comp_signals)

                # 3. Follow-up Email
                email_dict = self.generate_followup_email(account, comp_signals)

                outreach = OutreachMessage(
                    company=company,
                    linkedin_message=linkedin_msg,
                    email_subject=email_dict["subject"],
                    followup_email=email_dict["followup_email"],
                )
                outreach_list.append(outreach.to_dict())

            except Exception as err:
                logger.error(
                    "Failed generation for company %s: %s. Continuing remaining accounts...",
                    company,
                    err,
                )

        # Export outputs/research_briefs.json
        json_out = self.output_dir / "research_briefs.json"
        try:
            with open(json_out, "w", encoding="utf-8") as f:
                json.dump(briefs_list, f, indent=2, ensure_ascii=False)
            logger.info("Successfully exported %s", json_out)
        except Exception as err:
            logger.error("Failed exporting research_briefs.json: %s", err)

        # Export outputs/outreach_messages.csv
        csv_out = self.output_dir / "outreach_messages.csv"
        try:
            df = pd.DataFrame(outreach_list)
            df.to_csv(csv_out, index=False, encoding="utf-8")
            logger.info("Successfully exported %s", csv_out)
        except Exception as err:
            logger.error("Failed exporting outreach_messages.csv: %s", err)

        logger.info("Export completed.")
        return briefs_list, outreach_list
