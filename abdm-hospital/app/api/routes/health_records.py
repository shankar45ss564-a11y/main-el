"""
Health Records API Routes for ABDM Hospital.
Provides endpoints to view, manage, and track health records.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
import shutil
import tempfile
import os
import json
import logging

# Third-party ML clients used by the on-device OCR + parsing flow
try:
    from gradio_client import Client, handle_file
except Exception:
    Client = None
    handle_file = None

try:
    import google.genai as genai
except Exception:
    genai = None
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import uuid

from app.database.connection import get_db
from app.database.models import HealthRecord, Patient
from app.services.health_data_service import (
    get_health_records_for_patient,
    get_external_health_records,
    get_health_record_summary
)

router = APIRouter(prefix="/api/health-records", tags=["health-records"])


# ============================================================================
# Schemas
# ============================================================================

class HealthRecordResponse(BaseModel):
    id: str
    type: str
    date: str
    sourceHospital: Optional[str]
    data: Dict[str, Any]
    receivedAt: str
    requestId: Optional[str] = None
    # Additional fields for frontend display
    patientId: Optional[str] = None
    patientName: Optional[str] = None
    title: Optional[str] = None  # Derived from record type or data

    class Config:
        from_attributes = True


class HealthRecordSummaryResponse(BaseModel):
    totalRecords: int
    byType: Dict[str, int]
    bySource: Dict[str, int]
    lastUpdated: str


class CreateHealthRecordRequest(BaseModel):
    recordType: str
    recordDate: str
    data: Dict[str, Any]
    dataText: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/")
async def list_all_patients_with_records(
    db: Session = Depends(get_db)
):
    """
    List all patients that have health records.
    
    Returns:
    - List of patients with record counts
    """
    # Get all patients
    patients = db.execute(select(Patient)).scalars().all()
    
    result = []
    for patient in patients:
        # Count records for this patient
        record_count = db.execute(
            select(HealthRecord).where(HealthRecord.patient_id == patient.id)
        ).scalars().all()
        
        if len(record_count) > 0:
            result.append({
                "patientId": str(patient.id),
                "name": patient.name,
                "mobile": patient.mobile,
                "abhaId": patient.abha_id,
                "recordCount": len(record_count)
            })
    
    return {
        "total": len(result),
        "patients": result
    }


@router.get("/{patient_id}", response_model=List[HealthRecordResponse])
async def list_health_records(
    patient_id: str,
    record_type: Optional[str] = Query(None, description="Filter by record type (e.g., PRESCRIPTION)"),
    source_hospital: Optional[str] = Query(None, description="Filter by source hospital"),
    db: Session = Depends(get_db)
):
    """
    List all health records for a patient.
    
    Query Parameters:
    - record_type: Optional filter by type (PRESCRIPTION, DIAGNOSTIC_REPORT, etc.)
    - source_hospital: Optional filter by source hospital bridge ID
    
    Returns:
    - List of health records with all details
    """
    records = await get_health_records_for_patient(
        db=db,
        patient_id=patient_id,
        record_type=record_type,
        source_hospital=source_hospital
    )
    
    if not records:
        # Check if patient exists
        try:
            patient_uuid = uuid.UUID(patient_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid patient ID format")
        
        patient = db.execute(
            select(Patient).where(Patient.id == patient_uuid)
        ).scalar_one_or_none()
        
        if not patient:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {patient_id} not found"
            )
        
        return []
    
    return records


@router.get("/{patient_id}/summary", response_model=HealthRecordSummaryResponse)
async def get_patient_health_summary(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get summary statistics of health records for a patient.
    
    Returns:
    - Total count
    - Count by record type
    - Count by source hospital
    - Last updated timestamp
    """
    # Check if patient exists
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient ID format")
    
    patient = db.execute(
        select(Patient).where(Patient.id == patient_uuid)
    ).scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {patient_id} not found"
        )
    
    summary = await get_health_record_summary(db=db, patient_id=patient_id)
    return summary


