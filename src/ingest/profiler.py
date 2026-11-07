"""
Comprehensive Data Profiler for Enterprise Ingestion.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np


class DataProfiler:
    """Computes statistical profiles, data anomalies, and quality indicators."""

    @classmethod
    def profile_dataset(cls, df: pd.DataFrame, source_name: str = "Source_A") -> Dict[str, Any]:
        """Generate a complete statistical and anomaly profile of the dataset."""
        row_count = len(df)
        col_count = len(df.columns)
        memory_usage_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)

        # 1. Null Value Analysis
        null_counts = df.isnull().sum()
        columns_with_nulls = {
            col: {
                "missing_count": int(count),
                "missing_pct": round(float(count / row_count) * 100, 2)
            }
            for col, count in null_counts.items() if count > 0
        }

        # 2. Duplicate Analysis
        duplicate_rows = int(df.duplicated().sum())
        id_col = next((c for c in ["ID", "id", "customer_id", "crm_customer_id"] if c in df.columns), None)
        id_duplicates = int(df[id_col].duplicated().sum()) if id_col else 0

        # 3. Column Data Types and Cardinality
        column_profiles = {}
        zero_variance_cols = []

        for col in df.columns:
            series = df[col]
            n_unique = int(series.nunique(dropna=True))
            dtype_str = str(series.dtype)

            col_meta: Dict[str, Any] = {
                "dtype": dtype_str,
                "null_count": int(null_counts[col]),
                "unique_values": n_unique,
            }

            if n_unique <= 1:
                zero_variance_cols.append(col)

            if pd.api.types.is_numeric_dtype(series):
                valid_num = series.dropna()
                if len(valid_num) > 0:
                    q1 = float(valid_num.quantile(0.25))
                    q3 = float(valid_num.quantile(0.75))
                    iqr = q3 - q1
                    lower_bound = q1 - (1.5 * iqr)
                    upper_bound = q3 + (1.5 * iqr)
                    outliers_count = int(((valid_num < lower_bound) | (valid_num > upper_bound)).sum())

                    col_meta.update({
                        "min": float(valid_num.min()),
                        "max": float(valid_num.max()),
                        "mean": round(float(valid_num.mean()), 2),
                        "median": round(float(valid_num.median()), 2),
                        "std": round(float(valid_num.std()), 2) if len(valid_num) > 1 else 0.0,
                        "iqr_outliers": outliers_count
                    })
            else:
                top_values = series.value_counts(dropna=False).head(5).to_dict()
                col_meta["top_categories"] = {str(k): int(v) for k, v in top_values.items()}

            column_profiles[col] = col_meta

        # 4. Domain-Specific Anomalies (e.g. for customer personality data)
        anomalies = []
        if "Year_Birth" in df.columns:
            unusual_births = df[df["Year_Birth"] < 1920]["Year_Birth"].tolist()
            if unusual_births:
                anomalies.append({
                    "column": "Year_Birth",
                    "issue": "Unrealistically early birth years (< 1920)",
                    "count": len(unusual_births),
                    "examples": unusual_births[:5]
                })

        if id_col and (df[id_col] == 0).any():
            zero_ids = int((df[id_col] == 0).sum())
            anomalies.append({
                "column": id_col,
                "issue": "Customer ID equals 0 (potential sentinel value or missing surrogate key)",
                "count": zero_ids,
                "examples": [0]
            })

        if "Income" in df.columns:
            missing_income = int(df["Income"].isnull().sum())
            if missing_income > 0:
                anomalies.append({
                    "column": "Income",
                    "issue": "Missing Income records requiring policy decision",
                    "count": missing_income,
                    "examples": [None]
                })

        if zero_variance_cols:
            anomalies.append({
                "column": ", ".join(zero_variance_cols),
                "issue": "Zero-variance columns (constant values across all rows, e.g. Z_CostContact, Z_Revenue)",
                "count": len(zero_variance_cols),
                "examples": zero_variance_cols
            })

        if "Marital_Status" in df.columns:
            non_standard_marital = df[df["Marital_Status"].isin(["Alone", "Absurd", "YOLO"])]["Marital_Status"].value_counts().to_dict()
            if non_standard_marital:
                anomalies.append({
                    "column": "Marital_Status",
                    "issue": "Non-standard or colloquial marital status values",
                    "count": sum(non_standard_marital.values()),
                    "examples": non_standard_marital
                })

        return {
            "source_name": source_name,
            "row_count": row_count,
            "column_count": col_count,
            "memory_usage_mb": memory_usage_mb,
            "duplicate_rows": duplicate_rows,
            "id_duplicates": id_duplicates,
            "columns_with_nulls": columns_with_nulls,
            "zero_variance_columns": zero_variance_cols,
            "anomalies": anomalies,
            "column_profiles": column_profiles
        }

    @classmethod
    def generate_markdown_summary(cls, profile: Dict[str, Any]) -> str:
        """Render markdown summary of profiling results."""
        md = []
        md.append(f"# Data Profiling Report: {profile['source_name']}\n")
        md.append(f"- **Total Records**: {profile['row_count']:,}")
        md.append(f"- **Total Columns**: {profile['column_count']}")
        md.append(f"- **Memory Footprint**: {profile['memory_usage_mb']} MB")
        md.append(f"- **Full Row Duplicates**: {profile['duplicate_rows']}")
        md.append(f"- **ID Duplicates**: {profile['id_duplicates']}\n")

        md.append("## Null Value Overview")
        if profile["columns_with_nulls"]:
            md.append("| Column | Missing Records | Missing % |")
            md.append("| --- | --- | --- |")
            for col, stats in profile["columns_with_nulls"].items():
                md.append(f"| `{col}` | {stats['missing_count']} | {stats['missing_pct']}% |")
        else:
            md.append("No null values detected.\n")

        md.append("\n## Detected Anomalies & Quality Flags")
        if profile["anomalies"]:
            md.append("| Target Column | Issue Description | Count | Examples / Notes |")
            md.append("| --- | --- | --- | --- |")
            for a in profile["anomalies"]:
                md.append(f"| `{a['column']}` | {a['issue']} | {a['count']} | {a['examples']} |")
        else:
            md.append("No critical anomalies flagged.\n")

        return "\n".join(md)

