"""Application configuration settings using Pydantic Settings."""

from typing import Any, Dict, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://zuigo:zuigo_dev_2026@localhost:5432/zuigo_attendance"
    DATABASE_URL_SYNC: str = "postgresql://zuigo:zuigo_dev_2026@localhost:5432/zuigo_attendance"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    JWT_SECRET_KEY: str = "dev-jwt-secret-key-zuigo-attendance-2026-replace-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Dynamic QR Security
    QR_HMAC_SECRET: str = "dev-qr-hmac-secret-zuigo-attendance-2026-replace-in-prod"
    QR_CODE_TTL_SECONDS: int = 15
    QR_SKEW_TOLERANCE_SECONDS: int = 5

    # OTP Configuration
    OTP_GATEWAY_PROVIDER: str = "mock"
    OTP_GATEWAY_API_KEY: str = "mock-key"
    OTP_SENDER_ID: str = "ZUIGO"
    OTP_TTL_SECONDS: int = 300  # 5 minutes
    OTP_MAX_ATTEMPTS: int = 3

    # Field Visit Defaults
    DEFAULT_FIELD_DWELL_MINUTES: int = 30
    DEFAULT_FIELD_GEOFENCE_RADIUS_METERS: int = 75
    ODOMETER_DISCREPANCY_THRESHOLD_PCT: float = 15.0

    # Default Reimbursement Rates (INR per km)
    REIMBURSEMENT_RATES: Dict[str, Any] = {
        "COMPANY_CAR": 0.0,
        "PERSONAL_CAR": 8.00,
        "TWO_WHEELER": 4.00,
        "CAB": "ACTUAL",
        "PUBLIC_TRANSPORT": "ACTUAL",
        "WALKING": 0.0
    }


settings = Settings()
