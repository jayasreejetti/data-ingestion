"""
SQLAlchemy ORM Models for Enterprise Ingestion & Reconciliation.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class BatchMetadataModel(Base):
    """Tracks every file ingestion batch for data provenance and lineage."""
    __tablename__ = "ingestion_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), unique=True, nullable=False, index=True)
    source_name = Column(String(64), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    total_records = Column(Integer, nullable=False)
    passed_records = Column(Integer, nullable=False)
    quarantined_records = Column(Integer, nullable=False)
    status = Column(String(32), default="COMPLETED")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, default=datetime.utcnow)


class CustomerDemographicsModel(Base):
    """Cleaned customer demographics and marketing responses from Source A."""
    __tablename__ = "customer_demographics"

    customer_id = Column(Integer, primary_key=True, index=True)
    birth_year = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    education = Column(String(64), nullable=False)
    education_standardized = Column(String(64), nullable=False)
    marital_status = Column(String(64), nullable=False)
    marital_status_standardized = Column(String(64), nullable=False)
    income = Column(Float, nullable=True)
    kidhome = Column(Integer, default=0)
    teenhome = Column(Integer, default=0)
    total_dependents = Column(Integer, default=0)
    has_children = Column(Boolean, default=False)
    customer_since_date = Column(String(32), nullable=True)
    recency_days = Column(Integer, default=0)
    
    # Spending metrics
    mnt_wines = Column(Float, default=0.0)
    mnt_fruits = Column(Float, default=0.0)
    mnt_meat = Column(Float, default=0.0)
    mnt_fish = Column(Float, default=0.0)
    mnt_sweets = Column(Float, default=0.0)
    mnt_gold = Column(Float, default=0.0)
    total_spend = Column(Float, default=0.0)
    
    # Purchases
    num_web_purchases = Column(Integer, default=0)
    num_catalog_purchases = Column(Integer, default=0)
    num_store_purchases = Column(Integer, default=0)
    num_deals_purchases = Column(Integer, default=0)
    total_purchases = Column(Integer, default=0)
    num_web_visits_month = Column(Integer, default=0)
    
    # Marketing campaigns
    accepted_cmp1 = Column(Integer, default=0)
    accepted_cmp2 = Column(Integer, default=0)
    accepted_cmp3 = Column(Integer, default=0)
    accepted_cmp4 = Column(Integer, default=0)
    accepted_cmp5 = Column(Integer, default=0)
    campaigns_accepted_total = Column(Integer, default=0)
    campaign_response_rate = Column(Float, default=0.0)
    complain = Column(Integer, default=0)
    response = Column(Integer, default=0)
    
    batch_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CustomerCrmModel(Base):
    """Customer identity and contact attributes from Source B (CRM)."""
    __tablename__ = "customer_crm"

    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    full_name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True, index=True)
    phone = Column(String(64), nullable=True)
    city = Column(String(64), nullable=True)
    country = Column(String(64), default="USA")
    account_status = Column(String(32), default="ACTIVE")
    crm_created_at = Column(String(32), nullable=True)
    batch_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CustomerTransactionModel(Base):
    """Transaction ledger entries from Source C (Orders/Sales)."""
    __tablename__ = "customer_transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(Integer, index=True, nullable=False)
    transaction_date = Column(String(32), nullable=False)
    channel = Column(String(32), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(32), nullable=False)
    status = Column(String(32), default="COMPLETED")
    batch_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CanonicalCustomerModel(Base):
    """
    Golden Record: Single Pane of Glass Customer Master Entity
    Produced by Multi-Source Entity Resolution and Reconciliation.
    """
    __tablename__ = "canonical_customers"

    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=True)
    email = Column(String(128), nullable=True)
    phone = Column(String(64), nullable=True)
    city = Column(String(64), nullable=True)
    country = Column(String(64), nullable=True)
    account_status = Column(String(32), nullable=True)
    
    # Demographics
    birth_year = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)
    education = Column(String(64), nullable=True)
    marital_status = Column(String(64), nullable=True)
    income = Column(Float, nullable=True)
    total_dependents = Column(Integer, default=0)
    has_children = Column(Boolean, default=False)
    customer_since = Column(String(32), nullable=True)
    recency_days = Column(Integer, default=0)
    
    # Financial metrics
    total_spend = Column(Float, default=0.0)
    total_purchases = Column(Integer, default=0)
    wine_spend = Column(Float, default=0.0)
    meat_spend = Column(Float, default=0.0)
    gold_spend = Column(Float, default=0.0)
    
    # Multi-source reconciliation metadata
    sources_matched = Column(String(128), default="SOURCE_A")
    has_crm_match = Column(Boolean, default=False)
    has_transaction_history = Column(Boolean, default=False)
    reconciled_transaction_count = Column(Integer, default=0)
    reconciled_transaction_total = Column(Float, default=0.0)
    reconciliation_confidence = Column(Float, default=1.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuarantinedRecordModel(Base):
    """Stores rejected and quarantined records for governance and compliance."""
    __tablename__ = "quarantined_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), nullable=False, index=True)
    source_name = Column(String(64), nullable=False)
    record_identifier = Column(String(64), nullable=True)
    failure_codes = Column(String(255), nullable=False)
    failure_reasons = Column(Text, nullable=False)
    raw_payload_json = Column(Text, nullable=False)
    quarantined_at = Column(DateTime, default=datetime.utcnow)


class ReconciliationLogModel(Base):
    """Audit trail of cross-source reconciliation, entity resolution, and conflict decisions."""
    __tablename__ = "reconciliation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, nullable=False, index=True)
    resolution_type = Column(String(64), nullable=False)
    conflict_field = Column(String(64), nullable=True)
    source_a_value = Column(Text, nullable=True)
    source_b_value = Column(Text, nullable=True)
    chosen_value = Column(Text, nullable=True)
    resolution_rule = Column(String(128), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

