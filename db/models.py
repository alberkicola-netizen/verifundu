import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Base(DeclarativeBase):
    pass

class VerdictEnum(str, enum.Enum):
    AUTHENTIC = "AUTÊNTICO"
    FRAUD = "FALSO"
    SUSPECT = "SUSPEITO"
    PROCESSING = "PROCESSANDO"

class Receipt(Base):
    __tablename__ = "receipts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String, unique=True, index=True, nullable=False) # e.g., VF-2026-0001
    
    # Extraction Data
    bank_name = Column(String, index=True)
    bank_code = Column(String)
    iban = Column(String, index=True)
    beneficiary = Column(String)
    amount = Column(Float)
    currency = Column(String, default="Kz")
    receipt_date = Column(DateTime)
    channel = Column(String) # e.g., MULTICAIXA Express
    
    # Audit & Security
    verdict = Column(Enum(VerdictEnum), default=VerdictEnum.PROCESSING)
    fraud_score = Column(Integer) # 0-100
    ocr_confidence = Column(Float)
    ela_tamper_probability = Column(Float)
    meta_software_detected = Column(String)
    
    # Pipeline Metadata
    submitted_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    pipeline_duration_ms = Column(Integer)
    
    # Storage
    image_s3_key = Column(String) # Path in MinIO
    raw_ocr_text = Column(String)
    failed_rules = Column(JSON) # List of failed R codes
    
    # HITL (Human-in-the-Loop)
    analyst_override = Column(Boolean, default=False)
    analyst_note = Column(String)
    
    def __repr__(self):
        return f"<Receipt {self.job_id} - {self.verdict}>"

class AuditLog(Base):
    """
    Cryptographic ledger entry. 
    In a real implementation, each entry would contain a hash 
    of the previous entry + current receipt data.
    """
    __tablename__ = "audit_ledger"
    
    id = Column(Integer, primary_key=True)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"))
    entry_hash = Column(String, unique=True)
    previous_hash = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    receipt = relationship("Receipt")
