# Enterprise Data Quality Audit Report
**Generated**: 2026-11-06 14:19:33 | **Dataset**: SOURCE_A_DEMOGRAPHICS

## 1. Executive Quality Scorecard
| Quality Dimension | Metric Score | Benchmark Target | Status |
| --- | --- | --- | --- |
| **Composite Quality Index** | **99.9% (Grade: A+)** | > 90.0% | ✅ PASSED |
| **Validity Rate** | 99.87% | > 98.0% | ✅ PASSED |
| **Completeness Rate** | 99.82% | > 95.0% | ✅ PASSED |
| **Uniqueness Rate** | 100.0% | 100.0% | ✅ PASSED |

## 2. Ingestion & Validation Summary
- **Total Input Records**: 2,240
- **Clean Records Accepted**: 2,237 (99.87%)
- **Quarantined Records**: 3
- **Income Handling Policy**: `ACCEPT_WITH_NULL`

### Rule Violation Breakdown
| Rule Code | Description | Violations Detected |
| --- | --- | --- |
| `MISSING_INCOME` | Automated business rule validation | 0 |
| `INVALID_BIRTH_YEAR` | Automated business rule validation | 3 |
| `INVALID_ID` | Automated business rule validation | 0 |
| `INVALID_DATE` | Automated business rule validation | 0 |
| `NEGATIVE_SPEND` | Automated business rule validation | 0 |
| `NEGATIVE_PURCHASES` | Automated business rule validation | 0 |
| `INVALID_EDUCATION` | Automated business rule validation | 0 |
| `INVALID_MARITAL_STATUS` | Automated business rule validation | 0 |

## 3. Detected Structural Anomalies
| Column | Issue Flagged | Count | Details |
| --- | --- | --- | --- |
| `Year_Birth` | Unrealistically early birth years (< 1920) | 3 | `[1900, 1893, 1899]` |
| `ID` | Customer ID equals 0 (potential sentinel value or missing surrogate key) | 1 | `[0]` |
| `Income` | Missing Income records requiring policy decision | 24 | `[None]` |
| `Z_CostContact, Z_Revenue` | Zero-variance columns (constant values across all rows, e.g. Z_CostContact, Z_Revenue) | 2 | `['Z_CostContact', 'Z_Revenue']` |
| `Marital_Status` | Non-standard or colloquial marital status values | 7 | `{'Alone': 3, 'Absurd': 2, 'YOLO': 2}` |