from fastapi import Header, HTTPException, status

def require_gateway_headers(
        request_id: str | None = Header(default=None, convert_underscores=False, alias="REQUEST-ID"),
        timestamp: str | None = Header(default=None, convert_underscores=False, alias="TIMESTAMP"),
        cm_id: str | None = Header(default=None, convert_underscores=False, alias="X-CM-ID"),
) -> dict[str, str]:
    
    missing = [name for name, value in {
        "REQUEST-ID": request_id,
        "TIMESTAMP": timestamp,
        "X-CM-ID": cm_id
    }.items() if not value]

    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required headers: {', '.join(missing)}",
        )
    
    return {"request_id": request_id, "timestamp": timestamp, "cm_id": cm_id}
