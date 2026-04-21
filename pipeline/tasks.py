import time
from celery import shared_task
from typing import Dict
from sqlalchemy.orm import Session
from datetime import datetime
import structlog

from pipeline.orchestrator import celery_app
from db.models import Receipt, VerdictEnum, SessionLocal
from angola_domain.logic import validate_angola_iban, extract_amount_from_ocr

logger = structlog.get_logger()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@celery_app.task(name="pipeline.tasks.process_receipt")
def process_receipt(receipt_id: str):
    """
    Main processing pipeline. 
    In a real app, this would involve calling PaddleOCR and YOLOv8 models.
    """
    start_time = time.time()
    db = next(get_db())
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    
    if not receipt:
        logger.error("receipt_not_found", receipt_id=receipt_id)
        return

    logger.info("processing_started", job_id=receipt.job_id)

    try:
        # 1. Preprocessing (Simulated)
        # In reality: cv2.GaussianBlur, deskewing, etc.
        time.sleep(0.5)
        
        # 2. OCR (Simulated for now)
        # In reality: ocr = PaddleOCR(use_angle_cls=True); result = ocr.ocr(img_path)
        # Let's mock the text we "extracted" to test our domain logic
        mock_ocr_lines = [
            "BANCO ANGOLANO DE INVESTIMENTOS",
            "COMPROVATIVO DE TRANSFERENCIA",
            "IBAN: AO06004000007247845910146",
            "MONTANTE: 35.000,00 Kz",
            "BENEFICIARIO: JOAO PEDRO",
            "DATA: 2026-04-21"
        ]
        receipt.raw_ocr_text = "\n".join(mock_ocr_lines)
        
        # 3. Domain Parsing (Using fixed logic)
        iban_res = validate_angola_iban(mock_ocr_lines[2])
        amount_res = extract_amount_from_ocr(mock_ocr_lines)
        
        receipt.bank_name = iban_res.bank.name if iban_res.bank else "Unknown"
        receipt.bank_code = iban_res.bank.code if iban_res.bank else None
        receipt.iban = iban_res.iban_formatted
        receipt.amount = amount_res["amount"]
        receipt.beneficiary = "JOAO PEDRO"
        
        # 4. Rules Engine & Computer Vision (Simulated)
        # R02 Checksum Check
        if not iban_res.is_valid:
            receipt.verdict = VerdictEnum.FRAUD
            receipt.fraud_score = 95
            receipt.failed_rules = ["R02"]
        else:
            receipt.verdict = VerdictEnum.AUTHENTIC
            receipt.fraud_score = 5
            receipt.failed_rules = []

        # 5. Finalize
        receipt.processed_at = datetime.utcnow()
        receipt.pipeline_duration_ms = int((time.time() - start_time) * 1000)
        
        db.commit()
        logger.info("processing_finished", job_id=receipt.job_id, verdict=receipt.verdict)

    except Exception as e:
        logger.error("processing_failed", job_id=receipt.job_id, error=str(e))
        receipt.verdict = VerdictEnum.SUSPECT
        db.commit()
        raise e
