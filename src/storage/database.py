"""
Database Connection Manager and Storage Service.
"""
from contextlib import contextmanager
from typing import Generator, List, Dict, Any
from pathlib import Path
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config.settings import DATABASE_URL
from src.storage.models import (
    Base,
    BatchMetadataModel,
    CustomerDemographicsModel,
    CustomerCrmModel,
    CustomerTransactionModel,
    CanonicalCustomerModel,
    QuarantinedRecordModel,
    ReconciliationLogModel
)


class DatabaseManager:
    """Manages database connection lifecycle, migrations, and transactional CRUD."""

    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        self.engine = create_engine(db_url, echo=False, connect_args=connect_args)
        self.SessionFactory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.init_db()

    def init_db(self) -> None:
        """Create all tables if they do not already exist."""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Transactional context manager with automatic rollback on error."""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def record_batch_metadata(self, metadata: Dict[str, Any]) -> BatchMetadataModel:
        """Insert or update batch metadata audit record."""
        with self.get_session() as session:
            batch = BatchMetadataModel(
                batch_id=metadata["batch_id"],
                source_name=metadata["source_name"],
                file_name=metadata["file_name"],
                file_hash=metadata["file_hash"],
                file_size_bytes=metadata.get("file_size_bytes", 0),
                total_records=metadata.get("total_records", 0),
                passed_records=metadata.get("passed_records", 0),
                quarantined_records=metadata.get("quarantined_records", 0),
                status=metadata.get("status", "COMPLETED")
            )
            session.add(batch)
            return batch

    def bulk_insert_demographics(self, records: List[Dict[str, Any]]) -> int:
        """Insert cleaned demographics records."""
        if not records:
            return 0
        with self.get_session() as session:
            objects = [CustomerDemographicsModel(**r) for r in records]
            session.bulk_save_objects(objects)
            return len(objects)

    def bulk_insert_crm(self, records: List[Dict[str, Any]]) -> int:
        """Insert CRM contact records."""
        if not records:
            return 0
        with self.get_session() as session:
            objects = [CustomerCrmModel(**r) for r in records]
            session.bulk_save_objects(objects)
            return len(objects)

    def bulk_insert_transactions(self, records: List[Dict[str, Any]]) -> int:
        """Insert transaction ledger records."""
        if not records:
            return 0
        with self.get_session() as session:
            objects = [CustomerTransactionModel(**r) for r in records]
            session.bulk_save_objects(objects)
            return len(objects)

    def bulk_insert_quarantine(self, records: List[Dict[str, Any]]) -> int:
        """Log quarantined records in database for reporting."""
        if not records:
            return 0
        with self.get_session() as session:
            objects = []
            for r in records:
                cid = str(r.get("ID") or r.get("id") or r.get("customer_id") or "UNKNOWN")
                codes = ",".join(r.get("_quarantine_codes", ["RULE_VIOLATION"]))
                reasons = str(r.get("_quarantine_reasons", "Unknown validation failure"))
                
                # Exclude internal metadata from stored json payload
                clean_payload = {k: v for k, v in r.items() if not k.startswith("_")}
                
                objects.append(QuarantinedRecordModel(
                    batch_id=r.get("batch_id", "UNKNOWN"),
                    source_name=r.get("source_name", "UNKNOWN"),
                    record_identifier=cid,
                    failure_codes=codes,
                    failure_reasons=reasons,
                    raw_payload_json=json.dumps(clean_payload, default=str)
                ))
            session.bulk_save_objects(objects)
            return len(objects)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Fetch high-level record counts across warehouse tables."""
        with self.get_session() as session:
            return {
                "batches_processed": session.query(BatchMetadataModel).count(),
                "demographics_count": session.query(CustomerDemographicsModel).count(),
                "crm_count": session.query(CustomerCrmModel).count(),
                "transactions_count": session.query(CustomerTransactionModel).count(),
                "canonical_customers_count": session.query(CanonicalCustomerModel).count(),
                "quarantined_count": session.query(QuarantinedRecordModel).count(),
                "reconciliation_events": session.query(ReconciliationLogModel).count()
            }

