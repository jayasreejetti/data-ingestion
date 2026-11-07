"""
End-to-End Walkthrough and Demo of the Enterprise Data Ingestion & Reconciliation Platform.
"""
import sys
from pathlib import Path
import pandas as pd
from config.settings import (
    RAW_DIR,
    PROCESSED_DIR,
    REPORTS_DIR,
    DEFAULT_INCOME_POLICY,
    DATABASE_URL
)
from src.pipeline import IngestionPipeline
from src.storage.database import DatabaseManager
from src.storage.models import (
    CanonicalCustomerModel,
    CustomerDemographicsModel,
    CustomerCrmModel,
    QuarantinedRecordModel,
    ReconciliationLogModel
)


def run_full_demo():
    print("=" * 80)
    print("  ENTERPRISE DATA INGESTION & MULTI-SOURCE RECONCILIATION PLATFORM DEMO")
    print("=" * 80)

    # Initialize Pipeline with ACCEPT_WITH_NULL policy for Missing Income
    pipeline = IngestionPipeline(income_policy="ACCEPT_WITH_NULL")

    source_a_csv = RAW_DIR / "customer_personality.csv"
    source_b_excel = RAW_DIR / "source_b_crm.xlsx"
    source_c_json = RAW_DIR / "source_c_transactions.json"

    print("\n[PHASE 1: Ingestion & Validation of Source A]")
    print(f"Target dataset: {source_a_csv}")
    res_a = pipeline.run_source_a_ingestion(source_a_csv)

    print(f"  • Raw Rows Evaluated: {res_a['validation_summary']['total_evaluated']}")
    print(f"  • Passed Validation:   {res_a['loaded_count']}")
    print(f"  • Quarantined Rows:    {res_a['quarantine_info']['quarantine_count']}")
    print(f"  • Quality Index:       {res_a['quality_metrics']['composite_quality_score']}% (Grade: {res_a['quality_metrics']['quality_grade']})")
    print(f"  • Audit Report:        {res_a['report_path']}")

    # Inspect Quarantined Records
    with pipeline.db.get_session() as session:
        q_records = session.query(QuarantinedRecordModel).limit(5).all()
        if q_records:
            print("\n  [Sample Quarantined Records]")
            for q in q_records:
                print(f"    - ID: {q.record_identifier} | Codes: {q.failure_codes} | Reason: {q.failure_reasons}")

    print("\n[PHASE 2: Ingestion of Source B (CRM Contact Systems)]")
    res_b = pipeline.ingest_crm_source_b(source_b_excel)
    print(f"  • CRM Records Ingested: {res_b['loaded_count']}")

    print("\n[PHASE 3: Ingestion of Source C (Transaction Ledger)]")
    res_c = pipeline.ingest_transactions_source_c(source_c_json)
    print(f"  • Transaction Records Ingested: {res_c['loaded_count']}")

    print("\n[PHASE 4: Multi-Source Entity Resolution & Reconciliation]")
    res_recon = pipeline.run_multi_source_reconciliation()
    recon_meta = res_recon["reconciliation_summary"]
    print(f"  • Unified Golden Records Synthesized: {res_recon['total_golden_records_created']}")
    print(f"  • Source A & B Exact Entity Matches:   {recon_meta['matched_a_and_b_count']} ({res_recon['crm_enrichment_rate_pct']}%)")
    print(f"  • Customers with Transaction Ledger:   {recon_meta['customers_with_transactions_count']} ({res_recon['transaction_coverage_pct']}%)")
    print(f"  • Cross-System Discrepancies Audited: {res_recon['total_conflicts_logged']}")
    print(f"  • Reconciliation Report:               {res_recon['reconciliation_report_path']}")

    print("\n[PHASE 5: Sample Golden Customer Records (Single Source of Truth)]")
    with pipeline.db.get_session() as session:
        golden_samples = session.query(CanonicalCustomerModel).filter(
            CanonicalCustomerModel.has_crm_match == True,
            CanonicalCustomerModel.has_transaction_history == True
        ).limit(3).all()

        for g in golden_samples:
            print("-" * 60)
            print(f"Customer ID:       {g.customer_id}")
            print(f"Full Name:         {g.full_name}")
            print(f"Email:             {g.email}")
            print(f"Phone:             {g.phone}")
            print(f"Demographics:      Age {g.age} | Education: {g.education} | Marital: {g.marital_status}")
            print(f"Annual Income:     ${g.income:,.2f}" if g.income else "Annual Income:     NULL (Preserved under Policy)")
            print(f"Historical Spend:  ${g.total_spend:,.2f}")
            print(f"Reconciled Orders: {g.reconciled_transaction_count} orders totaling ${g.reconciled_transaction_total:,.2f}")
            print(f"Sources Matched:   {g.sources_matched}")
            print(f"Confidence:        {g.reconciliation_confidence * 100:.1f}%")

    print("\n" + "=" * 80)
    print("  DEMO WALKTHROUGH COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_full_demo()