@router.get("/{patient_id}/external", response_model=List[HealthRecordResponse])
async def list_external_health_records(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    List only health records received from other hospitals via ABDM Gateway.
    
    Returns:
    - List of external health records (those with source_hospital set)
    """
    # Check if patient exists
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient ID format")
    
    patient = db.execute(
        select(Patient).where(Patient.id == patient_uuid)
    ).scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {patient_id} not found"
        )
    
    records = await get_external_health_records(db=db, patient_id=patient_id)
    return records


@router.get("/{patient_id}/{record_id}", response_model=HealthRecordResponse)
async def get_health_record_details(
    patient_id: str,
    record_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific health record.
    
    Returns:
    - Complete health record with all fields
    """
    # Convert IDs to UUID
    try:
        patient_uuid = uuid.UUID(patient_id)
        record_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Query for the specific record
    record = db.execute(
        select(HealthRecord).where(
            and_(
                HealthRecord.id == record_uuid,
                HealthRecord.patient_id == patient_uuid
            )
        )
    ).scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Health record {record_id} not found for patient {patient_id}"
        )
    
    return {
        "id": str(record.id),
        "type": record.record_type,
        "date": record.record_date.isoformat(),
        "sourceHospital": record.source_hospital,
        "data": record.data_json,
        "receivedAt": record.created_at.isoformat(),
        "requestId": record.request_id
    }


@router.post("/{patient_id}", response_model=HealthRecordResponse)
async def create_health_record(
    patient_id: str,
    request: CreateHealthRecordRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new health record for a patient (internal use).
    
    This is used for locally generated health records,
    not for records received via ABDM Gateway.
    
    Body:
    - recordType: Type of record (PRESCRIPTION, DIAGNOSTIC_REPORT, etc.)
    - recordDate: ISO 8601 date string
    - data: JSON object with record details
    - dataText: Optional text representation
    
    Returns:
    - Created health record
    """
    # Check if patient exists
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid patient ID format")
    
    patient = db.execute(
        select(Patient).where(Patient.id == patient_uuid)
    ).scalar_one_or_none()
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {patient_id} not found"
        )
    
    # Create new health record
    new_record = HealthRecord(
        id=uuid.uuid4(),
        patient_id=patient_uuid,
        record_type=request.recordType,
        record_date=datetime.fromisoformat(request.recordDate),
        data_json=request.data,
        data_text=request.dataText,
        source_hospital=None,  # Local record
        request_id=None,
        was_encrypted=False,
        decryption_status="NONE",
        delivery_attempt=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    return {
        "id": str(new_record.id),
        "type": new_record.record_type,
        "date": new_record.record_date.isoformat(),
        "sourceHospital": new_record.source_hospital,
        "data": new_record.data_json,
        "receivedAt": new_record.created_at.isoformat(),
        "requestId": new_record.request_id
    }


@router.delete("/{patient_id}/{record_id}")
async def delete_health_record(
    patient_id: str,
    record_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a specific health record.
    
    WARNING: This permanently deletes the health record.
    Use with caution, especially for records received from other hospitals.
    
    Returns:
    - Success message
    """
    # Convert IDs to UUID
    try:
        patient_uuid = uuid.UUID(patient_id)
        record_uuid = uuid.UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    
    # Query for the specific record
    record = db.execute(
        select(HealthRecord).where(
            and_(
                HealthRecord.id == record_uuid,
                HealthRecord.patient_id == patient_uuid
            )
        )
    ).scalar_one_or_none()
    
    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Health record {record_id} not found for patient {patient_id}"
        )
    
    db.delete(record)
    db.commit()
    
    return {
        "status": "DELETED",
        "recordId": record_id,
        "message": f"Health record {record_id} deleted successfully"
    }


@router.get("/{patient_id}/by-type/{record_type}", response_model=List[HealthRecordResponse])
async def get_records_by_type(
    patient_id: str,
    record_type: str,
    db: Session = Depends(get_db)
):
    """
    Get all health records of a specific type for a patient.
    
    Path Parameters:
    - patient_id: Patient identifier
    - record_type: Type of record (PRESCRIPTION, DIAGNOSTIC_REPORT, LAB_REPORT, etc.)
    
    Returns:
    - List of health records of the specified type
    """
    records = await get_health_records_for_patient(
        db=db,
        patient_id=patient_id,
        record_type=record_type
    )
    
    if not records:
        # Check if patient exists
        try:
            patient_uuid = uuid.UUID(patient_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid patient ID format")
        
        patient = db.execute(
            select(Patient).where(Patient.id == patient_uuid)
        ).scalar_one_or_none()
        
        if not patient:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {patient_id} not found"
            )
        
        return []
    
    return records


