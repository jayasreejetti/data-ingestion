"""
Quarantine Manager: persists, catalogs, and manages rejected and quarantined records.
"""
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json
import pandas as pd
from config.settings import QUARANTINE_DIR


class QuarantineManager:
    """Manages quarantined records that failed validation."""

    def __init__(self, quarantine_dir: Path = QUARANTINE_DIR):
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def persist_quarantine(self, quarantine_df: pd.DataFrame, batch_id: str, source_name: str) -> Dict[str, Any]:
        """Save quarantined records to both JSON and CSV with audit metadata."""
        if quarantine_df.empty:
            return {
                "batch_id": batch_id,
                "quarantine_count": 0,
                "quarantine_file_csv": None,
                "quarantine_file_json": None
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"quarantine_{source_name}_{batch_id}_{timestamp}"
        csv_path = self.quarantine_dir / f"{base_name}.csv"
        json_path = self.quarantine_dir / f"{base_name}.json"

        # Export CSV
        quarantine_df.to_csv(csv_path, index=False)

        # Export JSON with structured metadata
        records = quarantine_df.to_dict(orient="records")
        payload = {
            "batch_id": batch_id,
            "source_name": source_name,
            "quarantined_at": datetime.now().isoformat(),
            "quarantined_record_count": len(quarantine_df),
            "records": records
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        return {
            "batch_id": batch_id,
            "quarantine_count": len(quarantine_df),
            "quarantine_file_csv": str(csv_path),
            "quarantine_file_json": str(json_path)
        }

