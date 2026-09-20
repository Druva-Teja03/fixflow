import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    FixFlow Application Settings loaded from .env file or environment variables.
    All variables are switchable without changing code.
    """
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 12
    CORS_ORIGINS: str = "http://localhost:8000"

    # Database Configuration (MySQL / Amazon RDS)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "fixflow_user"
    DB_PASSWORD: str = "FixFlow@123"
    DB_NAME: str = "fixflow"

    # Storage Backend: "local" or "s3"
    STORAGE_BACKEND: str = "local"
    S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "ap-south-1"

    # AI Configuration (Amazon Bedrock / Rule-based Fallback)
    AI_ENABLED: bool = True
    BEDROCK_MODEL_ID: Optional[str] = None

    # Notifications Configuration (Amazon SES / SNS)
    NOTIFICATIONS_ENABLED: bool = False
    SES_SENDER_EMAIL: Optional[str] = None

    @property
    def database_url(self) -> str:
        """Construct the SQLAlchemy MySQL connection string with URL-encoded credentials."""
        from urllib.parse import quote_plus
        encoded_user = quote_plus(self.DB_USER)
        encoded_password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_password}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated origins into a clean list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Look for .env in the project root
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
