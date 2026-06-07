"""
Konfigurasi aplikasi via environment variables.
Baca dari file .env secara otomatis (python-dotenv via pydantic-settings).
 
Contoh .env:
    DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bakery_db
    DEBUG=true
    DB_ECHO=false
"""
 
from functools import lru_cache
 
from pydantic_settings import BaseSettings, SettingsConfigDict
 
 
class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    # Wajib pakai driver asyncpg untuk async SQLAlchemy
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str
 
    # Log semua SQL query ke stdout (aktifkan saat debugging saja)
    DB_ECHO: bool = False
 
    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    DEBUG: bool = False
    APP_NAME: str = "Klangenan AI Microservice"
    API_PREFIX: str = "/api/v1"
 
    # ------------------------------------------------------------------
    # CORS — izinkan Next.js dev server
    # ------------------------------------------------------------------
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
 
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
 
 
@lru_cache
def get_settings() -> Settings:
    """
    Singleton settings — di-cache agar .env hanya dibaca sekali.
    Gunakan ini sebagai FastAPI dependency: settings = Depends(get_settings)
    """
    return Settings()
 
 
# Instance global untuk dipakai langsung (import dari modul lain)
settings = get_settings()