# IntentIQ Technical & Architectural Design Memo

## Problem Statement

Modern B2B Sales Development Representatives (SDRs) spend over 65% of their working hours on manual account research, searching disparate public sources, and guessing buying readiness. This inefficiency leads to delayed outreach, generic messaging, and low meeting conversion rates.

**IntentIQ** solves this problem by establishing an automated, evidence-grounded buying intent detection and SDR outreach pipeline. It continuously monitors public evidence (hiring announcements, funding rounds, leadership changes, retail store expansion), normalizes findings into a standardized signal taxonomy, calculates an explainable intent score, and generates highly targeted SDR research briefs and personalized outreach copy for ClickPost.

---

## Buying Intent Taxonomy

To prevent inconsistent, free-form signal classifications, IntentIQ establishes a centralized signal taxonomy (`config.SIGNAL_TYPES`). The pipeline supports six signal categories:

- `HIRING`: Openings in engineering, retail, logistics, and customer support indicating operational scaling.
- `FUNDING`: Capital infusions, venture investment rounds, and private equity backing indicating budget availability.
- `EXPANSION`: Retail store launches, international market entries, and warehouse infrastructure growth.
- `LEADERSHIP_CHANGE`: Executive, C-suite, and VP appointments indicating strategic operational transformations.
- `CUSTOMER_COMPLAINT`: Customer review spikes and delivery experience issues indicating immediate solution demand (captured via public news RSS search queries).
- `COMPETITOR_USAGE`: Usage of legacy or competing post-purchase tracking tools (implemented in taxonomy/mapping, though monitored competitor names were not present in this specific sample dataset).
- `OTHER`: Internal catch-all for unclassified public signals (automatically filtered from all user-facing SDR artifacts).

---

## Methodology

IntentIQ follows a modular 4-stage pipeline execution architecture:

```
[Target Accounts CSV]
         │
         ▼
 1. Signal Collection (collector.py)
    • Priority Sources: Careers ➔ Blog ➔ News RSS ➔ Trustpilot ➔ Reddit
    • Resilient HTTP Retries & Graceful Failure Handling
         │
         ▼
 2. Intent Scoring Engine (scorer.py)
    • Configurable Taxonomy Weights (CUSTOMER_COMPLAINT: +30, HIRING: +25, etc.)
    • Capped Score (0-100) & Priority Classification (High, Medium, Low)
    • Aggregated Qualitative Confidence & Rule-Based "Why Now" Generator
         │
         ▼
 3. SDR Outreach Generator (generator.py)
    • Dual Engine: OpenAI GPT-4o with Evidence-Grounded Fallback Synthesis
    • Account Research Briefs with Supporting Evidence Bullets
    • Concise LinkedIn Messages (<80 words) & Conversational Cold Emails (<150 words)
         │
         ▼
 4. Results Exporter (exporter.py)
    • Structured CSV & JSON Outputs in /outputs
```

---

## Scoring Strategy

IntentIQ implements a **deterministic, transparent, and explainable scoring algorithm**.

1. **Category Weighting**: Each unique detected signal category contributes a fixed weight defined in `config.SIGNAL_WEIGHTS`:
   - `CUSTOMER_COMPLAINT`: 30 points
   - `HIRING`: 25 points
   - `COMPETITOR_USAGE`: 25 points
   - `FUNDING`: 10 points
   - `EXPANSION`: 10 points
   - `LEADERSHIP_CHANGE`: 10 points
2. **Score Cap**: The final intent score is capped at `100` (`min(100, score)`).
3. **Priority Tiers**:
   - `80 – 100`: **High Priority**
   - `50 – 79`: **Medium Priority**
   - `0 – 49`: **Low Priority**
4. **Confidence Aggregation**: If any underlying signal is verified by official sources or multiple channels, company confidence escalates to **High**.

---

## Design Decisions

1. **Simple Flat Architecture**: Avoided deep directory nesting (`src/`, `app/`, `controllers/`) to minimize boilerplate and enable rapid evaluation during take-home review.
2. **Zero-Hallucination Fallback**: Implemented a dual outreach generator that invokes OpenAI GPT-4o when API keys exist, while seamlessly falling back to an evidence-grounded template builder if offline or unconfigured.
3. **Internal Category Isolation**: Isolated `"OTHER"` as an internal scoring bucket while strictly filtering it out from all user-facing SDR deliverables to maintain executive messaging quality.
4. **Conversational CTAs**: Replaced rigid time-slot requests ("Are you free Tuesday at 2 PM?") with value-driven, conversational permission CTAs.

---

## Trade-offs

- **Static vs. Real-Time Scraping**: Used public RSS feeds and static HTML extraction instead of headless browser rendering (Selenium/Playwright) to maximize pipeline speed, stability, and memory efficiency.
- **Rule-Based "Why Now" Summaries**: Chose deterministic template matching over non-deterministic LLM generation for intent explanations to ensure 100% reproducible and audit-safe SDR reasoning.

---

## Limitations

- **Rate Limits & Anti-Bot Protections**: Public third-party endpoints (e.g., Reddit, Trustpilot) frequently block automated scrapers with HTTP 403 Forbidden responses.
- **Domain Resolution**: Automated domain guessing (`companyname.com`) works reliably for primary consumer brands but requires a dedicated enrichment API (e.g., Clearbit, People Data Labs) for obscure enterprise names.

---

## Future Improvements

1. **Integration with B2B Data Providers**: Connect Clearbit / Apollo / ZoomInfo APIs for real-time contact enrichment (finding specific VP of Logistics email addresses).
2. **Headless Scraping & Proxy Rotation**: Integrate Playwright with residential proxy pools to bypass anti-scraping blocks on Trustpilot and G2.
3. **CRM Synchronization**: Build direct integrations with Salesforce and HubSpot to automatically create high-priority tasks for SDRs upon signal detection.
