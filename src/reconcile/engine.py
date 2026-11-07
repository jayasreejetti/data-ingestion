"""
Multi-Source Reconciliation Engine.
"""
from typing import Dict, Any, List
import pandas as pd
from src.reconcile.matcher import EntityMatcher
from src.reconcile.resolver import ConflictResolver
from src.storage.database import DatabaseManager
from src.storage.models import (
    CustomerDemographicsModel,
    CustomerCrmModel,
    CustomerTransactionModel,
    CanonicalCustomerModel,
    ReconciliationLogModel
)


class ReconciliationEngine:
    """End-to-end reconciliation orchestrator across warehouse tables."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def run_reconciliation(self) -> Dict[str, Any]:
        """
        Executes cross-source matching, conflict resolution, and golden customer load.
        """
        with self.db.get_session() as session:
            # 1. Fetch raw data tables into DataFrames for fast vector processing
            demographics = [r.__dict__ for r in session.query(CustomerDemographicsModel).all()]
            crms = [r.__dict__ for r in session.query(CustomerCrmModel).all()]
            transactions = [r.__dict__ for r in session.query(CustomerTransactionModel).all()]

        df_demo = pd.DataFrame(demographics)
        df_crm = pd.DataFrame(crms)
        df_tx = pd.DataFrame(transactions)

        # 2. Match entities across sources
        match_stats = EntityMatcher.match_entities(df_demo, df_crm, df_tx)

        # Pre-index records by customer_id for fast lookup
        demo_map = {int(r["customer_id"]): r for r in demographics} if demographics else {}
        crm_map = {int(r["customer_id"]): r for r in crms} if crms else {}
        tx_map: Dict[int, List[Dict[str, Any]]] = {}
        for t in transactions:
            cid = int(t["customer_id"])
            tx_map.setdefault(cid, []).append(t)

        all_cids = set(demo_map.keys()).union(set(crm_map.keys()))

        golden_records = []
        all_conflicts = []

        # 3. Resolve conflicts and synthesize golden records
        for cid in all_cids:
            demo_rec = demo_map.get(cid)
            crm_rec = crm_map.get(cid)
            cust_txs = tx_map.get(cid, [])

            golden, conflicts = ConflictResolver.resolve_customer_entity(
                cust_id=cid,
                demo_record=demo_rec,
                crm_record=crm_rec,
                tx_records=cust_txs
            )
            golden_records.append(golden)
            all_conflicts.extend(conflicts)

        # 4. Upsert golden records and audit logs into database
        with self.db.get_session() as session:
            # Clear existing canonical table for clean idempotency
            session.query(CanonicalCustomerModel).delete()
            session.query(ReconciliationLogModel).delete()

            # Insert Golden Customers
            canonical_objs = [CanonicalCustomerModel(**g) for g in golden_records]
            session.bulk_save_objects(canonical_objs)

            # Insert Conflict Logs
            log_objs = [ReconciliationLogModel(**c) for c in all_conflicts]
            session.bulk_save_objects(log_objs)

        return {
            "reconciliation_summary": match_stats,
            "total_golden_records_created": len(golden_records),
            "total_conflicts_logged": len(all_conflicts),
            "crm_enrichment_rate_pct": round((match_stats["matched_a_and_b_count"] / match_stats["source_a_count"]) * 100, 2) if match_stats["source_a_count"] else 0.0,
            "transaction_coverage_pct": round((match_stats["customers_with_transactions_count"] / match_stats["total_unique_customers"]) * 100, 2) if match_stats["total_unique_customers"] else 0.0
        }

