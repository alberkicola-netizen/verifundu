from typing import List, Optional
from pydantic import BaseModel, UUID4
from datetime import datetime
from db.models import VerdictEnum

class ReceiptBase(BaseModel):
    bank_name: Optional[str] = None
    iban: Optional[str] = None
    amount: Optional[float] = None
    beneficiary: Optional[str] = None
    receipt_date: Optional[datetime] = None
    channel: Optional[str] = None

class ReceiptCreate(ReceiptBase):
    pass # Initial submission only needs the file

class ReceiptUpdate(BaseModel):
    verdict: Optional[VerdictEnum] = None
    fraud_score: Optional[int] = None
    failed_rules: Optional[List[str]] = None
    analyst_override: Optional[bool] = None
    analyst_note: Optional[str] = None

class ReceiptRead(ReceiptBase):
    id: UUID4
    job_id: str
    verdict: VerdictEnum
    fraud_score: Optional[int] = None
    submitted_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PipelineStatus(BaseModel):
    job_id: str
    status: VerdictEnum
    progress: float # 0 to 1
    current_stage: str
