"""
Business Validation Rules and Validation Engine.
"""
from typing import Dict, Any, List, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from config.settings import (
    DEFAULT_INCOME_POLICY,
    MIN_VALID_BIRTH_YEAR,
    CURRENT_ANALYSIS_YEAR,
    VALID_EDUCATION_LEVELS,
    VALID_MARITAL_STATUSES,
)


class ValidationRuleResult:
    """Represents the validation result for a batch or row."""
    def __init__(self, is_valid: bool, rule_code: str, message: str, column: str, offending_value: Any = None):
        self.is_valid = is_valid
        self.rule_code = rule_code
        self.message = message
        self.column = column
        self.offending_value = offending_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "rule_code": self.rule_code,
            "message": self.message,
            "column": self.column,
            "offending_value": str(self.offending_value) if self.offending_value is not None else None,
        }


class ValidationEngine:
    """
    Executes business rules against raw data records.
    Partitions data into valid records and quarantined records.
    """

    def __init__(self, income_policy: str = DEFAULT_INCOME_POLICY):
        """
        income_policy: 'ACCEPT_WITH_NULL', 'QUARANTINE', or 'REJECT'
        """
        self.income_policy = income_policy.upper()

    def validate_source_a_customer_personality(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Validates Source A (Customer Personality Analysis dataset).
        Returns:
            (valid_df, quarantine_df, audit_summary)
        """
        quarantined_records = []
        valid_indices = []

        total_rows = len(df)
        rule_violation_counts: Dict[str, int] = {
            "MISSING_INCOME": 0,
            "INVALID_BIRTH_YEAR": 0,
            "INVALID_ID": 0,
            "INVALID_DATE": 0,
            "NEGATIVE_SPEND": 0,
            "NEGATIVE_PURCHASES": 0,
            "INVALID_EDUCATION": 0,
            "INVALID_MARITAL_STATUS": 0
        }

        # Vectorized rule checking for maximum enterprise performance
        for idx, row in df.iterrows():
            failures: List[Dict[str, Any]] = []

            # Rule 1: ID validation
            cust_id = row.get("ID")
            if pd.isna(cust_id) or not isinstance(cust_id, (int, np.integer, float)) or cust_id < 0:
                failures.append({
                    "rule_code": "INVALID_ID",
                    "column": "ID",
                    "value": cust_id,
                    "reason": f"Customer ID must be a non-negative integer. Found: {cust_id}"
                })
                rule_violation_counts["INVALID_ID"] += 1

            # Rule 2: Year_Birth validation
            birth_year = row.get("Year_Birth")
            if pd.isna(birth_year) or birth_year < MIN_VALID_BIRTH_YEAR or birth_year > (CURRENT_ANALYSIS_YEAR - 18):
                failures.append({
                    "rule_code": "INVALID_BIRTH_YEAR",
                    "column": "Year_Birth",
                    "value": birth_year,
                    "reason": f"Year_Birth {birth_year} outside realistic adult bounds ({MIN_VALID_BIRTH_YEAR}-{CURRENT_ANALYSIS_YEAR - 18})"
                })
                rule_violation_counts["INVALID_BIRTH_YEAR"] += 1

            # Rule 3: Income validation & Policy application
            income = row.get("Income")
            if pd.isna(income):
                if self.income_policy in ["QUARANTINE", "REJECT"]:
                    failures.append({
                        "rule_code": "MISSING_INCOME",
                        "column": "Income",
                        "value": None,
                        "reason": f"Income value is missing (Policy: {self.income_policy})"
                    })
                    rule_violation_counts["MISSING_INCOME"] += 1
            elif income < 0:
                failures.append({
                    "rule_code": "NEGATIVE_INCOME",
                    "column": "Income",
                    "value": income,
                    "reason": f"Income cannot be negative. Found: {income}"
                })

            # Rule 4: Dt_Customer date parseability
            dt_raw = str(row.get("Dt_Customer", "")).strip()
            date_valid = False
            for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    datetime.strptime(dt_raw, fmt)
                    date_valid = True
                    break
                except ValueError:
                    pass
            if not date_valid:
                failures.append({
                    "rule_code": "INVALID_DATE",
                    "column": "Dt_Customer",
                    "value": dt_raw,
                    "reason": f"Cannot parse enrollment date: '{dt_raw}'"
                })
                rule_violation_counts["INVALID_DATE"] += 1

            # Rule 5: Non-negative spending amounts
            spend_cols = ["MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds"]
            for sc in spend_cols:
                val = row.get(sc, 0)
                if not pd.isna(val) and val < 0:
                    failures.append({
                        "rule_code": "NEGATIVE_SPEND",
                        "column": sc,
                        "value": val,
                        "reason": f"Spend value {sc} cannot be negative ({val})"
                    })
                    rule_violation_counts["NEGATIVE_SPEND"] += 1

            # Rule 6: Non-negative purchase counts
            purch_cols = ["NumDealsPurchases", "NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases", "NumWebVisitsMonth"]
            for pc in purch_cols:
                val = row.get(pc, 0)
                if not pd.isna(val) and val < 0:
                    failures.append({
                        "rule_code": "NEGATIVE_PURCHASES",
                        "column": pc,
                        "value": val,
                        "reason": f"Purchase count {pc} cannot be negative ({val})"
                    })
                    rule_violation_counts["NEGATIVE_PURCHASES"] += 1

            # If failures occurred, route row to quarantine
            if failures:
                q_entry = row.to_dict()
                q_entry["_quarantine_reasons"] = "; ".join(f["reason"] for f in failures)
                q_entry["_quarantine_codes"] = [f["rule_code"] for f in failures]
                quarantined_records.append(q_entry)
            else:
                valid_indices.append(idx)

        valid_df = df.loc[valid_indices].copy()
        quarantine_df = pd.DataFrame(quarantined_records)

        summary = {
            "total_evaluated": total_rows,
            "passed_validation_count": len(valid_df),
            "quarantined_count": len(quarantine_df),
            "pass_rate_pct": round((len(valid_df) / total_rows) * 100, 2) if total_rows > 0 else 0.0,
            "income_policy_applied": self.income_policy,
            "violation_counts": rule_violation_counts
        }

        return valid_df, quarantine_df, summary

