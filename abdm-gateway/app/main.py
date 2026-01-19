from fastapi import FastAPI 
from loguru import logger 

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.api.routes import api_router

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="ABDM Gateway",
    description="API Gateway for ABDM services",
    version="0.1.0"
)

app.include_router(api_router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "abdm-gateway"}

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting ADBM Gateway on {settings.app_host}:{settings.app_port}")
    logger.info(f"Envirnment: {settings.app_env}")

@app.on_event("shutdown")
async def stutdown_event():
    logger.info("Setting down ABDM Gateway")

@app.get("/hello")
async def hello():
    return {"message": "Hello, ABDM Gateway!"}
