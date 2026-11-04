from pathlib import Path
from typing import Any, List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ProjectLens API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8001

    # CORS configuration
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    # Database configuration
    # Default to PostgreSQL, with support for SQLite for easy fallback/testing
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/projectlens_db"

    # Uploads and storage configuration
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Extraction security limits
    EXTRACTED_DIR: str = "./uploads/extracted"
    MAX_EXTRACTED_FILES: int = 2000
    MAX_EXTRACTED_SIZE_MB: int = 150
    MAX_SINGLE_FILE_SIZE_MB: int = 50

    # Phase 4 Similarity Configuration
    SIMILARITY_ENABLE_SEMANTIC: bool = False
    SIMILARITY_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SIMILARITY_MODEL_PATH: str = ""
    SIMILARITY_WEIGHT_TOKEN: float = 0.30
    SIMILARITY_WEIGHT_STRUCTURE: float = 0.40
    SIMILARITY_WEIGHT_SEMANTIC: float = 0.30

    # Phase 7A LLM Configuration (OpenRouter via OpenAI-compatible SDK)
    LLM_ENABLED: bool = False
    LLM_PROVIDER: str = "openrouter"
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "google/gemma-4-26b-a4b-it:free"
    LLM_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_INPUT_CHARS: int = 18000
    LLM_MAX_OUTPUT_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.2

    @property
    def api_key(self) -> Optional[str]:
        """Return configured API key, preferring OPENROUTER_API_KEY then LLM_API_KEY."""
        if self.OPENROUTER_API_KEY and self.OPENROUTER_API_KEY.strip():
            return self.OPENROUTER_API_KEY.strip()
        if self.LLM_API_KEY and self.LLM_API_KEY.strip():
            return self.LLM_API_KEY.strip()
        return None

    @property
    def llm_configured(self) -> bool:
        """Return True when LLM is enabled and a non-empty API key is configured."""
        if not self.LLM_ENABLED:
            return False
        return bool(self.api_key)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def assemble_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes", "debug", "dev", "development")
        return bool(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json
            return json.loads(v)
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def max_extracted_size_bytes(self) -> int:
        return self.MAX_EXTRACTED_SIZE_MB * 1024 * 1024

    @property
    def max_single_file_size_bytes(self) -> int:
        return self.MAX_SINGLE_FILE_SIZE_MB * 1024 * 1024

    @property
    def resolved_upload_dir(self) -> Path:
        path = Path(self.UPLOAD_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_extracted_dir(self) -> Path:
        path = Path(self.EXTRACTED_DIR).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    model_config = SettingsConfigDict(
        env_file=(str(Path(__file__).resolve().parent.parent / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
