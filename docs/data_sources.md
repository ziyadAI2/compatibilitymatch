# Data sources and evidence boundaries

## Government open-data portals

The My.gov.sa page about open data explains the Saudi open-data policy, reuse
license, and the National Open Data Platform. It is a guidance page, not a
company financial dataset. The platform is [open.data.gov.sa](https://open.data.gov.sa/ar/home),
where publishers provide dataset files and metadata.

## Company records

The company catalogue contains 27 listed Saudi companies. Names and ticker
symbols are linked to the Saudi Exchange issuer directory. Company-specific
annual figures are stored in `company_financials`; the source URL is stored on
each record and in `company_sources`. A source link to an issuer directory is
evidence for issuer identity/listing; it does not by itself substantiate every
description or financial metric. Financial numbers must be checked against the
company's annual filing or Saudi Exchange financial disclosure.

## Sector context imported

`market_context_indicators` contains 20 records from the General Authority for
Statistics (GASTAT), [Structural Business Statistics 2024](https://www.stats.gov.sa/documents/20117/2435267/Structural%2BBusiness%2BStatistics%2B2024%2BEN.pdf/3cb467dd-e8b0-881c-b81a-4195c6564d41?t=1761717962636).
The records include national totals and operating-revenue/expenditure shares
by economic activity. They are aggregate sector statistics, not company-level
financials, and are not substituted into company scoring.

## Simulated values

Any generated scenario data must be labeled `is_synthetic = true`, identified
as a simulation in the user interface and excluded from factual claims. It
must never be represented as a filing or official statistic.
