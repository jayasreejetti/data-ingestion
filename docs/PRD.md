# Product Requirements Document (PRD)
## Enterprise Data Ingestion & Multi-Source Reconciliation Platform
**Document Version:** 1.0.0  
**Target Architecture:** Production Data Platform  
**Author / Role:** Lead Product Manager & Senior Forward Deployed Engineer (FDE)  
**Status:** Approved & Implemented  

---

## 1. Executive Summary & Product Vision
Modern enterprises operate across siloed applications: customer demographic data resides in analytical files or data lakes, contact and address data in CRM systems (e.g., Salesforce), and transactional history in e-commerce or ERP databases. These disconnected systems lead to duplicate identities, incomplete profiles, data drift, and untrusted business analytics.

The **Enterprise Data Ingestion & Reconciliation Platform** is a unified, automated data engineering platform designed to ingest multi-format datasets, profile structural integrity, enforce business validations, isolate corrupted records in a quarantine store, and reconcile disparate records across multiple operational sources into a single **Golden Master Record** ("Single Source of Truth").

---

## 2. Problem Statement & Business Objectives
### 2.1 The Problem
- **Data Inconsistencies:** Tabular customer files contain formatting idiosyncrasies (e.g., tab-delimited files disguised as `.csv`), missing values, and demographic anomalies (e.g., birth years from 1893 to 1900).
- **Data Quality Loss:** Corrupted records are frequently dropped silently or cause pipeline crashes without diagnostic audit trails.
- **Entity Fragmentation:** Customer information is divided between demographics, CRM contact identities, and sales transaction logs without cross-system reconciliation.

### 2.2 Core Product Objectives
1. **Multi-Format Ingestion:** Robustly ingest CSV, TSV, Excel (`.xlsx`), and JSON with automatic delimiter, encoding, and schema detection.
2. **Automated Profiling & Anomaly Flagging:** Compute statistical profiles, identify null distributions, detect zero-variance columns, and flag domain outliers.
3. **Configurable Business Validation & Quarantine:** Apply strict business rules with configurable policies for handling missing values (e.g., Income policy: `ACCEPT_WITH_NULL`, `QUARANTINE`, or `REJECT`) and persist invalid records into an isolated quarantine zone.
4. **Canonical Data Transformation:** Cleanse dates into ISO-8601 (`YYYY-MM-DD`), normalize categorical taxonomies (Education, Marital Status), and engineer derived analytical features.
5. **Multi-Source Entity Resolution & Reconciliation:** Join Source A (Demographics), Source B (CRM), and Source C (Sales Ledger) to synthesize a single golden customer profile, resolve attribute conflicts, and audit cross-system financial variances.
6. **Executive Quality Reporting:** Generate executive-ready Data Quality Audit Reports and Reconciliation Reports in Markdown and standalone HTML.

---

## 3. Input Data Architecture & Source Specifications

### Source A: Customer Personality & Demographic Dataset
- **Format:** Tab-delimited text (`.csv` / TSV) and Excel working copy (`.xlsx`)
- **Volume:** 2,240 records, 29 attributes
- **Characteristics:** Contains customer birth year, education, marital status, income, household composition, enrollment dates, spending across product categories, and marketing campaign responses.
- **Known Quality Nuances:** 
  - Delimiter is Tab (`\t`), not comma.
  - 24 missing values in `Income`.
  - 3 records with birth year < 1920 (1893, 1899, 1900).
  - Non-standard marital categories (`Alone`, `Absurd`, `YOLO`).
  - Zero-variance columns (`Z_CostContact = 3`, `Z_Revenue = 11`).

### Source B: CRM Customer System
- **Format:** Excel spreadsheet (`source_b_crm.xlsx`)
- **Volume:** 2,050 records
- **Attributes:** `crm_customer_id`, `first_name`, `last_name`, `email`, `phone`, `city`, `country`, `account_status`, `crm_created_at`.
- **Purpose:** Primary authoritative source for customer personal identity and verified contact channels.

### Source C: Sales & Transaction Ledger
- **Format:** JSON array (`source_c_transactions.json`)
- **Volume:** 4,513 transaction records
- **Attributes:** `transaction_id`, `customer_id`, `transaction_date`, `channel` (Web, Store, Catalog), `amount`, `payment_method`, `status`.
- **Purpose:** Transactional ledger used to calculate aggregated cross-channel customer spend and audit financial consistency against Source A's reported historical spend.

---

## 4. Ingestion, Profiling & Validation Specifications

### 4.1 Ingestion Flow
```
[Raw File] ──► [FileDetector] ──► [DataReader] ──► [DataProfiler]
                      │                  │                  │
               SHA-256 Checksum    Auto-Delimiter      Nulls & Outliers
               Encoding Sniffing   DataFrame Load      Zero-Variance
```

