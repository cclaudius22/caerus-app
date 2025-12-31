from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database (Supabase PostgreSQL)
    DATABASE_URL: str = "postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres"

    # Firebase
    FIREBASE_PROJECT_ID: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: str = ""

    # Google Cloud Storage
    GCS_BUCKET_NAME: str = "caerus-pitch-videos"

    # Apple IAP
    APPLE_SHARED_SECRET: str = ""

    # JWT
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Environment
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
