"""
Conflict Resolver: applies business rules to reconcile discrepant data attributes.
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd


class ConflictResolver:
    """Resolves attribute conflicts between multiple sources using prioritized strategies."""

    @staticmethod
    def resolve_customer_entity(
        cust_id: int,
        demo_record: Optional[Dict[str, Any]],
        crm_record: Optional[Dict[str, Any]],
        tx_records: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Synthesizes a Golden Record for a customer and logs any conflict decisions.
        """
        conflict_logs = []

        # Determine lineage sources
        sources = []
        if demo_record:
            sources.append("SOURCE_A_DEMOGRAPHICS")
        if crm_record:
            sources.append("SOURCE_B_CRM")
        if tx_records:
            sources.append("SOURCE_C_TRANSACTIONS")

        golden = {
            "customer_id": cust_id,
            "sources_matched": "+".join(sources),
            "has_crm_match": bool(crm_record),
            "has_transaction_history": bool(tx_records),
            "reconciliation_confidence": 1.0
        }

        # 1. Identity & Contact Resolution (CRM wins by priority)
        if crm_record:
            golden["first_name"] = crm_record.get("first_name")
            golden["last_name"] = crm_record.get("last_name")
            golden["full_name"] = crm_record.get("full_name")
            golden["email"] = crm_record.get("email")
            golden["phone"] = crm_record.get("phone")
            golden["city"] = crm_record.get("city")
            golden["country"] = crm_record.get("country", "USA")
            golden["account_status"] = crm_record.get("account_status", "ACTIVE")
        else:
            golden["first_name"] = None
            golden["last_name"] = None
            golden["full_name"] = f"Customer #{cust_id}"
            golden["email"] = None
            golden["phone"] = None
            golden["city"] = None
            golden["country"] = None
            golden["account_status"] = "UNREGISTERED_IN_CRM"
            golden["reconciliation_confidence"] *= 0.9

        # 2. Demographics Resolution (Source A is master of truth)
        if demo_record:
            golden["birth_year"] = demo_record.get("birth_year")
            golden["age"] = demo_record.get("age")
            golden["education"] = demo_record.get("education_standardized", demo_record.get("education"))
            golden["marital_status"] = demo_record.get("marital_status_standardized", demo_record.get("marital_status"))
            golden["income"] = demo_record.get("income")
            golden["total_dependents"] = demo_record.get("total_dependents", 0)
            golden["has_children"] = bool(demo_record.get("has_children", False))
            golden["customer_since"] = demo_record.get("customer_since_date")
            golden["recency_days"] = demo_record.get("recency_days", 0)
            golden["total_spend"] = float(demo_record.get("total_spend", 0.0))
            golden["total_purchases"] = int(demo_record.get("total_purchases", 0))
            golden["wine_spend"] = float(demo_record.get("mnt_wines", 0.0))
            golden["meat_spend"] = float(demo_record.get("mnt_meat", 0.0))
            golden["gold_spend"] = float(demo_record.get("mnt_gold", 0.0))
        else:
            # Customer only in CRM or Transactions
            golden["birth_year"] = None
            golden["age"] = None
            golden["education"] = "Unknown"
            golden["marital_status"] = "Unknown"
            golden["income"] = None
            golden["total_dependents"] = 0
            golden["has_children"] = False
            golden["customer_since"] = crm_record.get("crm_created_at") if crm_record else None
            golden["recency_days"] = 0
            golden["total_spend"] = 0.0
            golden["total_purchases"] = 0
            golden["wine_spend"] = 0.0
            golden["meat_spend"] = 0.0
            golden["gold_spend"] = 0.0
            golden["reconciliation_confidence"] *= 0.85

        # 3. Transaction Ledger Reconciliation (Source C)
        if tx_records:
            completed_txs = [t for t in tx_records if t.get("status") == "COMPLETED"]
            golden["reconciled_transaction_count"] = len(completed_txs)
            golden["reconciled_transaction_total"] = round(sum(float(t.get("amount", 0.0)) for t in completed_txs), 2)
            
            # Check for financial variance between Demographics spend and Ledger transactions
            if demo_record and golden["total_spend"] > 0:
                variance = abs(golden["total_spend"] - golden["reconciled_transaction_total"])
                variance_pct = round((variance / golden["total_spend"]) * 100, 2)
                if variance_pct > 50.0:
                    conflict_logs.append({
                        "customer_id": cust_id,
                        "resolution_type": "FINANCIAL_SPEND_VARIANCE",
                        "conflict_field": "total_spend",
                        "source_a_value": str(golden["total_spend"]),
                        "source_b_value": str(golden["reconciled_transaction_total"]),
                        "chosen_value": str(golden["total_spend"]),
                        "resolution_rule": f"Flagged cross-system spend variance ({variance_pct}% delta). Demographics spend retained as baseline."
                    })
        else:
            golden["reconciled_transaction_count"] = 0
            golden["reconciled_transaction_total"] = 0.0

        return golden, conflict_logs

