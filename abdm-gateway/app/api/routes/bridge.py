from fastapi import APIRouter, Depends, HTTPException, status
from app.deps.headers import require_gateway_headers
from app.deps.auth import get_current_token
from app.api.schemas import (
    BridgeRegisterRequest, BridgeRegisterResponse,
    BridgeUrlUpdateRequest, BridgeUrlUpdateResponse,
    BridgeService
)
from app.services.bridge_service import (
    register_bridge, update_bridge_url,
    get_services_by_bridge, get_service_by_id
)

router = APIRouter(prefix="/bridge", tags=["bridge"])

@router.post("/register", response_model=BridgeRegisterResponse)
def register_bridge_endpoint(body: BridgeRegisterRequest,
                             token=Depends(get_current_token),
                             headers=Depends(require_gateway_headers)):
    # token is validated: proceed to register bridge
    data = register_bridge(body.bridgeId, body.entityType, body.name)
    return BridgeRegisterResponse(
        bridgeId=data["bridgeId"],
        entityType=data["entityType"],
        name=data["name"]
    )

@router.patch("/url", response_model=BridgeUrlUpdateResponse)
def update_url_endpoint(body: BridgeUrlUpdateRequest,
                        token=Depends(get_current_token),
                        headers=Depends(require_gateway_headers)):
    updated = update_bridge_url(body.bridgeId, str(body.webhookUrl))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Bridge not found")
    return BridgeUrlUpdateResponse(bridgeId=updated["bridgeId"], webhookUrl=updated["webhookUrl"])

@router.get("/{bridge_id}/services", response_model=list[BridgeService])
def list_services_endpoint(bridge_id: str,
                           token=Depends(get_current_token),
                           headers=Depends(require_gateway_headers)):
    return [BridgeService(**svc) for svc in get_services_by_bridge(bridge_id)]

@router.get("/service/{service_id}", response_model=BridgeService)
def get_service_endpoint(service_id: str,
                         token=Depends(get_current_token),
                         headers=Depends(require_gateway_headers)):
    svc = get_service_by_id(service_id)
    if not svc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Service not found")
    return BridgeService(**svc)