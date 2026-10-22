# Pitch deck source — 3 minute presentation

## Slide 1 — The gap (0:00–0:30)
**CompatibilityMatch AI** — Saudi business partnership and investment intelligence. Companies need a credible way to screen potential partners and measure whether approved relationships achieve their goals.

## Slide 2 — One lifecycle (0:30–1:00)
Discover → Analyze → Decide → Monitor. Our prototype connects pre-decision compatibility analysis to post-decision KPI tracking. The score is a transparent screening signal, not an investment promise.

## Slide 3 — How it works (1:00–1:35)
Compare two records across strategic partnership, directional equity investment, or joint venture. The same deterministic rubric ranks local candidates. Optional LLM explains opportunities and risks from supplied company descriptions; missing financial inputs stay missing.

## Slide 4 — Monitor outcomes (1:35–2:10)
Enter actual monthly performance against targets. Revenue and cost use different achievement formulas. The sample relationship and numbers are fictional. A shortfall becomes a review signal, without claiming to know its cause.

## Slide 5 — Measure the product (2:10–2:40)
A separate technical dashboard reads request counts, errors, and response times from SQLite telemetry. Diagnostic events help demonstrate failure investigation. A human review sheet checks whether AI claims are supported.

## Slide 6 — Limits and next step (2:40–3:00)
Today: synthetic data and local MVP. Next: verified official disclosures, secure multi-user workflow, and independent evaluation. CompatibilityMatch helps teams ask better questions; human management remains responsible for decisions.

# Technical Q&A preparation (10 minutes)

1. **Where does the score come from?** Version 1 weighted rubric in `app.py`; LLM never computes numeric scores. Explain weights and missing-data behavior.
2. **Why these weights?** Transparent initial product assumptions, not empirically calibrated weights. They require practitioner review and sensitivity analysis.
3. **How do you prevent hallucinated financial facts?** No financial claims are seeded; supplied business descriptions are sent to the model; Demo Mode is explicit; parse/provider failures are logged. Review remains necessary.
4. **Is it an investment recommendation?** No. The result is preliminary screening, directionally analyzes A investing in B, and omits valuation when source data is absent.
5. **How is performance measured?** Manually entered actuals compared with target, period, unit and KPI direction. Public stock data cannot reveal private agreement execution.
6. **Why distinguish technical and business monitoring?** Technical events describe the app's own reliability; KPI actuals describe the user's relationship. Separate tables and dashboard sections prevent conflation.
7. **Are monitoring figures real?** Counts/latency calculate from stored app events. The included relationship values are simulated and labeled.
8. **How did you evaluate AI quality?** Human claim-level source support review; no benchmark or accuracy is claimed. Discuss how to report reviewer agreement in future.
9. **Why not Flask/SQLAlchemy?** Deadline-focused, low-dependency local implementation using standard-library HTTP and SQLite. Trade-off: production safeguards/migrations are missing; Flask is a reasonable next refactor.
10. **What would production require?** Verified ingestion provenance, authentication/authorization, secure relationship approvals, audit retention, API timeout and usage metrics, robust validation, backups, reviewer validation, and deployment monitoring.
