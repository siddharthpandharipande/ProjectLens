from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api.health import router as health_router
from app.api.projects import router as projects_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure upload directory and database tables exist
    settings.resolved_upload_dir
    try:
        init_db()
    except Exception as e:
        print(f"[Warning] Could not initialize database on startup: {e}")
    yield
    # Shutdown logic (if any)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI backend for ProjectLens faculty evaluation suite.",
    lifespan=lifespan,
)

# CORS configuration for frontend
allow_origin_regex = (
    r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$"
    if settings.ENVIRONMENT == "development"
    else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )

# Register routes
app.include_router(health_router)
app.include_router(projects_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "ProjectLens Backend API is running.",
        "documentation": "/docs",
        "health": "/api/health",
        "version": settings.VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
