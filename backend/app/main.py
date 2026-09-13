from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.db.init_db import init_db
from app.api.projects import router as projects_router
from app.api.health import router as health_router
from app.api.code_quality import router as code_quality_router
from app.api.similarity import router as similarity_router
from app.api.documentation import router as documentation_router

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
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(code_quality_router, prefix=settings.API_V1_STR)
app.include_router(similarity_router, prefix=settings.API_V1_STR)
app.include_router(documentation_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "2.4.0",
        "status": "healthy",
        "docs": "/docs"
    }


