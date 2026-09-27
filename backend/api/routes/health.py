from fastapi import APIRouter
from backend.config import settings

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "demo_mode": settings.DEMO_MODE,
        "uptime_seconds": 3600 # Static for now, could be dynamic
    }
