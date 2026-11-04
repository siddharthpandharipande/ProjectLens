from fastapi import APIRouter, status
from app.database import check_db_connection
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
@router.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Return backend health and database connectivity status.
    Serves both /health and /api/health for full compatibility.
    """
    db_ok = check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected" if db_ok else "disconnected",
        "environment": settings.ENVIRONMENT,
    }
