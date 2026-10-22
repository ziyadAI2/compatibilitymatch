# System architecture

## Product request path
Browser (Arabic RTL) → Python HTTP handler → deterministic scoring + optional Gemini `generateContent` JSON REST call (preferred) or OpenAI Chat Completions fallback → SQLite (`companies`, `analyses`, `relationships`, `kpis`, `milestones`, `events`) → Jinja2 HTML response. Chart.js renders the submitted relationship KPI series.

## Business monitoring
A relationship row references two companies and carries relationship type/status/simulation marker. KPI rows store target, unit, direction, period, and entered actual. Server computes target achievement and labels low attainment as needing attention. Historical KPI rows are charted. The demo relationship has synthetic values only. No external public disclosure is treated as evidence of private agreement execution.

## Technical monitoring
Analysis, KPI, failure, and simulation handlers write real event records with status, elapsed milliseconds, detail and UTC timestamp. The dashboard calculates request totals, successes, failures, and mean latency from those rows at page load. Token usage and cost are not currently collected.

## AI safety and errors
No provider key: deterministic Demo Mode. With `GEMINI_API_KEY`, the app uses Google's `generateContent` REST endpoint with JSON response format; Gemini takes priority if both provider keys exist. Otherwise, `OPENAI_API_KEY` enables the OpenAI fallback. The model receives company records and score components; its response must pass JSON shape validation. Provider/JSON failure returns an HTTP error and persists a failure event. Numerical scores never come from the LLM. Factual financial data is not supplied when absent. Keys are read only from environment variables.
