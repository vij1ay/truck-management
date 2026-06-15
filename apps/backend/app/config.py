import pytz
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/transport_db"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production-min-256-bits"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Security
    BCRYPT_COST_FACTOR: int = 12
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # SuperAdmin Seeder
    SUPERADMIN_EMAIL: str = "admin@system.local"
    SUPERADMIN_PASSWORD: str | None = "admin123"
    SUPERADMIN_FIRST_NAME: str = "Super"
    SUPERADMIN_LAST_NAME: str = "Admin"
    
    # Application
    APP_NAME: str = "Transport Management System"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    LOG_FILE: str = "app.log"
    LOG_MAX_SIZE_MB: int = 20
    LOG_BACKUP_COUNT: int = 100

    # Timezone — used to format displayed timestamps for users without an explicit
    # `timezone` set on their profile (see app/core/timezone_context.py).
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # Profile picture / logo uploads — stored on local disk, served via authenticated
    # GET /{resource}/{id}/avatar endpoints (see app/core/avatar_storage.py).
    UPLOAD_DIR: str = "uploads"
    MAX_AVATAR_SIZE_MB: int = 5

    @field_validator("DEFAULT_TIMEZONE")
    @classmethod
    def validate_default_timezone(cls, v: str) -> str:
        if v not in pytz.all_timezones_set:
            raise ValueError(f"Invalid timezone: {v}")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
