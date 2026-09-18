from fastapi import APIRouter, Response, status

from app.core.database import check_db_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    return {"status": "ok", "service": "MedRoute AI API"}


@router.get("/health/live")
async def liveness():
    """Liveness: process is up. Does not touch the DB."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(response: Response):
    """Readiness: process is up AND can reach the database."""
    db_ok = await check_db_connection()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "database": "unreachable"}
    return {"status": "ready", "database": "connected"}
