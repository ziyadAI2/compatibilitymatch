# Implemented technical diagrams

## Development flow
```mermaid
flowchart LR
 A[Requirements] --> B[Data preparation: synthetic seed + provenance fields]
 B --> C[Backend development: HTTP handlers + SQLite]
 C --> D[AI integration: optional JSON API, deterministic demo mode]
 D --> E[Unit tests]
 E --> F[Debugging from test and event logs]
 F --> G[Local deployment: Python server]
 G --> H[Maintenance: review telemetry, sources, and rubric]
```

## Monitoring flow
```mermaid
flowchart LR
 P[Analysis / KPI / diagnostic request] --> C[Request handler + telemetry collector]
 C --> DB[(SQLite events table)]
 DB --> M[Dashboard calculations: totals, failures, mean latency]
 M --> UI[System Monitoring Dashboard]
 C --> A[Business target/actual validation]
 A --> K[(SQLite KPI actuals)]
 K --> V[Achievement and variance calculations]
 V --> AL[Attention status]
 AL --> S[Evidence-based AI summary on analysis; management review]
 K --> B[Partnership dashboard and actual-vs-target chart]
```

Business status flow begins from a relationship recorded as approved/signed by the user; the seeded sample is explicitly marked simulated. The current UI treats KPI updates as user-entered measurements and does not infer causes.
