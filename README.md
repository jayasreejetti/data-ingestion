# Enterprise Data Ingestion & Multi-Source Reconciliation Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade Enterprise Data Ingestion, Profiling, Validation, Quarantine, and Multi-Source Reconciliation Platform. Built to handle multi-format inputs (CSV, TSV, Excel, JSON), enforce configurable business validation rules, isolate corrupted data, standardize entities, and synthesize a reconciled **Single Source of Truth (Golden Record)** across disparate operational systems.

---

## Architecture Overview

```
                      +---------------------------------------+
                      | Raw Inputs (CSV/TSV, Excel, JSON)     |
                      +---------------------------------------+
                                          │
                                          ▼
                      +---------------------------------------+
                      | FileDetector (SHA-256, Delimiter, Enc)|
                      +---------------------------------------+
                                          │
                                          ▼
                      +---------------------------------------+
                      | DataProfiler (IQR, Nulls, Anomalies)  |
                      +---------------------------------------+
                                          │
                                          ▼
                      +---------------------------------------+
                      | ValidationEngine (Configurable Rules) |
                      +---------------------------------------+
                                    │           │
                    Valid Records   ▼           ▼  Violations
            +---------------------------+   +---------------------------+
            | DataCleaner & Standardizer|   | QuarantineManager         |
            | - ISO-8601 Dates          |   | - Error Codes & Payloads  |
            | - Standard Taxonomies     |   | - JSON & CSV Isolation    |
            | - Derived Analytics       |   +---------------------------+
            +---------------------------+
                          │
                          ▼
            +---------------------------+
            | Staging & Warehouse DB    |
            | (Demographics, CRM, Sales)|
            +---------------------------+
                          │
                          ▼
            +---------------------------+
            | ReconciliationEngine      |
            | - Multi-Source Matcher    |
            | - Conflict Resolver       |
            | - Golden Customer Record  |
            +---------------------------+
                          │
                          ▼
            +---------------------------+
            | Automated Audit Reports   |
            | (Markdown & Standalone HTML)
            +---------------------------+
```

---

## Repository Structure

```
enterprise-data-platform/
│
├── config/
│   ├── __init__.py
│   └── settings.py               # Paths, DB URL, validation policies, taxonomies
│
├── data/
│   ├── raw/                      # Untouched source datasets
│   │   ├── customer_personality.csv         # Source A (Raw TSV/CSV)
│   │   ├── customer_personality_source.xlsx # Source A (Excel working copy)
│   │   ├── source_b_crm.xlsx                # Source B (CRM contact profiles)
│   │   └── source_c_transactions.json       # Source C (Orders / POS ledger)
│   ├── staging/                  # Intermediate cleansed records
│   ├── quarantine/               # Isolated records failing business validation
│   ├── processed/                # Production SQLite warehouse (`enterprise_warehouse.db`)
│   └── reports/                  # Generated HTML and Markdown audit reports
│
├── src/
│   ├── ingest/
│   │   ├── detector.py           # Delimiter sniff, SHA-256 hashing, encoding detect
│   │   ├── reader.py             # Multi-format reader (CSV, TSV, XLSX, JSON)
│   │   └── profiler.py           # Statistical profiling, nulls & anomaly checks
│   ├── validate/
│   │   ├── rules.py              # Business validation engine & policies
│   │   ├── schema.py             # Pydantic schemas for Source A, B, C & Golden Record
│   │   └── quarantine.py         # Quarantine persistence manager
│   ├── transform/
│   │   ├── cleaner.py            # Date conversion, string trimming, categorization
│   │   └── standardizer.py       # Staging generation
│   ├── storage/
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   └── database.py           # Transactional session manager & bulk loaders
│   ├── reconcile/
│   │   ├── matcher.py            # Cross-source entity resolution
│   │   ├── resolver.py           # Conflict resolution & golden record synthesis
│   │   └── engine.py             # Multi-source reconciliation orchestrator
│   ├── reports/
│   │   ├── metrics.py            # Quality dimensions (validity, completeness, uniqueness)
│   │   └── generator.py          # Markdown & responsive HTML report generator
│   └── pipeline.py               # End-to-end pipeline orchestrator
│
├── tests/
│   └── test_platform.py          # Unit & integration test suite (100% passing)
│
├── docs/
│   ├── PRD.md                    # Product Requirements Document
│   ├── ARCHITECTURE.md           # Technical Architecture & Lineage
│   └── DATA_DICTIONARY.md        # Detailed Field-by-Field Data Dictionary
│
├── main.py                       # Command-Line Interface (CLI)
├── run_demo.py                   # Complete End-to-End Demo Runner
├── requirements.txt
└── README.md
```

---

## Quickstart & Execution

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Complete End-to-End Demo
Executes ingestion of Source A, B, and C, quarantine routing, multi-source reconciliation, and report generation in seconds:
```bash
python run_demo.py
```

### 3. Run the Automated Test Suite
```bash
python -m unittest tests/test_platform.py
```

---

## CLI Usage

The platform provides a modular CLI via `main.py`:

### Profile Any Dataset
```bash
python main.py profile --file data/raw/customer_personality.csv
```

### Ingest Source A with Custom Policy
```bash
# Accept missing income with NULL (Recommended production baseline)
python main.py ingest --file data/raw/customer_personality.csv --income-policy ACCEPT_WITH_NULL

# Or quarantine missing income records for manual review
python main.py ingest --file data/raw/customer_personality.csv --income-policy QUARANTINE
```

### Run Multi-Source Reconciliation
```bash
python main.py reconcile
```

### View Warehouse Statistics
```bash
python main.py stats
```

### Run All Stages Sequentially
```bash
python main.py run-all
```

---

## Key Validation Policies & Results

### 1. Missing Income Handling
- **Dataset Reality:** 24 customer records in Source A contain missing `Income` values.
- **Implemented Decision:** Handled via configurable policy (`ACCEPT_WITH_NULL` by default). Valid customer accounts remain accessible for relationship management without losing valid contact and behavioral history.

### 2. Demographic Anomaly Isolation
- **Quarantined Records:** Exactly 3 records had `Year_Birth < 1920` (specifically years 1893, 1899, and 1900, indicating ages > 120 years).
- **Action:** Routed to `data/quarantine/` with failure code `INVALID_BIRTH_YEAR` and full uncorrupted JSON payloads preserved for governance.

### 3. Multi-Source Reconciliation Highlights
- **Total Golden Records Synthesized:** 2,290 customers.
- **CRM Enrichment Rate:** 89.27% of Source A customers matched with verified names, emails, and phone numbers in Source B.
- **Transaction Coverage:** 65.5% of master customers linked to actual purchase order ledgers in Source C.
- **Data Quality Score:** **99.9% (Grade: A+)**.

