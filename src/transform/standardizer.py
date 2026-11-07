"""
Data Standardizer and Staging Writer.
"""
from pathlib import Path
from datetime import datetime
import pandas as pd
from config.settings import STAGING_DIR


class DataStandardizer:
    """Manages mapping to canonical models and staging file generation."""

    def __init__(self, staging_dir: Path = STAGING_DIR):
        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def stage_records(self, df: pd.DataFrame, source_name: str, batch_id: str) -> str:
        """Persist cleaned records to staging directory for downstream database load."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"staged_{source_name}_{batch_id}_{timestamp}.csv"
        target_path = self.staging_dir / filename
        df.to_csv(target_path, index=False)
        return str(target_path)

