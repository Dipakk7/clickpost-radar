# ClickPost Radar

> **AI-Powered Account Intelligence & Outbound Activation**

*Built as my solution for the ClickPost AI Engineer Intern Take-Home Assignment.*

> [!NOTE]
> *This repository is an independent prototype created for evaluation purposes and is not an official ClickPost product.*

ClickPost Radar is an automated sales intelligence pipeline that monitors public evidence for target accounts, scores buying intent using a transparent, explainable algorithm, and generates personalized, evidence-grounded SDR outreach copy (LinkedIn InMails & follow-up emails) for ClickPost.

---

## 🎯 Business Problem

Modern B2B Sales Development Representatives (SDRs) spend up to **65% of their day manually searching for account news**, guessing buying readiness, and sending generic cold outreach. This leads to missed sales opportunities, low response rates, and inefficient SDR workflows.

**ClickPost Radar** automates the entire prospecting workflow:
1. **Detects buying intent signals** across company careers pages, press releases, news RSS feeds, and customer channels.
2. **Scores & ranks target accounts** deterministically based on weighted signal categories.
3. **Synthesizes SDR research briefs** and personalized outreach copy grounded in verified facts.

---

## 🏗️ Architecture & Pipeline Overview

ClickPost Radar utilizes a **Simple Flat Architecture** for maximum clarity, maintainability, and rapid evaluation.

```text
                     +-----------------------+
                     |     companies.csv     |
                     +-----------+-----------+
                                 |
                                 v
                     +-----------------------+
                     |      collector.py     |
                     | (Signal Collection)   |
                     +-----------+-----------+
                                 |
                                 v  outputs/signals.json
                     +-----------------------+
                     |       scorer.py       |
                     |   (Intent Scoring)    |
                     +-----------+-----------+
                                 |
                                 v  outputs/scored_accounts.json
                     +-----------------------+
                     |      generator.py     |
                     | (SDR Outreach Engine) |
                     +-----------+-----------+
                                 |
                                 v
   +-----------------------------------------------------------+
   |                       OUTPUTS                             |
   |  • outputs/scored_accounts.csv    • research_briefs.json  |
   |  • outputs/scored_accounts.json   • outreach_messages.csv |
   +-----------------------------------------------------------+
```

---

## 📁 Repository Structure

```text
clickpost-radar/
├── companies.csv           # Input target company list (e.g. Vuori)
├── config.py              # Centralized configuration, signal taxonomy & weights
├── collector.py           # Multi-source signal collection engine (Retries & Error Handling)
├── scorer.py              # Deterministic intent scoring & account ranking engine
├── generator.py           # Evidence-grounded research brief & outreach copy generator
├── exporter.py            # Results exporter module (CSV & JSON)
├── main.py                # Pipeline entry point & orchestrator
├── requirements.txt       # Project dependencies
├── README.md              # Documentation (5-minute reviewer guide)
├── memo.md                # Architecture & technical design memo
├── .env.example           # Environment variables configuration template
├── outputs/               # Pipeline execution output directory
│   └── .gitkeep
├── sample_outputs/        # Pre-generated sample outputs for instant review
│   ├── signals.json
│   ├── scored_accounts.csv
│   ├── scored_accounts.json
│   ├── research_briefs.json
│   └── outreach_messages.csv
└── logs/                  # Application runtime logs
    └── .gitkeep
```

---

## ⚡ Quick Start & Installation

### Prerequisites
- **Python 3.11+**
- Virtual environment (`venv` or `conda`)

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/Dipakk7/clickpost-radar.git
cd clickpost-radar

# Create & activate virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

---

## 🚀 Running the Project

To execute the complete end-to-end ClickPost Radar pipeline:

```bash
python main.py
```

### Expected Log Output
```text
==================================================
ClickPost Radar — AI-Powered Account Intelligence & Outbound Activation
==================================================

[ClickPost Radar] Target Companies Loaded: ['Vuori']

[ClickPost Radar] All components successfully initialized:
  - Collector: SignalCollector
  - Scorer: IntentScorer
  - Generator: OutreachGenerator
  - Exporter: Exporter

Starting ClickPost Radar Automated Pipeline...
Collecting signals...
[ClickPost Radar] Signal Collection Completed: 1 company signal sets collected.
Scoring accounts...
[ClickPost Radar] Account Scoring Completed: 1 accounts scored & ranked.
Generating outreach...
[ClickPost Radar] SDR Outreach Generation Completed: 1 research briefs & 1 outreach payloads generated.
Export complete.

[ClickPost Radar] Pipeline execution finished successfully.
  - Signals Output: outputs\signals.json
  - Scores Output: outputs\scored_accounts.csv & outputs\scored_accounts.json
  - Research Briefs: outputs\research_briefs.json
  - Outreach Messages: outputs\outreach_messages.csv
```

