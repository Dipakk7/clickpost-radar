# IntentIQ

> **AI-Powered Buying Intent Detection & Personalized SDR Outreach**

IntentIQ is an automated pipeline designed to detect high-intent target accounts, score buying signals, and generate personalized sales research briefs and outreach copy (LinkedIn messages & follow-up emails) for Sales Development Representatives (SDRs).

---

## Project Overview

Modern B2B sales teams spend excessive hours manually researching target accounts and guessing buying readiness. **IntentIQ** automates buying intent detection by collecting signals across multiple channels (hiring patterns, news announcements, technological changes, competitor evaluation), scoring intent with configurable weights, and generating tailored SDR outreach copy.

---

## Architecture

IntentIQ uses a **Simple Flat Architecture** for maximum clarity, rapid prototyping, and zero overhead.

```
intentiq/
├── companies.csv       # Input list of target companies
├── config.py          # Centralized configuration, constants & signal taxonomy
├── collector.py       # Resilient multi-source signal collection engine
├── scorer.py          # Intent scoring & account ranking module placeholder
├── generator.py       # LLM outreach & research brief generator module placeholder
├── exporter.py        # Pipeline results exporter module placeholder
├── main.py            # Application entry point & pipeline orchestrator
├── requirements.txt   # Python project dependencies
├── README.md          # Project documentation
├── memo.md            # Architecture & strategy memo template
├── .env.example       # Environment variables template
├── outputs/           # Output directory for exported data (e.g. signals.json)
│   └── .gitkeep
└── logs/              # Log directory for application runtime logs
    └── .gitkeep
```

---

## Installation

### Prerequisites

- **Python 3.11+**
- Virtual environment tool (`venv` or `conda`)

### Setup Instructions

1. **Clone the repository / navigate to project directory**:
   ```bash
   git clone https://github.com/Dipakk7/IntentIQ.git
   cd IntentIQ
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```

---

## Running

To run the pipeline and collect buying intent signals for target companies (`companies.csv`), execute:

```bash
python main.py
```

### Expected Execution Log
```text
==================================================
IntentIQ — AI-Powered Buying Intent Detection & SDR Outreach
Phase 1: Project Foundation & Infrastructure Ready
==================================================

[IntentIQ] Target Companies Loaded: ['Vuori']

[IntentIQ] All components successfully initialized:
  - Collector: SignalCollector
  - Scorer: IntentScorer
  - Generator: OutreachGenerator
  - Exporter: Exporter

[IntentIQ] Phase 2 Collection Completed: 1 company signal sets collected.
[IntentIQ] Startup completed successfully. Ready for business logic implementation.
```

---

## Current Status

- **Phase 1: Foundation & Infrastructure** — ✅ **Completed**
  - Clean flat architecture established
  - Type-hinted module interfaces & docstrings defined
  - Centralized configuration and logging setup implemented

- **Phase 2: Signal Collection Engine** — ✅ **Completed**
  - Resilient multi-source evidence extraction (Careers, Blog, News RSS, Trustpilot, Reddit)
  - HTTP retries, timeouts, and graceful error handling

- **Phase 2.1: Taxonomy & Confidence Normalization** — ✅ **Completed**
  - Centralized signal taxonomy (`HIRING`, `FUNDING`, `EXPANSION`, `LEADERSHIP_CHANGE`, `CUSTOMER_COMPLAINT`, `COMPETITOR_USAGE`, `OTHER`)
  - Qualitative confidence levels (`High`, `Medium`, `Low`) based on source reliability and confirmation rules

---

## Project Roadmap

- [x] **Phase 1: Foundation & Infrastructure** — Project scaffold, interfaces, and entry point.
- [x] **Phase 2: Signal Collection Engine** — Multi-source signal collection with retries & error handling.
- [x] **Phase 2.1: Taxonomy & Confidence Normalization** — Centralized signal taxonomy & qualitative confidence scoring.
- [ ] **Phase 3: Intent Scoring** — TODO: Implement weighted scoring algorithms & account ranking.
- [ ] **Phase 4: Outreach Generation** — TODO: Integrate LLM to synthesize research briefs and SDR copy.
- [ ] **Phase 5: Export & Reporting** — TODO: Implement CSV/Markdown exporting & final pipeline automation.
