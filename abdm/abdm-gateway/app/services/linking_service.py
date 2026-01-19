import uuid
from typing import Dict, List

_tokens: Dict[str, Dict] = {}
_txns: Dict[str, Dict] = {}

def generate_link_token(patient_id: str, hip_id: str) -> Dict:
    token = str(uuid.uuid4())
    _tokens[token] = {
        "patientId": patient_id,
        "hipId": hip_id,
    }
    return {"token": token, "expiresIn": 300}

def link_care_contexts(patient_id: str, care_contexts: List[Dict]) -> Dict:
    return {"status": "PENDING"}

def discover_patient(mobile: str, name: str | None) -> Dict:
    patient_id = f"pat-{mobile}"
    return {"patientId": patient_id, "status": "FOUND"}

def init_link(patient_id: str, txn_id: str) -> Dict:
    _txns[txn_id] = {
        "patientId": patient_id,
        "status": "INITIATED"
    }
    return {"status": "INITIATED", "txnId": txn_id}

def confirm_link(patient_id: str, txn_id: str, otp: str) -> Dict:
    _txns[txn_id] = {
        "patientId": patient_id,
        "status": "CONFIRMED"
    }
    return {"status": "CONFIRMED", "txnId": txn_id}

def notify_link(txn_id: str, status: str) -> Dict:
    _txns[txn_id] = {
        "patientId": _txns.get(txn_id, {}).get("patientId"),
        "status": status
    }
    return {"status": status, "txnId": txn_id}