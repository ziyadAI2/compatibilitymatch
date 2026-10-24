# Project 1 report — مِشراك (CompatibilityMatch AI)

**Course:** AI Product Development and Monitoring  
**Product:** مِشراك — منصة توافق الشركات واكتشاف فرص الشراكة
**Date:** 22 October 2026

## 1. Problem and users

Saudi corporate strategy and finance teams need an early way to compare potential partners and joint ventures.

## 2. Product

The Flask MVP supports Gemini-evaluated company comparison for strategic partnerships and joint ventures when configured, local catalogue discovery, reports, and a separate technical system monitor. Role-based access supports regular users and administrators.

## 3. Data and provenance

- The database contains **27 actual Saudi Exchange Main Market listed issuers/securities**: 4 telecommunications, 7 energy/utilities/oil-services, 8 petrochemical, and 8 banking.
- Names and trading symbols are referenced to the [Saudi Exchange Issuer Directory](https://www.saudiexchange.sa/wps/portal/saudiexchange/trading/participants-directory/issuer-directory?locale=en). The app links this source from the company register.
- Short activity summaries and sector groupings are curated for the MVP. There is no live exchange synchronization.
- No company financial statements or current market valuation are fabricated. Financial analysis criteria are unavailable until a verified source and fiscal period are imported.

## 4. AI and development tools

Python, Flask, SQLAlchemy, SQLite, Jinja2, HTML/CSS/JavaScript, Chart.js, pytest, and Cursor-assisted vibe coding. With a configured key, Gemini receives company facts and criterion weights, then returns scores and structured Arabic analysis. The app validates the returned criteria and computes the weighted total from Gemini's scores. It does not send precomputed criterion scores. Without a key, deterministic rules produce a labeled Demo Mode result. Admin monitoring counts Gemini HTTP attempts separately and records provider-reported usage when available. Admin-entered API keys are Fernet-encrypted in SQLite; the Fernet key is held outside the database in deployment secrets.

AI-assisted work included initial scaffolding, templates, and documentation. Product requirements, company sourcing policy, scoring flow, data labels, and scenario values were checked and corrected in the implementation. The latest local Gemini requests failed with connection errors, so a successful live response and its factual quality have not yet been evaluated.

## 5. Scoring and evaluation

Two documented weight sets cover partnership and joint venture. In live comparison mode Gemini estimates each criterion from the company facts and supplied evidence; Python validates its response and calculates a weighted total using those fixed weights (`gemini-ai-v1`). If a criterion has no defensible evidence, the model may return null and the available weight coverage is reported. The separate discovery ranking and no-key Demo Mode use `cm-score-v2`, a heuristic that normalizes Arabic and English activity descriptions and extracts capabilities. Neither live AI scores nor heuristic rankings are validated empirical predictions; both require human review.

Automated tests cover scoring, absent financials, all 702 ordered pairs across the 27-company catalogue for both supported relationship types, every company as a discovery starting point, ranking/comparison consistency, new-company eligibility, technical monitoring events, Demo Mode, and API timeout simulation. Human factual support review template: `docs/AI_EVALUATION.md`.

Gemini API tests use mocked HTTP responses for success, absent credentials, 401/403, 429, timeout, and malformed structured output. Recent real requests were attempted but could not connect to the provider; a successful live analysis still needs verification in an environment with outbound access.

**Executed 22 October 2026:** test results are maintained by the current automated run; no live Gemini benchmark or human factual-claim review is claimed. Automated tests do not establish real-world predictive accuracy.

## 6. Technical monitoring

Application requests and validation errors are written to `technical_monitoring_events`; the System Monitoring Dashboard aggregates persisted events, latency, errors, AI failures, tokens/cost when available, and data freshness. Startup does not insert fake system telemetry. Simulation controls create explicit test events.

## 7. Architecture and diagrams

Single-process Flask app and SQLite database. Company analyses and technical telemetry use separate models and calculations. See `docs/ARCHITECTURE.md` and Mermaid diagrams in `docs/DIAGRAMS.md`.

## 8. Limitations

- No automatic Tadawul feed, price feed, or public-filings synchronization.
- No financial ratios or investment valuation until official financial data is loaded.
- Discovery and no-key demo rankings are heuristic; they require domain validation and human review. On the current catalogue snapshot, among 351 unordered company pairs the partnership heuristic yielded 104 distinct rounded scores and the joint-venture heuristic 105.
- Gemini's criterion scores are model judgments, not audited business results, and require fact checking and subject-matter review.
- Company activity summaries are concise curated records rather than complete official filings.
- The system still lacks automatic issuer-data synchronization and verified financial statements.
- LLM factual quality requires human review and a configured API key.

Future work: validated financial imports, stronger issuer-specific sources, an audited review dataset, and tested decision thresholds.