---

## 📊 Sample Outputs Preview

### 1. Intent Score & Account Priority (`outputs/scored_accounts.json`)
```json
[
  {
    "company": "Vuori",
    "intent_score": 55,
    "priority": "Medium",
    "confidence": "High",
    "evidence_count": 10,
    "detected_signals": [
      "EXPANSION",
      "FUNDING",
      "HIRING",
      "LEADERSHIP_CHANGE"
    ],
    "why_now": "Recent funding combined with active hiring suggests operational expansion and increasing logistics complexity."
  }
]
```

### 2. SDR Research Brief (`outputs/research_briefs.json`)
```json
[
  {
    "company": "Vuori",
    "buying_intent_summary": "Vuori shows strong buying intent with active expansion, funding signals and notable growth across operations.",
    "key_signals": [
      "EXPANSION",
      "FUNDING",
      "HIRING",
      "LEADERSHIP_CHANGE"
    ],
    "evidence": [
      "Vuori Careers – Retail & Corporate Job Openings in Athletic Apparel.",
      "Why Upstart Athleisure Brand Vuori Is Opening So Many Stores.",
      "Vuori Announces Four C-Suite Hires."
    ],
    "why_now": "Recent funding combined with active hiring suggests operational expansion and increasing logistics complexity.",
    "suggested_persona": "VP of Supply Chain / Head of E-commerce Logistics",
    "recommended_outreach_angle": "AI-powered post-purchase tracking, carrier exception handling, and delivery experience scaling"
  }
]
```

---

## 💡 Key Design Decisions

1. **Centralized Taxonomy & Internal Filtering**: Supports six signal categories (`HIRING`, `FUNDING`, `EXPANSION`, `LEADERSHIP_CHANGE`, `CUSTOMER_COMPLAINT`, `COMPETITOR_USAGE`). Five categories triggered in the current sample dataset execution run. Internal `OTHER` categories are filtered out of all SDR-facing outputs.
2. **News Evidence Relevance Validation**: Exact quoted Google News queries (`"{company_name}"`) and post-fetch normalization check verify that target company names explicitly appear in article titles or descriptions before accepting evidence.
3. **Deterministic Intent Scoring**: Implements a transparent weighted scoring system (capped at 100) with rule-based "Why Now" explanations. No opaque AI scoring black-boxes.
4. **Dual Generator Engine & Signal-Aware Outreach**: Integrates OpenAI GPT-4o when `OPENAI_API_KEY` is present, while providing a seamless, zero-hallucination evidence-grounded synthesis engine when offline. The outreach generator adapts its messaging based on the primary verified buying signal (`HIRING`, `FUNDING`, `EXPANSION`, `LEADERSHIP_CHANGE`, `CUSTOMER_COMPLAINT`), producing context-aware SDR outreach while remaining grounded in collected evidence.
5. **Conversational SDR CTAs**: Follow-up emails use soft, permission-based value CTAs instead of rigid time-slot demands.

---

## ⚠️ Limitations & Real-World Dataset Observations

- **News Attribution & Heuristic Entity Matching**: Google News evidence undergoes relevance validation to reject false-positive articles. Entity matching uses heuristic brand token normalization, which minimizes false attributions while preserving genuine news coverage.
- **Competitor Usage Detection**: The pipeline implements competitor keyword mapping (`AfterShip`, `Narvar`, `ShipStation`, `ParcelLab`, `Wonderment`, `LateShipment`, `Shippo`, `Malomo`). Competitor usage did not trigger in this specific 25-account sample dataset because monitored competitor names were not present in collected public content.
- **Anti-Bot Defenses**: Public endpoints like Reddit and Trustpilot return HTTP 403 Forbidden under standard automated HTTP requests. Customer complaints are captured via public news RSS search queries (`"shipping delays customer complaint issue"`), while direct community endpoints are handled gracefully without crashing.
- **Future Integration**: Connect Clearbit/ZoomInfo for contact enrichment, and integrate Playwright with residential proxy pools for headless web scraping.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
