"""
End-to-End Enterprise Data Ingestion & Reconciliation Pipeline Orchestrator.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import pandas as pd

from config.settings import (
    RAW_DIR,
    DEFAULT_INCOME_POLICY,
    DATABASE_URL
)
from src.ingest.reader import DataReader
from src.ingest.profiler import DataProfiler
from src.validate.rules import ValidationEngine
from src.validate.quarantine import QuarantineManager
from src.transform.cleaner import DataCleaner
from src.transform.standardizer import DataStandardizer
from src.storage.database import DatabaseManager
from src.reconcile.engine import ReconciliationEngine
from src.reports.metrics import QualityMetricsCalculator
from src.reports.generator import ReportGenerator


class IngestionPipeline:
    """Orchestrates the entire enterprise ingestion and reconciliation workflow."""

    def __init__(
        self,
        income_policy: str = DEFAULT_INCOME_POLICY,
        db_url: str = DATABASE_URL
    ):
        self.income_policy = income_policy
        self.db = DatabaseManager(db_url)
        self.validator = ValidationEngine(income_policy=income_policy)
        self.quarantine_mgr = QuarantineManager()
        self.standardizer = DataStandardizer()
        self.reporter = ReportGenerator()

    def run_source_a_ingestion(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Executes complete ingestion for Source A (Customer Personality Analysis dataset).
        """
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        path = Path(file_path).resolve()

        # Step 1: Ingest and detect metadata
        df_raw, file_meta = DataReader.read(path)
        file_meta["batch_id"] = batch_id
        file_meta["source_name"] = "SOURCE_A_DEMOGRAPHICS"

        # Step 2: Profile raw dataset
        profile = DataProfiler.profile_dataset(df_raw, source_name="SOURCE_A_DEMOGRAPHICS")

        # Step 3: Validate and partition into valid vs quarantined
        valid_df, quarantine_df, val_summary = self.validator.validate_source_a_customer_personality(df_raw)

        # Step 4: Persist quarantine if any failures exist
        quarantine_info = self.quarantine_mgr.persist_quarantine(
            quarantine_df,
            batch_id=batch_id,
            source_name="SOURCE_A"
        )

        # Step 5: Clean and standardize passed records
        cleaned_df = DataCleaner.clean_source_a(valid_df)

        # Step 6: Stage cleaned data
        staged_path = self.standardizer.stage_records(cleaned_df, source_name="source_a", batch_id=batch_id)

        # Step 7: Load into Warehouse Database
        records_to_load = []
        for _, row in cleaned_df.iterrows():
            rec = {
                "customer_id": int(row["ID"]),
                "birth_year": int(row["Year_Birth"]),
                "age": int(row["Age"]),
                "education": str(row["Education"]),
                "education_standardized": str(row["Education_Standardized"]),
                "marital_status": str(row["Marital_Status"]),
                "marital_status_standardized": str(row["Marital_Status_Standardized"]),
                "income": float(row["Income"]) if not pd.isna(row["Income"]) else None,
                "kidhome": int(row.get("Kidhome", 0)),
                "teenhome": int(row.get("Teenhome", 0)),
                "total_dependents": int(row.get("Total_Dependents", 0)),
                "has_children": bool(row.get("Has_Children", 0)),
                "customer_since_date": str(row.get("Customer_Since_Date", "")),
                "recency_days": int(row.get("Recency", 0)),
                "mnt_wines": float(row.get("MntWines", 0.0)),
                "mnt_fruits": float(row.get("MntFruits", 0.0)),
                "mnt_meat": float(row.get("MntMeatProducts", 0.0)),
                "mnt_fish": float(row.get("MntFishProducts", 0.0)),
                "mnt_sweets": float(row.get("MntSweetProducts", 0.0)),
                "mnt_gold": float(row.get("MntGoldProds", 0.0)),
                "total_spend": float(row.get("Total_Spend", 0.0)),
                "num_web_purchases": int(row.get("NumWebPurchases", 0)),
                "num_catalog_purchases": int(row.get("NumCatalogPurchases", 0)),
                "num_store_purchases": int(row.get("NumStorePurchases", 0)),
                "num_deals_purchases": int(row.get("NumDealsPurchases", 0)),
                "total_purchases": int(row.get("Total_Purchases", 0)),
                "num_web_visits_month": int(row.get("NumWebVisitsMonth", 0)),
                "accepted_cmp1": int(row.get("AcceptedCmp1", 0)),
                "accepted_cmp2": int(row.get("AcceptedCmp2", 0)),
                "accepted_cmp3": int(row.get("AcceptedCmp3", 0)),
                "accepted_cmp4": int(row.get("AcceptedCmp4", 0)),
                "accepted_cmp5": int(row.get("AcceptedCmp5", 0)),
                "campaigns_accepted_total": int(row.get("Campaigns_Accepted_Total", 0)),
                "campaign_response_rate": float(row.get("Campaign_Response_Rate", 0.0)),
                "complain": int(row.get("Complain", 0)),
                "response": int(row.get("Response", 0)),
                "batch_id": batch_id
            }
            records_to_load.append(rec)

        # Clear existing demographics records for idempotency during re-runs
        with self.db.get_session() as session:
            from src.storage.models import CustomerDemographicsModel, QuarantinedRecordModel
            session.query(CustomerDemographicsModel).delete()

        loaded_count = self.db.bulk_insert_demographics(records_to_load)

        # Log quarantined records in database
        if not quarantine_df.empty:
            q_records = quarantine_df.to_dict(orient="records")
            for q in q_records:
                q["batch_id"] = batch_id
                q["source_name"] = "SOURCE_A"
            self.db.bulk_insert_quarantine(q_records)

        # Record batch audit trail
        batch_audit = {
            "batch_id": batch_id,
            "source_name": "SOURCE_A",
            "file_name": path.name,
            "file_hash": file_meta["sha256_hash"],
            "file_size_bytes": file_meta["file_size_bytes"],
            "total_records": len(df_raw),
            "passed_records": len(valid_df),
            "quarantined_records": len(quarantine_df),
            "status": "COMPLETED"
        }
        self.db.record_batch_metadata(batch_audit)

        # Step 8: Calculate Quality Metrics & Generate Reports
        null_counts = df_raw.isnull().sum().to_dict()
        critical_cols = ["ID", "Year_Birth", "Income", "Education", "Marital_Status", "Dt_Customer"]
        quality_metrics = QualityMetricsCalculator.calculate_dimensions(
            total_rows=len(df_raw),
            passed_rows=len(valid_df),
            quarantined_rows=len(quarantine_df),
            null_counts=null_counts,
            duplicate_count=int(df_raw.duplicated().sum()),
            critical_cols=critical_cols
        )

        report_path = self.reporter.generate_data_quality_report(
            profile=profile,
            validation_summary=val_summary,
            quality_metrics=quality_metrics
        )

        return {
            "batch_id": batch_id,
            "file_metadata": file_meta,
            "validation_summary": val_summary,
            "quality_metrics": quality_metrics,
            "quarantine_info": quarantine_info,
            "staged_path": staged_path,
            "loaded_count": loaded_count,
            "report_path": report_path
        }

    def ingest_crm_source_b(self, file_path: str | Path) -> Dict[str, Any]:
        """Ingest Source B (CRM Excel file)."""
        batch_id = f"crm_{uuid.uuid4().hex[:10]}"
        path = Path(file_path).resolve()
        df_raw, meta = DataReader.read(path)

        cleaned_df = DataCleaner.clean_crm_source_b(df_raw)

        records = []
        for _, row in cleaned_df.iterrows():
            records.append({
                "customer_id": int(row["crm_customer_id"]),
                "first_name": str(row["first_name"]),
                "last_name": str(row["last_name"]),
                "full_name": str(row["full_name"]),
                "email": str(row["email"]) if pd.notna(row["email"]) else None,
                "phone": str(row["phone"]) if pd.notna(row["phone"]) else None,
                "city": str(row.get("city", "")),
                "country": str(row.get("country", "USA")),
                "account_status": str(row.get("account_status", "ACTIVE")),
                "crm_created_at": str(row.get("crm_created_at", "")),
                "batch_id": batch_id
            })

        with self.db.get_session() as session:
            from src.storage.models import CustomerCrmModel
            session.query(CustomerCrmModel).delete()

        loaded = self.db.bulk_insert_crm(records)
        return {"batch_id": batch_id, "loaded_count": loaded, "file_name": path.name}

    def ingest_transactions_source_c(self, file_path: str | Path) -> Dict[str, Any]:
        """Ingest Source C (Transactions JSON file)."""
        batch_id = f"tx_{uuid.uuid4().hex[:10]}"
        path = Path(file_path).resolve()
        df_raw, meta = DataReader.read(path)

        records = []
        for _, row in df_raw.iterrows():
            records.append({
                "transaction_id": str(row["transaction_id"]),
                "customer_id": int(row["customer_id"]),
                "transaction_date": str(row["transaction_date"]),
                "channel": str(row["channel"]),
                "amount": float(row["amount"]),
                "payment_method": str(row["payment_method"]),
                "status": str(row.get("status", "COMPLETED")),
                "batch_id": batch_id
            })

        with self.db.get_session() as session:
            from src.storage.models import CustomerTransactionModel
            session.query(CustomerTransactionModel).delete()

        loaded = self.db.bulk_insert_transactions(records)
        return {"batch_id": batch_id, "loaded_count": loaded, "file_name": path.name}

    def run_multi_source_reconciliation(self) -> Dict[str, Any]:
        """Execute cross-source reconciliation and generate report."""
        engine = ReconciliationEngine(self.db)
        recon_results = engine.run_reconciliation()
        report_path = self.reporter.generate_reconciliation_report(recon_results)
        recon_results["reconciliation_report_path"] = report_path
        return recon_results
