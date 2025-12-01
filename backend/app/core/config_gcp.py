"""
GCP-specific configuration overrides
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class GCPSettings(BaseSettings):
    """Settings for GCP deployment"""

    # Project info
    PROJECT_NAME: str = "Skinopathy-AtopicDermatitis-Demov2"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

    # GCP Project
    GCP_PROJECT_ID: str = os.getenv("PROJECT_ID", "total-furnace-288818")
    GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")

    # CORS - allow Cloud Run domains
    ALLOWED_ORIGINS: List[str] = [
        "https://*.run.app",  # Cloud Run
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000"
    ]

    # Database - Cloud SQL via Unix socket or secret
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://skinopathy:password@/skinopathy_ad?host=/cloudsql/total-furnace-288818:us-central1:skinopathy-ad-db"
    )

    # Cloud Storage
    MODELS_BUCKET: str = os.getenv("MODELS_BUCKET", "total-furnace-288818-models")
    DATA_BUCKET: str = os.getenv("DATA_BUCKET", "total-furnace-288818-skinopathy-data")

    # Storage paths - using Cloud Storage
    USE_CLOUD_STORAGE: bool = True
    STORAGE_PATH: str = f"gs://{os.getenv('DATA_BUCKET', 'total-furnace-288818-skinopathy-data')}"
    ML_MODELS_PATH: str = f"gs://{os.getenv('MODELS_BUCKET', 'total-furnace-288818-models')}"

    # Local temp storage for processing
    LOCAL_TEMP_PATH: str = "/tmp/skinopathy"

    # Image upload settings
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png"]

    # CNN Model settings
    CNN_MODEL_PATH: str = f"gs://{os.getenv('MODELS_BUCKET', 'total-furnace-288818-models')}/efficientnet_b7_ad.h5"
    CNN_INPUT_SIZE: tuple = (224, 224)
    CNN_CONFIDENCE_THRESHOLD: float = 0.7

    # VLM settings
    QWEN_MODEL_NAME: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    QWEN_MODEL_PATH: str = f"gs://{os.getenv('MODELS_BUCKET', 'total-furnace-288818-models')}/qwen"
    USE_LOCAL_VLM: bool = False  # Use API-based for Cloud Run

    # OpenAI API (fallback for VLM)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4-vision-preview"

    # GradCAM settings
    GRADCAM_LAYER_NAME: str = "top_conv"
    GRADCAM_ALPHA: float = 0.4

    # Flare detection thresholds
    FLARE_SPIKE_THRESHOLD: float = 0.40
    PRE_FLARE_ITCH_INCREASE: float = 0.20
    PRE_FLARE_DRYNESS_INCREASE: float = 0.15

    # Redis (Memorystore)
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    USE_REDIS: bool = False  # Enable if using Memorystore

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-in-production-use-secret-manager")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Cloud Run specific
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "2"))

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
gcp_settings = GCPSettings()
