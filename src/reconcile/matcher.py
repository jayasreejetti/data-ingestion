"""
Entity Matcher: links records across heterogeneous data sources.
"""
from typing import Dict, Any, List, Set, Tuple
import pandas as pd


class EntityMatcher:
    """Matches customer entities across Source A, Source B, and Source C."""

    @staticmethod
    def match_entities(
        df_demographics: pd.DataFrame,
        df_crm: pd.DataFrame,
        df_transactions: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Performs multi-source deterministic join and entity resolution.
        """
        # Demographic IDs (Source A)
        id_a_col = "customer_id" if "customer_id" in df_demographics.columns else "ID"
        ids_a: Set[int] = set(df_demographics[id_a_col].dropna().astype(int))

        # CRM IDs (Source B)
        id_b_col = "customer_id" if "customer_id" in df_crm.columns else "crm_customer_id"
        ids_b: Set[int] = set(df_crm[id_b_col].dropna().astype(int)) if not df_crm.empty else set()

        # Transaction IDs (Source C)
        id_c_col = "customer_id"
        ids_c: Set[int] = set(df_transactions[id_c_col].dropna().astype(int)) if not df_transactions.empty else set()

        # Set algebra for cross-source entity linkage
        matched_a_and_b = ids_a.intersection(ids_b)
        only_in_a = ids_a - ids_b
        only_in_b = ids_b - ids_a
        all_unique_customers = ids_a.union(ids_b)

        # Transaction coverage
        customers_with_transactions = (ids_a.union(ids_b)).intersection(ids_c)

        return {
            "total_unique_customers": len(all_unique_customers),
            "source_a_count": len(ids_a),
            "source_b_count": len(ids_b),
            "source_c_customer_count": len(ids_c),
            "matched_a_and_b_count": len(matched_a_and_b),
            "only_in_source_a_count": len(only_in_a),
            "only_in_source_b_count": len(only_in_b),
            "customers_with_transactions_count": len(customers_with_transactions),
            "match_rate_pct": round((len(matched_a_and_b) / len(ids_a)) * 100, 2) if ids_a else 0.0,
            "matched_ids": matched_a_and_b,
            "only_in_a_ids": only_in_a,
            "only_in_b_ids": only_in_b
        }

