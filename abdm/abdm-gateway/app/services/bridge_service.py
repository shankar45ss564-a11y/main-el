from typing import Dict, List, Optional 

_bridges: Dict[str, Dict] = {}
_services_index: Dict[str, Dict] = {}

def register_bridge(bridge_id: str, entity_type: str, name: str) -> Dict:
    if bridge_id not in _bridges:
        _bridges[bridge_id] = {
            "bridgeId": bridge_id,
            "entityType": entity_type,
            "name": name,
            "webhookUrl": None,
            "services": []
        }
        # seed a couple of services
        for i in range(1, 3):
            svc = {
                "id": f"{bridge_id}-svc-{i}",
                "name": f"Service-{i}",
                "active": True,
                "version": "v1"
            }
            _bridges[bridge_id]["services"].append(svc)
            _services_index[svc["id"]] = svc
    return _bridges[bridge_id]

def update_bridge_url(bridge_id: str, url: str) -> Optional[Dict]:
    if bridge_id in _bridges:
        _bridges[bridge_id]["webhookUrl"] = url
        return {"bridgeId": bridge_id, "webhookUrl": url}
    return None

def get_services_by_bridge(bridge_id: str) -> List[Dict]:
    if bridge_id in _bridges:
        return _bridges[bridge_id]["services"]
    return []

def get_service_by_id(service_id: str) -> Optional[Dict]:
    return _services_index.get(service_id)