@router.get("/{patient_id}/from-hospital/{hospital_id}", response_model=List[HealthRecordResponse])
async def get_records_from_hospital(
    patient_id: str,
    hospital_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all health records received from a specific hospital.
    
    Path Parameters:
    - patient_id: Patient identifier
    - hospital_id: Source hospital bridge ID
    
    Returns:
    - List of health records from the specified hospital
    """
    records = await get_health_records_for_patient(
        db=db,
        patient_id=patient_id,
        source_hospital=hospital_id
    )
    
    if not records:
        # Check if patient exists
        try:
            patient_uuid = uuid.UUID(patient_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid patient ID format")
        
        patient = db.execute(
            select(Patient).where(Patient.id == patient_uuid)
        ).scalar_one_or_none()
        
        if not patient:
            raise HTTPException(
                status_code=404,
                detail=f"Patient {patient_id} not found"
            )
        
        return []
    
    return records


# ============================================================================
# Additional Helper Endpoints
# ============================================================================


# ---------------------------------------------------------------------
# ML helpers (migrated from ml.py)
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiConfig:
    @staticmethod
    def api_key() -> str:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        return key

    @staticmethod
    def model() -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    @staticmethod
    def system_prompt() -> str:
        return os.getenv(
            "GEMINI_SYSTEM_PROMPT",
            (
                "You are an AI that extracts structured data from medical prescriptions.\n"
                "Extract ONLY the following fields:\n"
                "- patient_name\n"
                "- doctor_name\n"
                "- symptoms\n"
                "- prescription\n"
                "- dosage\n"
                "- doctor_notes\n\n"
                "Rules:\n"
                "1. Return ONLY a valid JSON object.\n"
                "2. No explanations, no markdown.\n"
                "3. Use null if a field is missing."
            )
        )


def _initialize_gemini_client() -> "genai.Client":
    if genai is None:
        raise RuntimeError("google.genai is not installed in the environment")
    return genai.Client(api_key=GeminiConfig.api_key())


def _build_prompt(ocr_text: str) -> str:
    return f"""
Prescription Text:
{ocr_text}

Expected JSON format:
{{
  "patient_name": null,
  "doctor_name": null,
  "symptoms": null,
  "prescription": null,
  "dosage": null,
  "doctor_notes": null
}}
""".strip()


def _parse_json_safely(text: str):
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()

    return json.loads(cleaned)


async def extract_structured_data(ocr_text: str):
    try:
        if not ocr_text or not ocr_text.strip():
            raise ValueError("OCR text is empty")

        client = _initialize_gemini_client()

        full_prompt = (
            f"{GeminiConfig.system_prompt()}\n\n"
            f"{_build_prompt(ocr_text)}"
        )

        response = await client.aio.models.generate_content(
            model=GeminiConfig.model(),
            contents=[
                {
                    "role": "user",
                    "parts": [{"text": full_prompt}],
                }
            ],
        )

        structured_data = _parse_json_safely(response.text)

        return {
            "success": True,
            "data": structured_data,
            "error": None,
        }

    except Exception as exc:
        logger.exception("Structured extraction failed")
        return {
            "success": False,
            "data": None,
            "error": str(exc),
        }


# ---------------------------------------------------------------------
# Endpoint: upload image, run OCR (gradio model), then parse with Gemini
# ---------------------------------------------------------------------
@router.post("/{patient_id}/scan")
async def scan_and_extract_prescription(
    patient_id: str,
    file: UploadFile = File(...),
):
    """
    Accept an image upload (camera/photo of prescription), run OCR using the
    Gradio demo model and then call Gemini-based extraction to return a
    structured JSON that can be used to pre-fill the create-record form.
    """
    if Client is None or handle_file is None:
        raise HTTPException(status_code=500, detail="OCR client not available on server")

    # Save uploaded file to a temp location
    tmpdir = tempfile.mkdtemp()
    try:
        filename = file.filename or "upload.png"
        tmp_path = os.path.join(tmpdir, filename)
        with open(tmp_path, "wb") as out_f:
            shutil.copyfileobj(file.file, out_f)

        try:
            client = Client("khang119966/DeepSeek-OCR-DEMO")
            result = client.predict(
                image=handle_file(tmp_path),
                model_size="Gundam (Recommended)",
                task_type="📝 Free OCR",
                ref_text="Hello!!",
                api_name="/process_ocr_task",
            )

            raw_text = result[0] if isinstance(result, (list, tuple)) else result

            extraction = await extract_structured_data(raw_text)

            return {
                "success": extraction.get("success", False),
                "ocr_text": raw_text,
                "data": extraction.get("data"),
                "error": extraction.get("error"),
            }

        except Exception as exc:
            logger.exception("Scan or extraction failed")
            raise HTTPException(status_code=500, detail=str(exc))

    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass

