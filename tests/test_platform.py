"""
Unit and Integration Test Suite for Enterprise Data Ingestion & Reconciliation Platform.
"""
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

from config.settings import RAW_DIR
from src.ingest.detector import FileDetector
from src.ingest.reader import DataReader
from src.ingest.profiler import DataProfiler
from src.validate.rules import ValidationEngine
from src.transform.cleaner import DataCleaner
from src.storage.database import DatabaseManager
from src.reconcile.matcher import EntityMatcher
from src.reconcile.resolver import ConflictResolver
from src.reports.metrics import QualityMetricsCalculator


class TestEnterpriseDataPlatform(unittest.TestCase):
    """Test suite covering ingestion, validation, quarantine, storage, and reconciliation."""

    def setUp(self):
        self.csv_path = RAW_DIR / "customer_personality.csv"
        self.excel_path = RAW_DIR / "customer_personality_source.xlsx"
        self.crm_path = RAW_DIR / "source_b_crm.xlsx"
        self.tx_path = RAW_DIR / "source_c_transactions.json"

    def test_01_file_detector(self):
        """Verify delimiter detection accurately identifies tab separator."""
        meta = FileDetector.inspect_file(self.csv_path)
        self.assertEqual(meta["delimiter"], "\t")
        self.assertEqual(meta["detected_type"], "tsv")
        self.assertTrue(len(meta["sha256_hash"]) == 64)

    def test_02_data_reader(self):
        """Verify multi-format reader correctly loads CSV and Excel."""
        df_csv, meta_csv = DataReader.read(self.csv_path)
        self.assertEqual(len(df_csv), 2240)
        self.assertEqual(len(df_csv.columns), 29)

        df_excel, meta_excel = DataReader.read(self.excel_path)
        self.assertEqual(len(df_excel), 2240)

    def test_03_data_profiler(self):
        """Verify profiler detects missing Income and Year_Birth anomalies."""
        df, _ = DataReader.read(self.csv_path)
        profile = DataProfiler.profile_dataset(df, "Source_A_Test")
        self.assertIn("Income", profile["columns_with_nulls"])
        self.assertEqual(profile["columns_with_nulls"]["Income"]["missing_count"], 24)
        
        # Verify birth year anomaly detected
        issues = [a["column"] for a in profile["anomalies"]]
        self.assertIn("Year_Birth", issues)

    def test_04_validation_engine_income_policies(self):
        """Verify configurable Income policy behavior."""
        df, _ = DataReader.read(self.csv_path)

        # Policy 1: ACCEPT_WITH_NULL
        engine_accept = ValidationEngine(income_policy="ACCEPT_WITH_NULL")
        valid_df1, q_df1, summary1 = engine_accept.validate_source_a_customer_personality(df)
        
        # In ACCEPT_WITH_NULL, only 3 records with Year_Birth < 1920 should be quarantined
        self.assertEqual(len(q_df1), 3)
        self.assertEqual(len(valid_df1), 2237)

        # Policy 2: QUARANTINE
        engine_quarantine = ValidationEngine(income_policy="QUARANTINE")
        valid_df2, q_df2, summary2 = engine_quarantine.validate_source_a_customer_personality(df)
        
        # In QUARANTINE, 24 missing income + 3 invalid birth years = 27 quarantined
        self.assertEqual(len(q_df2), 27)
        self.assertEqual(len(valid_df2), 2213)

    def test_05_cleaner_and_transformation(self):
        """Verify date conversion and categorical standardizations."""
        sample_data = pd.DataFrame([{
            "ID": 100,
            "Year_Birth": 1980,
            "Education": "2n Cycle",
            "Marital_Status": "Together",
            "Income": 50000.0,
            "Kidhome": 1,
            "Teenhome": 0,
            "Dt_Customer": "04-09-2012",
            "MntWines": 100,
            "MntFruits": 20,
            "MntMeatProducts": 50,
            "MntFishProducts": 10,
            "MntSweetProducts": 10,
            "MntGoldProds": 10,
            "NumWebPurchases": 3,
            "NumCatalogPurchases": 1,
            "NumStorePurchases": 4,
            "AcceptedCmp1": 0,
            "AcceptedCmp2": 0,
            "AcceptedCmp3": 1,
            "AcceptedCmp4": 0,
            "AcceptedCmp5": 0,
        }])
        cleaned = DataCleaner.clean_source_a(sample_data)
        self.assertEqual(cleaned["Education_Standardized"].iloc[0], "Master")
        self.assertEqual(cleaned["Marital_Status_Standardized"].iloc[0], "Cohabiting")
        self.assertEqual(cleaned["Customer_Since_Date"].iloc[0], "2012-09-04")
        self.assertEqual(cleaned["Total_Spend"].iloc[0], 200.0)
        self.assertEqual(cleaned["Total_Purchases"].iloc[0], 8)
        self.assertEqual(cleaned["Has_Children"].iloc[0], 1)

    def test_06_entity_matching_and_reconciliation(self):
        """Verify multi-source entity matcher and golden record resolution."""
        demo = pd.DataFrame([{"customer_id": 101, "birth_year": 1985, "age": 41, "income": 65000.0, "total_spend": 300.0}])
        crm = pd.DataFrame([{"crm_customer_id": 101, "first_name": "Alice", "last_name": "Smith", "full_name": "Alice Smith", "email": "alice@test.com"}])
        tx = pd.DataFrame([{"transaction_id": "T1", "customer_id": 101, "amount": 150.0, "status": "COMPLETED"}])

        match_stats = EntityMatcher.match_entities(demo, crm, tx)
        self.assertEqual(match_stats["matched_a_and_b_count"], 1)

        golden, conflicts = ConflictResolver.resolve_customer_entity(
            cust_id=101,
            demo_record=demo.iloc[0].to_dict(),
            crm_record=crm.iloc[0].to_dict(),
            tx_records=tx.to_dict(orient="records")
        )
        self.assertEqual(golden["full_name"], "Alice Smith")
        self.assertEqual(golden["email"], "alice@test.com")
        self.assertEqual(golden["birth_year"], 1985)
        self.assertEqual(golden["reconciled_transaction_count"], 1)
        self.assertEqual(golden["reconciled_transaction_total"], 150.0)

    def test_07_quality_metrics(self):
        """Verify data quality scorecard calculation."""
        metrics = QualityMetricsCalculator.calculate_dimensions(
            total_rows=1000,
            passed_rows=990,
            quarantined_rows=10,
            null_counts={"Income": 10},
            duplicate_count=0,
            critical_cols=["ID", "Year_Birth", "Income"]
        )
        self.assertGreaterEqual(metrics["composite_quality_score"], 90.0)
        self.assertEqual(metrics["quality_grade"], "A+")


if __name__ == "__main__":
    unittest.main()

