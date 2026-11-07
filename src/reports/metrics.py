"""
Data Quality Metrics & KPIs for Enterprise Governance.
"""
from typing import Dict, Any, List
import pandas as pd


class QualityMetricsCalculator:
    """Calculates enterprise data quality dimensions."""

    @staticmethod
    def calculate_dimensions(
        total_rows: int,
        passed_rows: int,
        quarantined_rows: int,
        null_counts: Dict[str, int],
        duplicate_count: int,
        critical_cols: List[str]
    ) -> Dict[str, Any]:
        """
        Calculates Completeness, Validity, Uniqueness, and Overall Quality Score.
        """
        # Validity: % of records that satisfied all business rules
        validity_pct = round((passed_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0

        # Uniqueness: % of records with unique identifiers
        uniqueness_pct = round(((total_rows - duplicate_count) / total_rows) * 100, 2) if total_rows > 0 else 100.0

        # Completeness: weighted completeness across critical columns
        critical_nulls = sum(null_counts.get(col, 0) for col in critical_cols)
        total_critical_fields = len(critical_cols) * total_rows if total_rows > 0 else 1
        completeness_pct = round(((total_critical_fields - critical_nulls) / total_critical_fields) * 100, 2)

        # Composite Quality Index (0 - 100)
        composite_score = round(
            (0.40 * validity_pct) + (0.35 * completeness_pct) + (0.25 * uniqueness_pct), 1
        )

        return {
            "validity_score": validity_pct,
            "completeness_score": completeness_pct,
            "uniqueness_score": uniqueness_pct,
            "composite_quality_score": composite_score,
            "quality_grade": "A+" if composite_score >= 95 else ("A" if composite_score >= 90 else ("B" if composite_score >= 80 else "C"))
        }

