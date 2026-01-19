from app.core.config import get_settings
from app.core.security import create_access_token

settings = get_settings()

def validate_client_credentials(client_id: str, client_secret: str) -> bool:
    # Simplified validation - replace with real DB lookup in production
    # For now, accept any non-empty credentials
    return bool(client_id and client_secret)

def issue_access_token(client_id: str, cm_id: str) -> str:
    token = create_access_token({"clientId": client_id, "cmId": cm_id})
    return {
        "accessToken": token,
        "expiresIn": settings.jwt_expiry_seconds,
        "tokenType": "Bearer"
    }