"""
Command-Line Interface (CLI) for Enterprise Data Ingestion & Reconciliation Platform.
"""
import argparse
import sys
from pathlib import Path
from config.settings import (
    RAW_DIR,
    DEFAULT_INCOME_POLICY,
    DATABASE_URL
)
from src.pipeline import IngestionPipeline
from src.ingest.reader import DataReader
from src.ingest.profiler import DataProfiler


def print_banner():
    banner = r"""
========================================================================
   ENTERPRISE DATA INGESTION & MULTI-SOURCE RECONCILIATION PLATFORM     
========================================================================
"""
    print(banner)


def main():
    print_banner()
    parser = argparse.ArgumentParser(
        description="Enterprise Data Ingestion & Reconciliation Platform CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available platform commands")

    # Command: profile
    p_profile = subparsers.add_parser("profile", help="Profile an input dataset")
    p_profile.add_argument("--file", "-f", required=True, help="Path to input data file")

    # Command: ingest
    p_ingest = subparsers.add_parser("ingest", help="Ingest and validate Source A dataset")
    p_ingest.add_argument("--file", "-f", default=str(RAW_DIR / "customer_personality.csv"), help="Path to input file")
    p_ingest.add_argument("--income-policy", "-p", choices=["ACCEPT_WITH_NULL", "QUARANTINE", "REJECT"], default=DEFAULT_INCOME_POLICY, help="Policy for handling missing income")

    # Command: reconcile
    p_recon = subparsers.add_parser("reconcile", help="Run multi-source entity resolution & reconciliation")

    # Command: stats
    p_stats = subparsers.add_parser("stats", help="Display warehouse record counts and summary")

    # Command: run-all
    p_all = subparsers.add_parser("run-all", help="Execute complete pipeline (Ingest A, B, C + Reconcile + Reports)")
    p_all.add_argument("--income-policy", "-p", choices=["ACCEPT_WITH_NULL", "QUARANTINE", "REJECT"], default=DEFAULT_INCOME_POLICY)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    pipeline = IngestionPipeline(income_policy=getattr(args, "income_policy", DEFAULT_INCOME_POLICY))

    if args.command == "profile":
        file_path = Path(args.file)
        print(f"[*] Reading and profiling file: {file_path.name}...")
        df, meta = DataReader.read(file_path)
        profile = DataProfiler.profile_dataset(df, source_name=file_path.stem)
        summary = DataProfiler.generate_markdown_summary(profile)
        print(summary)

    elif args.command == "ingest":
        file_path = Path(args.file)
        print(f"[*] Starting ingestion for {file_path.name} (Income Policy: {pipeline.income_policy})...")
        res = pipeline.run_source_a_ingestion(file_path)
        print(f"[+] Ingestion complete! Batch ID: {res['batch_id']}")
        print(f"    - Clean records loaded into Warehouse: {res['loaded_count']}")
        print(f"    - Quarantined records: {res['quarantine_info']['quarantine_count']}")
        print(f"    - Quality Score: {res['quality_metrics']['composite_quality_score']}% (Grade: {res['quality_metrics']['quality_grade']})")
        print(f"    - Report generated: {res['report_path']}")

    elif args.command == "reconcile":
        print("[*] Running multi-source reconciliation across warehouse tables...")
        res = pipeline.run_multi_source_reconciliation()
        print(f"[+] Reconciliation complete!")
        print(f"    - Master Golden Customers: {res['total_golden_records_created']}")
        print(f"    - CRM Match Rate: {res['crm_enrichment_rate_pct']}%")
        print(f"    - Transaction Coverage: {res['transaction_coverage_pct']}%")
        print(f"    - Audit Conflicts logged: {res['total_conflicts_logged']}")
        print(f"    - Report: {res['reconciliation_report_path']}")

    elif args.command == "stats":
        stats = pipeline.db.get_summary_stats()
        print("[*] Enterprise Warehouse Statistics:")
        for k, v in stats.items():
            print(f"    - {k.replace('_', ' ').title()}: {v}")

    elif args.command == "run-all":
        print("[*] Executing Full Enterprise Pipeline...")
        source_a = RAW_DIR / "customer_personality.csv"
        source_b = RAW_DIR / "source_b_crm.xlsx"
        source_c = RAW_DIR / "source_c_transactions.json"

        print(f"\n--- STEP 1: Ingesting Source A (Demographics: {source_a.name}) ---")
        res_a = pipeline.run_source_a_ingestion(source_a)
        print(f"[+] Source A Loaded: {res_a['loaded_count']} records (Quarantined: {res_a['quarantine_info']['quarantine_count']})")

        print(f"\n--- STEP 2: Ingesting Source B (CRM Contact Info: {source_b.name}) ---")
        res_b = pipeline.ingest_crm_source_b(source_b)
        print(f"[+] Source B Loaded: {res_b['loaded_count']} records")

        print(f"\n--- STEP 3: Ingesting Source C (Transaction Ledger: {source_c.name}) ---")
        res_c = pipeline.ingest_transactions_source_c(source_c)
        print(f"[+] Source C Loaded: {res_c['loaded_count']} records")

        print(f"\n--- STEP 4: Executing Multi-Source Reconciliation & Golden Record Generation ---")
        res_recon = pipeline.run_multi_source_reconciliation()
        print(f"[+] Golden Records Synthesized: {res_recon['total_golden_records_created']}")
        print(f"[+] Reconciliation Report: {res_recon['reconciliation_report_path']}")

        print(f"\n--- STEP 5: Warehouse Final State ---")
        stats = pipeline.db.get_summary_stats()
        for k, v in stats.items():
            print(f"    - {k.replace('_', ' ').title()}: {v}")
        print("\n[✔] Full pipeline completed successfully!")


if __name__ == "__main__":
    main()

