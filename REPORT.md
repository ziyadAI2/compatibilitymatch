# Project 1 — AI Product Development and Monitoring
## CompatibilityMatch AI | concise technical report

### Problem and target users
Saudi company strategy, partnership, and investment teams need an auditable way to screen potential partners and then compare approved relationship performance against objectives. This MVP targets corporate development, strategy, and partnership managers.

### Proposed product
CompatibilityMatch provides company comparison, ranking of records in a small local dataset, three relationship types, a post-decision KPI dashboard, and a separate system telemetry view. Its value is in traceable screening and follow-up, not market coverage or investment recommendations.

### Data collection and provenance
The seeded company and relationship records are synthetic and labeled as such. Financial values are absent, not fabricated. A CSV template exposes suitable fields. A real deployment should ingest official issuer disclosures and company reports, retain source URL and publication date, validate periods/currency/units, and preserve missingness. Public filings cannot establish private relationship execution KPIs.

### AI and technical choices
Python handles routing and calculations; SQLite stores records and telemetry; Jinja2 renders RTL pages; Chart.js provides the KPI trend chart. An optional OpenAI Chat Completions call produces a JSON explanation using the supplied records. Without credentials, deterministic demo text is explicitly labeled Demo Mode. The numerical score remains Python-derived. The implementation used AI assistance for code and documentation drafting; the author should review and understand each module and run the supplied checks. Standard-library HTTP routing replaces the originally proposed Flask/SQLAlchemy stack to reduce local setup dependencies; Jinja2 remains the sole app dependency.

### Product architecture
Browser → HTTP handler → deterministic score and optional LLM → SQLite → server-rendered dashboard. See architecture and diagrams. Three configurable-in-code rubrics provide transparent sub-scores. Confidence is independent and warns on missing financial data. Equity analysis is directional. It does not calculate a valuation when market price/ownership data is absent.

### Business monitoring
A relationship references both companies, kind, date, status, and simulation marker. KPI inputs retain target, actual, unit, direction, period. Revenue uses actual/target; cost uses target/actual. A threshold under 80% is flagged for attention. The dashboard charts actual and target series. This implementation does not assert causes of deviation. The demonstration relationship is fictional.

### Technical monitoring
Application handlers write request type, status, elapsed milliseconds, details, and UTC timestamp to SQLite. The dashboard computes request total, success/failure counts, and mean response time from stored events. Diagnostic controls write simulated timeout, missing-record, invalid-input, and latency event examples. These are clearly labeled diagnostic events. Token usage, provider cost, and true provider timeout injection are not currently instrumented.

### Evaluation and actual checks
Evaluation method is a human review worksheet in README: label factual vs interpretive claims, verify facts against supplied sources, flag unsupported claims, and rate usefulness/caution. No accuracy claim is made. Automated checks cover deterministic bounded scores, the missing-financial-data penalty in investment scoring, higher/lower KPI calculations, and telemetry persistence. Executed with the bundled Python runtime: `python -m py_compile app.py` succeeded; `python -m unittest discover -s tests -v` ran 4 tests and all passed. The checks cover score repeatability/bounds, missing financial data, KPI direction, and event persistence.

### Limitations and next steps
Synthetic-only company records, no full Tadawul coverage, no authenticated users, no CSV upload, no robust approval/signature workflow, no ownership/market valuation feed, no production access controls or deployment, and no token/cost analytics. Priorities: verified data ingestion with source review; role-based access and audit history; CSV validation; real signed relationship state; milestone CRUD; provider usage telemetry; and independent reviewer evaluation.

### References
Project 1 instructions PDF supplied with the assignment (scope, dashboard, lifecycle diagrams, evaluation and presentation requirements). External datasets/benchmarks were not used. Add primary Saudi Open Data Portal and Tadawul/company disclosure references only when actual records are imported and verified.

