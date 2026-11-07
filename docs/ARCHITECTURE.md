# Technical Architecture & Pipeline Design
## Enterprise Data Ingestion & Reconciliation Platform

```
+---------------------------------------------------------------------------------------------------+
|                                      INGESTION & STAGING LAYER                                    |
|                                                                                                   |
|  Source A (CSV/TSV/XLSX)            Source B (CRM Excel)            Source C (Sales Ledger JSON)  |
|         │                                    │                                    │               |
|         ▼                                    ▼                                    ▼               |
|  [ FileDetector ]                     [ FileDetector ]                     [ FileDetector ]       |
|  - SHA-256 Hashing                    - Metadata Sniffing                  - UTF-8 Validation     |
|  - Delimiter Detection (\t)           - Schema Extraction                  - Structure Check      |
|         │                                    │                                    │               |
|         ▼                                    ▼                                    ▼               |
|  [ DataReader ]                       [ DataReader ]                       [ DataReader ]         |
|  - High-perf DataFrame Load           - Excel Engine (openpyxl)            - Vectorized JSON Parse|
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                  VALIDATION & PROFILING LAYER                                     |
|                                                                                                   |
|                                     [ DataProfiler ]                                              |
|                                 - Statistical summary (IQR)                                       |
|                                 - Null and anomaly detection                                      |
|                                                 │                                                 |
|                                                 ▼                                                 |
|                                     [ ValidationEngine ]                                          |
|                                 - Birth Year bounds (1920-2008)                                   |
|                                 - Non-negative constraints                                        |
|                                 - Income Policy (ACCEPT/QUARANTINE)                               |
|                                                 │                                                 |
|                           ┌─────────────────────┴─────────────────────┐                           |
|                           ▼                                           ▼                           |
|                 [ Quarantined Records ]                             [ Valid Records ]             |
|                 - Isolated CSV & JSON Logs                          - Passed to Cleaning Engine   |
|                 - Persisted in DB Audit                             - Ready for Staging           |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                    TRANSFORMATION & STAGING                                       |
|                                                                                                   |
|                                     [ DataCleaner ]                                               |
|                                 - ISO-8601 Date Parsing (YYYY-MM-DD)                              |
|                                 - Education & Marital Status Normalization                        |
|                                 - Feature Engineering (Age, Total Spend, Dependents)              |
|                                                 │                                                 |
|                                                 ▼                                                 |
|                                     [ DataStandardizer ]                                          |
|                                 - Staged records written to data/staging/                         |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                     PERSISTENCE & STORAGE                                         |
|                                                                                                   |
|                                     [ DatabaseManager ]                                           |
|                           SQLite Warehouse / PostgreSQL Connection Pool                           |
|                                                 │                                                 |
|       ┌──────────────────┬──────────────────────┴──────────────────────┬──────────────────┐       |
|       ▼                  ▼                                             ▼                  ▼       |
| [ customer_demo ]  [ customer_crm ]                               [ customer_tx ]   [ audit_logs ]|
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                MULTI-SOURCE RECONCILIATION ENGINE                                 |
|                                                                                                   |
|                                     [ EntityMatcher ]                                             |
|                                 - Exact Primary Key Match (customer_id)                           |
|                                 - Cross-Source Set Coverage                                       |
|                                                 │                                                 |
|                                                 ▼                                                 |
|                                     [ ConflictResolver ]                                          |
|                                 - Contact Info Priority: CRM > Demographics                       |
|                                 - Demographic Master: Source A                                    |
|                                 - Transaction Aggregate Calculation                               |
|                                 - Spend Variance Auditing                                         |
|                                                 │                                                 |
|                                                 ▼                                                 |
|                                     [ Golden Master Record ]                                      |
|                                 Table: `canonical_customers`                                      |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                   REPORTING & AUDIT GENERATION                                    |
|                                                                                                   |
|  - DATA_QUALITY_AUDIT.md & .html       (Scorecard, validity, completeness, anomalies)             |
|  - RECONCILIATION_REPORT.md & .html   (Cross-source linkage, match rates, discrepancies)         |
+---------------------------------------------------------------------------------------------------+
```

---

## Data Lineage & Provenance
Every file processed by the platform generates an immutable audit record in `ingestion_batches`:
1. `batch_id`: Cryptographically secure unique batch execution token.
2. `file_hash`: SHA-256 hash guaranteeing that raw data files are untampered.
3. `record_counts`: Total received, passed validation, and quarantined records.
4. `timestamp`: UTC timestamps for ingestion start and completion.

