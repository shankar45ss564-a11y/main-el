import uuid 
from typing import Dict, Optional
from datetime import datetime, timezone

_consents: Dict[str, Dict] = {}

def init_consent(patient_id: str, hip_id: str, purpose: Dict) -> Dict:
    consent_id = str(uuid.uuid4())
    _consents[consent_id] = {
        "consentRequestId": consent_id,
        "patientId": patient_id,
        "hipId": hip_id,
        "purpose": purpose,
        "status": "REQUESTED",
        "grantedAt": None
    }
    return {"consentRequestId": consent_id, "status": "REQUESTED"}

def get_consent_status(consent_id: str) -> Optional[Dict]:
    consent = _consents.get(consent_id)
    if consent:
        return {
            "consentRequestId": consent_id,
            "status": consent["status"],
            "grantedAt": consent["grantedAt"]
        }
    return None

def fetch_consent(consent_id: str) -> Optional[Dict]:
    consent = _consents.get(consent_id)
    if consent:
        return {
            "consentRequestId": consent_id,
            "status": consent["status"],
            "consentArtefact": {"data": "encrypted-consent-artefact"}
        }
    return None

def notify_consent(consent_id: str, status: str) -> Dict:
    if consent_id in _consents:
        _consents[consent_id]["status"] = status
        if status == "GRANTED":
            _consents[consent_id]["grantedAt"] = datetime.now(timezone.utc).isoformat()
        return {"consentRequestId": consent_id, "status": status}
    
