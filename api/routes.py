from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import uuid
import os

from db.models import Receipt, VerdictEnum
from api.schemas import ReceiptRead
from infra.storage import storage
from pipeline.orchestrator import celery_app

router = APIRouter()

# ── DATABASE INJECTOR ─────────────────────────────────────────
# Note: In production, use async sessions. For now, simple sync for brevity.
POSTGRES_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'verifundu')}:{os.getenv('POSTGRES_PASSWORD', 'dev_password')}@{os.getenv('POSTGRES_HOST', 'localhost')}/{os.getenv('POSTGRES_DB', 'verifundu')}"
engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── ENDPOINTS ────────────────────────────────────────────────
@router.post("/submit", response_model=ReceiptRead)
async def submit_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Main entry point for receipt analysis.
    Saves image, creates DB entry, and fires Celery task.
    """
    # 1. Validation
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="INVALID_FILE_TYPE")

    # 2. Upload to Storage
    job_id = f"VF-{uuid.uuid4().hex[:8].upper()}"
    filename = f"{job_id}_{file.filename}"
    s3_key = storage.upload_file(file.file, filename)

    # 3. Create DB Entry
    db_receipt = Receipt(
        job_id=job_id,
        image_s3_key=s3_key,
        verdict=VerdictEnum.PROCESSING,
    )
    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)

    # 4. Trigger Celery Pipeline
    # We pass the internal ID to the worker
    celery_app.send_task(
        "pipeline.tasks.process_receipt",
        args=[str(db_receipt.id)],
        queue="pipeline"
    )

    return db_receipt

@router.get("/{job_id}", response_model=ReceiptRead)
async def get_receipt_status(job_id: str, db: Session = Depends(get_db)):
    receipt = db.query(Receipt).filter(Receipt.job_id == job_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="RECEIPT_NOT_FOUND")
    return receipt