### 4.2 Business Validation Rules
| Rule Code | Target Column | Validation Condition | Failure Action |
| --- | --- | --- | --- |
| `INVALID_ID` | `ID` | Must be non-negative integer (`ID >= 0`) | Quarantine with reason |
| `INVALID_BIRTH_YEAR` | `Year_Birth` | `1920 <= Year_Birth <= (Current_Year - 18)` | Quarantine with reason |
| `MISSING_INCOME` | `Income` | Value must not be null | Configurable: `ACCEPT_WITH_NULL` / `QUARANTINE` / `REJECT` |
| `NEGATIVE_INCOME` | `Income` | `Income >= 0` | Quarantine with reason |
| `INVALID_DATE` | `Dt_Customer` | Parseable as date (`%d-%m-%Y`, `%Y-%m-%d`) | Quarantine with reason |
| `NEGATIVE_SPEND` | `Mnt*` | Spend amounts must be `>= 0` | Quarantine with reason |
| `NEGATIVE_PURCHASES`| `Num*` | Purchase counts must be `>= 0` | Quarantine with reason |

### 4.3 Engineering Decision: Income Validation Policy
- **Option A (REJECT):** Immediately reject record from downstream use.
- **Option B (ACCEPT_WITH_NULL):** Retain customer profile in production warehouse while preserving `Income = NULL`. This is the recommended baseline policy because Income is an optional demographic attribute; discarding valid customer accounts leads to severe data attrition.
- **Option C (QUARANTINE):** Route record to quarantine storage for manual review and human remediation.

---

## 5. Canonical Data Model & Transformation
Cleaned records are normalized and transformed into a standardized master schema:
- **Date Normalization:** All date strings converted to standard ISO-8601 (`YYYY-MM-DD`).
- **Education Taxonomy:**
  - `Graduation` ➔ `Bachelor`
  - `PhD` ➔ `Doctorate`
  - `Master` / `2n Cycle` ➔ `Master`
  - `Basic` ➔ `Undergraduate`
- **Marital Status Taxonomy:**
  - `Married` ➔ `Married`
  - `Together` ➔ `Cohabiting`
  - `Single` / `Alone` ➔ `Single`
  - `Divorced` ➔ `Divorced`
  - `Widow` ➔ `Widowed`
  - `Absurd` / `YOLO` ➔ `Unknown`
- **Derived Analytical Features:**
  - `Age` = `2026 - Year_Birth`
  - `Total_Dependents` = `Kidhome + Teenhome`
  - `Has_Children` = Boolean (`Total_Dependents > 0`)
  - `Total_Spend` = Wine + Fruits + Meat + Fish + Sweets + Gold
  - `Total_Purchases` = Web + Catalog + Store Purchases
  - `Campaign_Response_Rate` = Accepted Campaigns / 5

---

## 6. Multi-Source Reconciliation & Entity Resolution
### 6.1 Match Hierarchy
1. **Deterministic Primary Key Matching:** Join on validated customer identifier (`customer_id` / `ID`).
2. **Contact Priority:** Source B (CRM) takes precedence for customer name, email, phone, city, and account status.
3. **Demographic Truth:** Source A is authoritative for birth year, education, income, family size, and historical customer tenure.
4. **Transaction Aggregation:** Source C transaction records are aggregated per customer (`reconciled_transaction_count`, `reconciled_transaction_total`).
5. **Financial Cross-System Audit:** Discrepancies between Source A historical spend and Source C transaction totals are calculated and logged in `reconciliation_logs` with resolution rationale.

---

## 7. Data Quality Dimensions & KPIs
The platform tracks four fundamental data quality dimensions:
1. **Validity:** Percentage of ingested records satisfying 100% of defined validation rules. (Target: > 98.0%)
2. **Completeness:** Percentage of non-null values across critical business columns. (Target: > 95.0%)
3. **Uniqueness:** Percentage of records with distinct primary identifiers. (Target: 100.0%)
4. **Composite Quality Score:** Weighted composite index:
   $$\text{Quality Score} = (0.40 \times \text{Validity}) + (0.35 \times \text{Completeness}) + (0.25 \times \text{Uniqueness})$$

---

## 8. Warehouse Schema & Persistence Layer
The storage layer utilizes SQLAlchemy ORM with default zero-dependency SQLite storage (`enterprise_warehouse.db`), fully swappable for enterprise PostgreSQL via `DATABASE_URL`:
- `ingestion_batches`: Batch ID, file name, SHA-256 hash, byte size, record counts, timestamp.
- `customer_demographics`: Cleaned, validated Source A records.
- `customer_crm`: Source B contact and account status records.
- `customer_transactions`: Source C e-commerce / POS transaction ledger.
- `canonical_customers`: Unified Golden Master Customer records.
- `quarantined_records`: Rejected records, error codes, and original JSON payloads.
- `reconciliation_logs`: Cross-source variance and conflict resolution audit entries.

---

## 9. Delivery Milestones & Acceptance Criteria
- [x] **Milestone 1: Ingestion & Profiling:** Automated format detection, SHA-256 hashing, profiling, anomaly detection.
- [x] **Milestone 2: Validation & Quarantine:** Multi-policy engine (`ACCEPT_WITH_NULL`, `QUARANTINE`, `REJECT`), quarantine persistence in JSON & CSV.
- [x] **Milestone 3: Data Transformation:** Standardized dates, normalized education/marital status, derived features.
- [x] **Milestone 4: Storage & Warehousing:** Relational schema with transactional ACID compliance and idempotency.
- [x] **Milestone 5: Multi-Source Reconciliation:** Entity matching across Demographics, CRM, and Transactions, generating Golden Master Records.
- [x] **Milestone 6: Reporting & Test Suite:** Automated HTML & Markdown reports, unit and integration test suite passing with 100% success.

