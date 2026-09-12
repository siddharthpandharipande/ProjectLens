import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ProjectLens"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = "sqlite:///./projectlens.db"
    
    # Secret Key & Security
    SECRET_KEY: str = "dev-secret-key-projectlens-academic-eval"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]
    
    # File Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    TEMP_DIR: Path = STORAGE_DIR / "tmp"
    
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure storage directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)
