import uuid 
from typing import Dict, Optional, List
from datetime import datetime, timezone

_health_data: Dict[str, Dict] = {}
_data_requests: Dict[str, Dict] = {}

def send_health_info(txn_id: str, patient_id: str, hip_id: str, care_context_id: str, health_info: Dict, metadata: Dict):
    data_id = str(uuid.uuid4())
    _health_data[data_id] = {
        "txnId": txn_id,
        "patientId": patient_id,
        "hipId": hip_id,
        "careContextId": care_context_id,
        "healthInfo": health_info,
        "metadata": metadata,
        "sentAt": datetime.now(timezone.utc).isoformat()
    }
    return {"status": "RECEIVED", "txnId": txn_id}

def request_health_info(patient_id: str, hip_id: str, care_context_id: str, data_types: List[str]) -> Dict:
    request_id = str(uuid.uuid4())
    _data_requests[request_id] = {
        "patientId": patient_id,
        "hipId": hip_id,
        "careContextId": care_context_id,
        "dataTypes": data_types,
        "status": "REQUESTED",
        "requestedAt": datetime.now(timezone.utc).isoformat()
    }
    return {"requestId": request_id, "status": "REQUESTED"}

def get_data_request_status(request_id: str) -> Optional[Dict]:
    return _data_requests.get(request_id)

def notify_data_flow(txn_id: str, status: str, hip_id: str) -> Dict:
    # Find and update data entry with matching txn_id
    for data_id, data in _health_data.items():
        if data["txnId"] == txn_id:
            _health_data[data_id]["status"] = status
            break
    return {"status": "ACKNOWLEDGED"}
