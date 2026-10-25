import os
from functools import lru_cache
from typing import List, Union

def _load_env_file(filepath: str = ".env"):
    if not os.path.exists(filepath):
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(filepath)
    except ImportError:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k not in os.environ:
                    os.environ[k] = v

_load_env_file()

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"
        )

        # Database Configuration
        DATABASE_URL: str = Field(
            default="postgresql+psycopg2://postgres:pwd@localhost:5432/postgres",
            description="SQLAlchemy database connection string"
        )
        DB_URI: str = Field(
            default="postgresql://postgres:pwd@localhost:5432/langgraph",
            description="PostgreSQL URI for LangGraph checkpointer"
        )

        # Authentication & Security
        SECRET_KEY: str = Field(
            default="SUPER_SECRET_KEY_CHANGE_IN_PRODUCTION",
            description="JWT signing secret key"
        )
        ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
        ACCESS_TOKEN_EXPIRE_HOURS: int = Field(default=2, description="JWT expiration in hours")

        # LLM & AI Providers
        GOOGLE_API_KEY: str = Field(default="", description="Google Gemini API key")
        GROQ_API_KEY: str = Field(default="", description="Groq API key")
        OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")
        QDRANT_CLIENT_URL: str = Field(default="http://localhost:6333", description="Qdrant vector DB URL")

        # LangSmith Tracing
        LANGSMITH_TRACING: bool = Field(default=False)
        LANGSMITH_ENDPOINT: str = Field(default="https://api.smith.langchain.com")
        LANGSMITH_API_KEY: str = Field(default="")
        LANGSMITH_PROJECT: str = Field(default="agentic-ticket-resolution")

        # Application / Network
        API_URL: str = Field(default="http://127.0.0.1:8001", description="Backend API base URL")
        CORS_ORIGINS: List[str] = Field(
            default=[
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:8501",
                "http://127.0.0.1:8501",
            ],
            description="Allowed CORS origins"
        )
        LANGGRAPH_API: bool = Field(default=False, description="Whether running in LangGraph Cloud API")

        @field_validator("CORS_ORIGINS", mode="before")
        @classmethod
        def parse_cors_origins(cls, v):
            if isinstance(v, str):
                if v.startswith("[") and v.endswith("]"):
                    try:
                        import json
                        return json.loads(v)
                    except Exception:
                        pass
                return [s.strip() for s in v.split(",") if s.strip()]
            return v

except ImportError:
    # Graceful fallback when pydantic-settings is not installed in the active environment
    class Settings:  # type: ignore
        def __init__(self):
            self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:pwd@localhost:5432/postgres")
            self.DB_URI = os.getenv("DB_URI", "postgresql://postgres:pwd@localhost:5432/langgraph")
            self.SECRET_KEY = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY_CHANGE_IN_PRODUCTION").strip('"')
            self.ALGORITHM = os.getenv("ALGORITHM", "HS256").strip('"')
            self.ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "2"))

            self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
            self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
            self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
            self.QDRANT_CLIENT_URL = os.getenv("QDRANT_CLIENT_URL", "http://localhost:6333")

            self.LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
            self.LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
            self.LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
            self.LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "agentic-ticket-resolution").strip('"')

            self.API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")
            raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501")
            self.CORS_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
            self.LANGGRAPH_API = os.getenv("LANGGRAPH_API", "false").lower() == "true"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
