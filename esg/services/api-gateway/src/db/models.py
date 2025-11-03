"""SQLAlchemy models for all database tables."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    DECIMAL,
    CheckConstraint,
    UniqueConstraint,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class CompanyCatalog(Base):
    """Company catalog table model."""

    __tablename__ = "company_catalog"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(Text, nullable=False)
    industry = Column(Text)
    symbol = Column(Text, nullable=False)
    series = Column(Text)
    isin_code = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("symbol", "isin_code", name="uq_symbol_isin"),)

    # Relationships
    ingestion_metadata = relationship("IngestionMetadata", back_populates="company")
    extracted_indicators = relationship("ExtractedIndicator", back_populates="company")
    esg_scores = relationship("ESGScore", back_populates="company")

    def __repr__(self):
        return f"<CompanyCatalog(id={self.id}, name={self.company_name}, symbol={self.symbol})>"


class IngestionMetadata(Base):
    """Ingestion metadata table model."""

    __tablename__ = "ingestion_metadata"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_catalog.id"), nullable=False)
    source = Column(Text, nullable=False)  # NSE, MCA, CPCB, SPCB, NEWS
    file_path = Column(Text, nullable=False)  # MinIO path
    file_type = Column(Text, nullable=False)  # pdf, csv, json
    ingested_at = Column(TIMESTAMP, default=datetime.utcnow)
    status = Column(Text, default="SUCCESS")

    __table_args__ = (
        UniqueConstraint("company_id", "source", "file_path", name="uq_company_source_path"),
    )

    # Relationships
    company = relationship("CompanyCatalog", back_populates="ingestion_metadata")

    def __repr__(self):
        return f"<IngestionMetadata(id={self.id}, company_id={self.company_id}, source={self.source})>"


class DocumentEmbedding(Base):
    """Document embeddings table model."""

    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    object_key = Column(Text, index=True)
    company_name = Column(Text, index=True)
    report_year = Column(Integer, index=True)
    page_number = Column(Integer)
    chunk_index = Column(Integer)
    embedding = Column(Vector(3072))
    chunk_text = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"<DocumentEmbedding(id={self.id}, object_key={self.object_key}, page={self.page_number})>"


class BRSRIndicator(Base):
    """BRSR Core indicator definitions table model."""

    __tablename__ = "brsr_indicators"

    id = Column(Integer, primary_key=True, index=True)
    indicator_code = Column(Text, nullable=False, unique=True)
    attribute_number = Column(
        Integer,
        nullable=False,
        index=True,
    )
    parameter_name = Column(Text, nullable=False)
    measurement_unit = Column(Text)
    description = Column(Text)
    pillar = Column(Text, nullable=False, index=True)
    weight = Column(DECIMAL(5, 4), nullable=False, default=1.0)
    data_assurance_approach = Column(Text)
    brsr_reference = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("attribute_number >= 1 AND attribute_number <= 9", name="ck_attribute_range"),
        CheckConstraint("pillar IN ('E', 'S', 'G')", name="ck_pillar_values"),
    )

    # Relationships
    extracted_indicators = relationship("ExtractedIndicator", back_populates="indicator")

    def __repr__(self):
        return f"<BRSRIndicator(id={self.id}, code={self.indicator_code}, pillar={self.pillar})>"


class ExtractedIndicator(Base):
    """Extracted indicators table model."""

    __tablename__ = "extracted_indicators"

    id = Column(Integer, primary_key=True, index=True)
    object_key = Column(Text, nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("company_catalog.id"), nullable=False, index=True)
    report_year = Column(Integer, nullable=False, index=True)
    indicator_id = Column(Integer, ForeignKey("brsr_indicators.id"), nullable=False, index=True)
    extracted_value = Column(Text, nullable=False)
    numeric_value = Column(DECIMAL)
    confidence_score = Column(DECIMAL(3, 2))
    validation_status = Column(Text, default="pending", index=True)
    source_pages = Column(ARRAY(Integer))
    source_chunk_ids = Column(ARRAY(Integer))
    extracted_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("object_key", "indicator_id", name="uq_object_indicator"),
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="ck_confidence_range",
        ),
        CheckConstraint(
            "validation_status IN ('valid', 'invalid', 'pending')",
            name="ck_validation_status",
        ),
    )

    # Relationships
    company = relationship("CompanyCatalog", back_populates="extracted_indicators")
    indicator = relationship("BRSRIndicator", back_populates="extracted_indicators")

    def __repr__(self):
        return f"<ExtractedIndicator(id={self.id}, company_id={self.company_id}, indicator_id={self.indicator_id})>"


class ESGScore(Base):
    """ESG scores table model."""

    __tablename__ = "esg_scores"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_catalog.id"), nullable=False, index=True)
    report_year = Column(Integer, nullable=False, index=True)
    environmental_score = Column(DECIMAL(5, 2))
    social_score = Column(DECIMAL(5, 2))
    governance_score = Column(DECIMAL(5, 2))
    overall_score = Column(DECIMAL(5, 2))
    calculation_metadata = Column(JSONB)
    calculated_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("company_id", "report_year", name="uq_company_year"),)

    # Relationships
    company = relationship("CompanyCatalog", back_populates="esg_scores")

    def __repr__(self):
        return f"<ESGScore(id={self.id}, company_id={self.company_id}, year={self.report_year}, overall={self.overall_score})>"


class User(Base):
    """User table model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    is_admin = Column(Integer, default=0)  # 1 = admin, 0 = regular user
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class APIKey(Base):
    """API key table model for API authentication."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    scopes = Column(JSONB, default=list)  # List of permission scopes
    is_active = Column(Integer, default=1)  # 1 = active, 0 = revoked
    last_used_at = Column(TIMESTAMP, nullable=True)
    expires_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, user_id={self.user_id}, name={self.key_name}, prefix={self.key_prefix})>"
