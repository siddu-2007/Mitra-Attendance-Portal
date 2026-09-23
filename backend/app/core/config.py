"""Application Configuration Module using Pydantic Settings."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration parameters loaded from environment and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General App Configuration
    ENVIRONMENT: str = Field(default="development", description="Application runtime environment")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=False, description="Debug mode")
    APP_NAME: str = Field(default="VIT Mithra Attendance Portal", description="Service application name")
    API_V1_PREFIX: str = Field(default="/api", description="Base prefix for v1 API routes")

    # Firebase Service Account Credentials
    FIREBASE_PROJECT_ID: Optional[str] = Field(default=None, description="Google Cloud / Firebase Project ID")
    FIREBASE_CLIENT_EMAIL: Optional[str] = Field(default=None, description="Firebase service account email")
    FIREBASE_PRIVATE_KEY: Optional[str] = Field(default=None, description="Firebase service account private key")
    FIREBASE_STORAGE_BUCKET: Optional[str] = Field(default=None, description="Firebase storage bucket name")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(
        default=None, description="Optional path to local serviceAccountKey.json"
    )

    # API Key for Service-to-Service and Administrative Operations
    API_KEY: Optional[str] = Field(
        default=None, description="Backend secret API key for protected service-to-service calls"
    )

    # CORS Configuration
    FRONTEND_URL: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Allowed frontend origin URLs, separated by comma",
    )

    # Rate Limiting
    RATE_LIMIT_LOGIN: str = Field(default="10/minute", description="Rate limit for login/auth verification")
    RATE_LIMIT_BULK: str = Field(default="30/minute", description="Rate limit for bulk attendance submission")
    RATE_LIMIT_REPORTS: str = Field(default="15/minute", description="Rate limit for report generation")

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated FRONTEND_URL string into a clean list of origins."""
        if not self.FRONTEND_URL:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in self.FRONTEND_URL.split(",") if origin.strip()]

    @property
    def clean_private_key(self) -> Optional[str]:
        """Normalize private key line breaks if passed via environment string."""
        if not self.FIREBASE_PRIVATE_KEY:
            return None
        key = self.FIREBASE_PRIVATE_KEY.strip()
        # Handle cases where quotes or escaped \n strings are present
        if key.startswith('"') and key.endswith('"'):
            key = key[1:-1]
        return key.replace("\\n", "\n")


settings = Settings()
