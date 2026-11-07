"""
Multi-format Data Reader for CSV, TSV, Excel, and JSON files.
"""
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
from src.ingest.detector import FileDetector


class DataReader:
    """Reads structured enterprise data files into pandas DataFrames with metadata."""

    @classmethod
    def read(cls, file_path: str | Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Reads any supported file format and returns (DataFrame, FileMetadata).
        """
        path = Path(file_path).resolve()
        metadata = FileDetector.inspect_file(path)
        ext = metadata["extension"]
        delimiter = metadata["delimiter"]
        encoding = metadata["encoding"] or "utf-8"

        if ext in [".csv", ".tsv", ".txt"]:
            # Auto-use detected delimiter (e.g. \t for Kaggle marketing_campaign.csv)
            df = pd.read_csv(
                path,
                sep=delimiter or "\t",
                encoding=encoding,
                low_memory=False
            )
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(path, engine="openpyxl")
        elif ext == ".json":
            df = pd.read_json(path)
        elif ext == ".parquet":
            df = pd.read_parquet(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        metadata["row_count"] = len(df)
        metadata["column_count"] = len(df.columns)
        metadata["columns"] = df.columns.tolist()

        return df, metadata

