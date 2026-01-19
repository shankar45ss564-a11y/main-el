from fastapi import APIRouter, Depends, HTTPException, status
from app.deps.headers import require_gateway_headers
from app.deps.auth import get_current_token
from app.api.schemas import (
    LinkTokenRequest, LinkTokenResponse,
    LinkCareContextRequest, LinkCareContextResponse,
    DiscoverPatientRequest, DiscoverPatientResponse,
    LinkInitRequest, LinkInitResponse,
    LinkConfirmRequest, LinkConfirmResponse,
    LinkNotifyRequest
)
from app.services.linking_service import (
    generate_link_token, link_care_contexts,
    discover_patient, init_link, confirm_link, notify_link
)

router = APIRouter(prefix="/link", tags=["linking"])

@router.post("/token/generate", response_model=LinkTokenResponse)
def generate_token(body: LinkTokenRequest,
                    token=Depends(get_current_token),
                    headers=Depends(require_gateway_headers)):
    return LinkTokenResponse(**generate_link_token(body.patientId, body.hipId))

@router.post("/carecontext", response_model=LinkCareContextResponse)
def link_carecontext(body: LinkCareContextRequest,
                     token=Depends(get_current_token),
                     headers=Depends(require_gateway_headers)):
    return LinkCareContextResponse(**link_care_contexts(body.patientId, [cc.dict() for cc in body.careContexts]))

@router.post("/discover", response_model=DiscoverPatientResponse)
def discover(body: DiscoverPatientRequest,
             token=Depends(get_current_token),
             headers=Depends(require_gateway_headers)):
    return DiscoverPatientResponse(**discover_patient(body.mobile, body.name))

@router.post("/init", response_model=LinkInitResponse)
def init(body: LinkInitRequest,
                       token=Depends(get_current_token),
                       headers=Depends(require_gateway_headers)):
    return LinkInitResponse(**init_link(body.patientId, body.txnId))

@router.post("/confirm", response_model=LinkConfirmResponse)
def confirm(body: LinkConfirmRequest,
                          token=Depends(get_current_token),
                          headers=Depends(require_gateway_headers)):
    return LinkConfirmResponse(**confirm_link(body.patientId, body.txnId, body.otp))

@router.post("/notify")
def notify(body: LinkNotifyRequest):
    return notify_link(body.txnId, body.status)