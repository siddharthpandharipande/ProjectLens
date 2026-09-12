from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.db.init_db import init_db
from app.api.projects import router as projects_router

# Initialize database tables on startup
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Academic project evaluation platform static analysis engine",
    version="2.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(projects_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "2.4.0",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "ProjectLens API Engine"}
