"""
LegalMind Configuration Settings
Google Cloud / Vertex AI Configuration
"""

import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # -------------------------------------------------------------------------
    # Vertex AI Configuration
    # -------------------------------------------------------------------------
    gemini_model: str = "gemini-2.0-flash"
    
    # -------------------------------------------------------------------------
    # Google Cloud Project Configuration
    # -------------------------------------------------------------------------
    google_cloud_project: str = ""
    google_application_credentials: Optional[str] = None
    
    # -------------------------------------------------------------------------
    # Firestore Configuration
    # -------------------------------------------------------------------------
    firestore_database: str = "(default)"
    
    # -------------------------------------------------------------------------
    # Cloud Storage Configuration
    # -------------------------------------------------------------------------
    gcs_bucket_name: str = "legalmind-contracts"
    gcs_contracts_folder: str = "contracts"
    gcs_documents_folder: str = "generated-documents"
    
    # -------------------------------------------------------------------------
    # Application Settings
    # -------------------------------------------------------------------------
    app_name: str = "LegalMind"
    app_env: str = "development"
    debug: bool = True

    # Security Settings
    api_secret_key: str = ""
    allowed_origins: str = ""
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Session Configuration
    session_timeout_minutes: int = 60
    max_tokens_per_request: int = 8192
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 30

    # Caching
    response_cache_ttl_seconds: int = 60
    
    # -------------------------------------------------------------------------
    # Feature Flags
    # -------------------------------------------------------------------------
    enable_search_grounding: bool = True
    enable_thinking_logs: bool = True
    enable_citations: bool = True

    @field_validator("google_cloud_project", mode="after")
    @classmethod
    def validate_project(cls, v):
        """Validate Google Cloud project is configured."""
        if not v:
            raise ValueError(
                "Missing required environment variable: GOOGLE_CLOUD_PROJECT. "
                "Please set it in your .env.local file."
            )
        return v
    
    model_config = {
        "env_file": str(Path(__file__).parent.parent / ".env.local"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
        "validate_assignment": True,
    }



@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()


def get_google_cloud_project() -> str:
    """Get the Google Cloud project ID.
    
    Returns:
        str: The Google Cloud project ID
        
    Raises:
        ValueError: If the project ID is not configured
    """
    settings = get_settings()
    return settings.google_cloud_project


def get_gcs_bucket_name() -> str:
    """Get the Google Cloud Storage bucket name.
    
    Returns:
        str: The GCS bucket name
    """
    return get_settings().gcs_bucket_name


def validate_settings() -> bool:
    """Validate that all required settings are configured.
    
    Returns:
        bool: True if all settings are valid
        
    Raises:
        ValueError: If any required settings are missing
    """
    settings = get_settings()
    
    # GOOGLE_CLOUD_PROJECT is always required
    if not settings.google_cloud_project:
        raise ValueError(
            "Missing required environment variable: GOOGLE_CLOUD_PROJECT. "
            "Please check your .env file."
        )
    
    return True