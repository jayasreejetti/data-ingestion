"""
Pydantic Schemas for Multi-Source Ingestion & Canonical Master Data.
"""
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, field_validator


class SourceACustomerSchema(BaseModel):
    """Schema definition for Source A raw demographic & marketing records."""
    ID: int = Field(ge=0, description="Customer unique identifier")
    Year_Birth: int = Field(ge=1900, le=2026)
    Education: str
    Marital_Status: str
    Income: Optional[float] = None
    Kidhome: int = Field(ge=0)
    Teenhome: int = Field(ge=0)
    Dt_Customer: str
    Recency: int = Field(ge=0)
    MntWines: float = Field(ge=0.0)
    MntFruits: float = Field(ge=0.0)
    MntMeatProducts: float = Field(ge=0.0)
    MntFishProducts: float = Field(ge=0.0)
    MntSweetProducts: float = Field(ge=0.0)
    MntGoldProds: float = Field(ge=0.0)
    NumDealsPurchases: int = Field(ge=0)
    NumWebPurchases: int = Field(ge=0)
    NumCatalogPurchases: int = Field(ge=0)
    NumStorePurchases: int = Field(ge=0)
    NumWebVisitsMonth: int = Field(ge=0)
    AcceptedCmp3: int = Field(ge=0, le=1)
    AcceptedCmp4: int = Field(ge=0, le=1)
    AcceptedCmp5: int = Field(ge=0, le=1)
    AcceptedCmp1: int = Field(ge=0, le=1)
    AcceptedCmp2: int = Field(ge=0, le=1)
    Complain: int = Field(ge=0, le=1)
    Response: int = Field(ge=0, le=1)


class SourceBCrmSchema(BaseModel):
    """Schema definition for Source B CRM customer contact data."""
    crm_customer_id: int = Field(ge=0)
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = "USA"
    account_status: str = "ACTIVE"
    crm_created_at: Optional[str] = None


class SourceCTransactionSchema(BaseModel):
    """Schema definition for Source C E-commerce / POS transactions."""
    transaction_id: str
    customer_id: int = Field(ge=0)
    transaction_date: str
    channel: str
    amount: float = Field(ge=0.0)
    payment_method: str
    status: str = "COMPLETED"


class CanonicalCustomerSchema(BaseModel):
    """
    Unified Golden Master Record combining Demographics, CRM, and Transaction Summaries.
    """
    master_customer_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    
    # Demographics
    birth_year: int
    age: int
    education_level: str
    marital_status: str
    annual_income: Optional[float] = None
    kid_count: int = 0
    teen_count: int = 0
    total_dependents: int = 0
    has_children: bool = False
    
    # Engagement & Enrollment
    customer_since: Optional[date] = None
    recency_days: int = 0
    crm_status: Optional[str] = None
    
    # Spend & Purchase aggregates
    total_spend: float = 0.0
    total_purchases: int = 0
    web_purchases: int = 0
    store_purchases: int = 0
    catalog_purchases: int = 0
    wine_spend: float = 0.0
    meat_spend: float = 0.0
    gold_spend: float = 0.0
    
    # Marketing campaigns
    total_campaigns_accepted: int = 0
    campaign_response_rate: float = 0.0
    has_complained: bool = False
    
    # Reconciliation Audit
    sources_matched: str = "SOURCE_A"
    reconciliation_confidence: float = 1.0

