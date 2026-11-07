"""
Configuration and Settings for Enterprise Data Ingestion & Reconciliation Platform.
"""
from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
QUARANTINE_DIR = DATA_DIR / "quarantine"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"
DOCS_DIR = BASE_DIR / "docs"

# Ensure all directories exist
for directory in [DATA_DIR, RAW_DIR, STAGING_DIR, QUARANTINE_DIR, PROCESSED_DIR, REPORTS_DIR, DOCS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database Configuration
# Default to local SQLite warehouse; easily override via DATABASE_URL for PostgreSQL
DEFAULT_DB_PATH = PROCESSED_DIR / "enterprise_warehouse.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Business Validation Policies
# Income handling options: 'ACCEPT_WITH_NULL', 'QUARANTINE', 'REJECT'
DEFAULT_INCOME_POLICY = os.getenv("INCOME_POLICY", "ACCEPT_WITH_NULL")

# Demographic bounds
MIN_VALID_BIRTH_YEAR = 1920
MAX_VALID_AGE = 105
CURRENT_ANALYSIS_YEAR = 2026

# Standard taxonomies
VALID_EDUCATION_LEVELS = ["Graduation", "PhD", "Master", "2n Cycle", "Basic"]
EDUCATION_NORMALIZATION = {
    "Graduation": "Bachelor",
    "PhD": "Doctorate",
    "Master": "Master",
    "2n Cycle": "Master",
    "Basic": "Undergraduate"
}

VALID_MARITAL_STATUSES = ["Single", "Together", "Married", "Divorced", "Widow", "Alone", "Absurd", "YOLO"]
MARITAL_STATUS_NORMALIZATION = {
    "Married": "Married",
    "Together": "Cohabiting",
    "Single": "Single",
    "Divorced": "Divorced",
    "Widow": "Widowed",
    "Alone": "Single",
    "Absurd": "Unknown",
    "YOLO": "Unknown"
}

