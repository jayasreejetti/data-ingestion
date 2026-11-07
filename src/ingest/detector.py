"""
File type, encoding, and delimiter detection utilities.
"""
from pathlib import Path
import hashlib
import csv
from typing import Dict, Any, Tuple


class FileDetector:
    """Detects encoding, delimiters, and file integrity metadata."""

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Calculate SHA-256 hash of file for data provenance tracking."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def detect_encoding(file_path: Path) -> str:
        """Sniff file encoding using candidate standard encodings."""
        candidates = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        for enc in candidates:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    f.read(4096)
                return enc
            except UnicodeDecodeError:
                continue
        return "utf-8"

    @staticmethod
    def detect_csv_delimiter(file_path: Path, encoding: str = "utf-8") -> str:
        """
        Detect delimiter for text files.
        Checks tab, comma, semicolon, pipe.
        """
        delimiters = ["\t", ",", ";", "|"]
        delimiter_counts: Dict[str, int] = {d: 0 for d in delimiters}

        try:
            with open(file_path, "r", encoding=encoding, errors="ignore") as f:
                sample_lines = [f.readline() for _ in range(10)]
            
            for line in sample_lines:
                if not line.strip():
                    continue
                for d in delimiters:
                    delimiter_counts[d] += line.count(d)

            best_delimiter = max(delimiter_counts, key=delimiter_counts.get)
            if delimiter_counts[best_delimiter] > 0:
                return best_delimiter
        except Exception:
            pass
        return ","

    @classmethod
    def inspect_file(cls, file_path: str | Path) -> Dict[str, Any]:
        """Produce comprehensive structural metadata for an input file."""
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")

        ext = p.suffix.lower()
        file_size = p.stat().st_size
        sha256 = cls.compute_sha256(p)

        file_type = "unknown"
        delimiter = None
        encoding = None

        if ext in [".csv", ".tsv", ".txt"]:
            encoding = cls.detect_encoding(p)
            delimiter = cls.detect_csv_delimiter(p, encoding)
            file_type = "csv" if delimiter == "," else ("tsv" if delimiter == "\t" else "delimited_text")
        elif ext in [".xlsx", ".xls"]:
            file_type = "excel"
        elif ext == ".json":
            encoding = cls.detect_encoding(p)
            file_type = "json"
        elif ext == ".parquet":
            file_type = "parquet"

        return {
            "file_name": p.name,
            "file_path": str(p),
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 3),
            "sha256_hash": sha256,
            "extension": ext,
            "detected_type": file_type,
            "encoding": encoding,
            "delimiter": delimiter,
        }

