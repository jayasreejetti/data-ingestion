# Data Dictionary
## Enterprise Data Ingestion & Reconciliation Platform

This document describes the schema, constraints, data types, and business descriptions for all input and canonical tables.

---

## 1. Source A: Customer Personality & Demographics
**File Source:** `data/raw/customer_personality.csv` (and `customer_personality_source.xlsx`)

| Field Name | Type | Nullable | Description & Business Rules |
| --- | --- | --- | --- |
| `ID` | Integer | No | Unique customer identifier. Must be non-negative. |
| `Year_Birth` | Integer | No | Customer birth year. Must be between 1920 and (Current Year - 18). |
| `Education` | String | No | Customer highest education level. Categories: Graduation, PhD, Master, 2n Cycle, Basic. |
| `Marital_Status` | String | No | Marital status. Standard categories: Married, Together, Single, Divorced, Widow. Colloquial: Alone, Absurd, YOLO. |
| `Income` | Float | Yes | Annual household income. Contains 24 missing values handled by business policy. |
| `Kidhome` | Integer | No | Number of young children in household. Must be `>= 0`. |
| `Teenhome` | Integer | No | Number of teenagers in household. Must be `>= 0`. |
| `Dt_Customer` | String | No | Date of customer enrollment with company (e.g., `04-09-2012`). |
| `Recency` | Integer | No | Days since the last customer purchase. Must be `>= 0`. |
| `MntWines` | Float | No | Amount spent on wine products in the last 2 years. |
| `MntFruits` | Float | No | Amount spent on fruit products in the last 2 years. |
| `MntMeatProducts`| Float | No | Amount spent on meat products in the last 2 years. |
| `MntFishProducts`| Float | No | Amount spent on fish products in the last 2 years. |
| `MntSweetProducts`| Float| No | Amount spent on sweet/confectionery products in the last 2 years. |
| `MntGoldProds` | Float | No | Amount spent on gold/luxury products in the last 2 years. |
| `NumDealsPurchases` | Integer | No | Purchases made with a promotion/discount. |
| `NumWebPurchases` | Integer | No | Purchases made through the company website. |
| `NumCatalogPurchases` | Integer | No | Purchases made using the print catalog. |
| `NumStorePurchases` | Integer | No | Purchases made directly in retail stores. |
| `NumWebVisitsMonth` | Integer | No | Number of visits to company's website in the last month. |
| `AcceptedCmp1-5` | Integer | No | Binary indicators (0 or 1) indicating whether campaign 1-5 was accepted. |
| `Complain` | Integer | No | 1 if customer complained in the last 2 years, 0 otherwise. |
| `Response` | Integer | No | 1 if customer accepted the offer in the last marketing campaign. |
| `Z_CostContact` | Integer | No | Constant value 3 (zero variance). |
| `Z_Revenue` | Integer | No | Constant value 11 (zero variance). |

---

## 2. Source B: CRM Contact System
**File Source:** `data/raw/source_b_crm.xlsx`

| Field Name | Type | Nullable | Description & Business Rules |
| --- | --- | --- | --- |
| `crm_customer_id` | Integer | No | Primary key matching customer identifier. |
| `first_name` | String | No | Cleaned customer first name (title-cased). |
| `last_name` | String | No | Cleaned customer last name (title-cased). |
| `full_name` | String | No | Concatenated first and last name. |
| `email` | String | Yes | Verified email address. Lowercase standardized. |
| `phone` | String | Yes | Standardized contact telephone number. |
| `city` | String | Yes | Primary residential metropolitan area. |
| `country` | String | No | ISO country code or name (Default: `USA`). |
| `account_status` | String | No | Account status: `ACTIVE`, `INACTIVE`, `PENDING_VERIFICATION`. |
| `crm_created_at` | String | Yes | ISO registration date. |

---

## 3. Source C: Transactions & Sales Ledger
**File Source:** `data/raw/source_c_transactions.json`

| Field Name | Type | Nullable | Description & Business Rules |
| --- | --- | --- | --- |
| `transaction_id` | String | No | Unique transaction token (e.g., `TX-100001`). |
| `customer_id` | Integer | No | Foreign key linking to customer identifier. |
| `transaction_date`| String | No | ISO date of transaction (`YYYY-MM-DD`). |
| `channel` | String | No | Purchase channel: `WEB`, `STORE`, `CATALOG`. |
| `amount` | Float | No | Transaction purchase total in USD. |
| `payment_method` | String | No | Payment type: `CREDIT_CARD`, `DEBIT_CARD`, `PAYPAL`, `GIFT_CARD`. |
| `status` | String | No | Transaction status: `COMPLETED`, `REFUNDED`. |

---

## 4. Master Golden Customer Table
**Database Table:** `canonical_customers`

| Field Name | Type | Source Origin | Description |
| --- | --- | --- | --- |
| `customer_id` | Integer (PK) | Source A/B/C | Master enterprise customer ID. |
| `first_name` | String | Source B | Reconciled first name. |
| `last_name` | String | Source B | Reconciled last name. |
| `full_name` | String | Source B | Reconciled full name. |
| `email` | String | Source B | Verified customer contact email. |
| `phone` | String | Source B | Verified customer phone number. |
| `city` | String | Source B | Customer residential city. |
| `country` | String | Source B | Customer country. |
| `account_status` | String | Source B | CRM account lifecycle status. |
| `birth_year` | Integer | Source A | Master birth year. |
| `age` | Integer | Source A | Calculated age (`2026 - birth_year`). |
| `education` | String | Source A | Standardized education (`Bachelor`, `Master`, `Doctorate`). |
| `marital_status`| String | Source A | Standardized marital status (`Married`, `Cohabiting`, `Single`). |
| `income` | Float | Source A | Annual household income (preserves NULL under policy). |
| `total_dependents`| Integer | Source A | Total children (`Kidhome + Teenhome`). |
| `has_children` | Boolean | Source A | True if `total_dependents > 0`. |
| `customer_since` | String | Source A/B | ISO customer enrollment date. |
| `recency_days` | Integer | Source A | Days since last engagement. |
| `total_spend` | Float | Source A | Aggregated category spending from Demographics. |
| `total_purchases` | Integer | Source A | Aggregated purchase count from Demographics. |
| `wine_spend` | Float | Source A | Wine category spending. |
| `meat_spend` | Float | Source A | Meat category spending. |
| `gold_spend` | Float | Source A | Gold category spending. |
| `sources_matched`| String | Pipeline | Lineage flags indicating matched sources (`SOURCE_A+SOURCE_B+SOURCE_C`). |
| `has_crm_match` | Boolean | Pipeline | True if customer exists in Source B CRM. |
| `has_transaction_history`| Boolean| Pipeline | True if customer has orders in Source C ledger. |
| `reconciled_transaction_count`| Integer| Source C | Total completed orders in Source C. |
| `reconciled_transaction_total`| Float| Source C | Sum of all completed order amounts in Source C. |
| `reconciliation_confidence`| Float | Pipeline | Match quality score (0.0 to 1.0). |

