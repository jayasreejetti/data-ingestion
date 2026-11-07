"""
Data Cleaner: normalizes raw fields, cleans strings, and parses dates.
"""
from datetime import datetime
from typing import Optional, Any
import pandas as pd
from config.settings import (
    EDUCATION_NORMALIZATION,
    MARITAL_STATUS_NORMALIZATION,
    CURRENT_ANALYSIS_YEAR
)


class DataCleaner:
    """Performs deterministic cleansing on validated records."""

    @staticmethod
    def parse_date(date_val: Any) -> Optional[str]:
        """Convert heterogeneous date strings to ISO-8601 YYYY-MM-DD."""
        if pd.isna(date_val):
            return None
        date_str = str(date_val).strip()
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @classmethod
    def clean_source_a(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize Source A customer personality dataset."""
        cleaned = df.copy()

        # Clean string columns: strip whitespace
        for col in ["Education", "Marital_Status"]:
            if col in cleaned.columns:
                cleaned[col] = cleaned[col].astype(str).str.strip()

        # Standardize categorical mappings
        cleaned["Education_Standardized"] = cleaned["Education"].map(
            lambda x: EDUCATION_NORMALIZATION.get(x, x)
        )
        cleaned["Marital_Status_Standardized"] = cleaned["Marital_Status"].map(
            lambda x: MARITAL_STATUS_NORMALIZATION.get(x, "Unknown")
        )

        # Standardize dates
        if "Dt_Customer" in cleaned.columns:
            cleaned["Customer_Since_Date"] = cleaned["Dt_Customer"].apply(cls.parse_date)

        # Calculate derived analytical attributes
        if "Year_Birth" in cleaned.columns:
            cleaned["Age"] = CURRENT_ANALYSIS_YEAR - cleaned["Year_Birth"].astype(int)

        kid = cleaned["Kidhome"] if "Kidhome" in cleaned.columns else 0
        teen = cleaned["Teenhome"] if "Teenhome" in cleaned.columns else 0
        cleaned["Total_Dependents"] = kid + teen
        cleaned["Has_Children"] = (cleaned["Total_Dependents"] > 0).astype(int)

        # Spend aggregates
        spend_cols = [c for c in ["MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds"] if c in cleaned.columns]
        cleaned["Total_Spend"] = cleaned[spend_cols].sum(axis=1)

        # Purchase aggregates
        purch_cols = [c for c in ["NumWebPurchases", "NumCatalogPurchases", "NumStorePurchases"] if c in cleaned.columns]
        cleaned["Total_Purchases"] = cleaned[purch_cols].sum(axis=1)

        # Marketing campaign response rate
        cmp_cols = [c for c in ["AcceptedCmp1", "AcceptedCmp2", "AcceptedCmp3", "AcceptedCmp4", "AcceptedCmp5"] if c in cleaned.columns]
        cleaned["Campaigns_Accepted_Total"] = cleaned[cmp_cols].sum(axis=1)
        cleaned["Campaign_Response_Rate"] = round(cleaned["Campaigns_Accepted_Total"] / 5.0, 3)

        return cleaned

    @classmethod
    def clean_crm_source_b(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Clean CRM source data."""
        cleaned = df.copy()
        if "first_name" in cleaned.columns:
            cleaned["first_name"] = cleaned["first_name"].astype(str).str.strip().str.title()
        if "last_name" in cleaned.columns:
            cleaned["last_name"] = cleaned["last_name"].astype(str).str.strip().str.title()
        if "email" in cleaned.columns:
            cleaned["email"] = cleaned["email"].astype(str).str.strip().str.lower()
            cleaned.loc[cleaned["email"].isin(["none", "nan", ""],), "email"] = None
        if "account_status" in cleaned.columns:
            cleaned["account_status"] = cleaned["account_status"].astype(str).str.strip().str.upper()

        cleaned["full_name"] = cleaned["first_name"] + " " + cleaned["last_name"]
        return cleaned
