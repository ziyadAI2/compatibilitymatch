# Implemented technical diagrams

## Integrated development and monitoring flow
```mermaid
flowchart TD
 REQ[Requirements and data] --> CODE[Implement app and scoring]
 CODE --> TEST[Unit tests and workflow review]
 TEST --> GH[GitHub main]
 GH --> RENDER[Render build and start]
 RENDER --> APP[Running service on 0.0.0.0 and PORT]
 APP --> ROUTES[Analysis, relationship, KPI, and diagnostic routes]
 ROUTES --> EVENTS[(SQLite events)]
 ROUTES --> KPI[(SQLite KPI rows)]
 EVENTS --> METRICS[Counts, failures, mean latency]
 KPI --> BUSINESS[KPI achievement and dashboard chart]
 METRICS --> ADMIN[Admin user dashboard view]
 BUSINESS --> ADMIN
 ADMIN --> REVIEW[Review events, KPIs, and analysis]
 REVIEW --> CODE
```

The admin user is shown as a dashboard viewer. The current application does not enforce login or admin-only permissions.

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
 UI --> ADM[Admin user reviews metrics and events]
 C --> A[Business target/actual validation]
 A --> K[(SQLite KPI actuals)]
 K --> V[Achievement and variance calculations]
 V --> AL[Attention status]
 AL --> ADM
 K --> B[Partnership dashboard and actual-vs-target chart]
 B --> ADM
```

Business status flow begins from a relationship recorded as approved/signed by the user; the seeded sample is explicitly marked simulated. The current UI treats KPI updates as user-entered measurements and does not infer causes. The admin user in this diagram is an operational viewer only: the app currently has no login, role checks, or admin-only authorization.
