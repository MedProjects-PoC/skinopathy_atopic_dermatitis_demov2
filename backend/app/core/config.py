"""
Application configuration - Auto-detects local vs GCP environment
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "Skinopathy-AtopicDermatitis-Demov2"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Auto-detect environment (K_SERVICE is set by Cloud Run)
    IS_GCP: bool = os.getenv("K_SERVICE") is not None or os.getenv("ENVIRONMENT") == "production"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production" if (os.getenv("K_SERVICE") is not None or os.getenv("ENVIRONMENT") == "production") else "development")

    # CORS - allow Cloud Run domains in GCP
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        if self.IS_GCP:
            return [
                # New frontend service will be: skinopathy-atopic-dermatitis-demo2-web-<hash>.run.app
                # Using ALLOWED_ORIGIN_REGEX below to match all *.run.app domains
                "http://localhost",
                "http://localhost:3000",
            ]
        return [
            "http://localhost",
            "http://localhost:80",
            "http://localhost:3000",
            "http://127.0.0.1",
            "http://127.0.0.1:80",
            "http://127.0.0.1:3000"
        ]

    # CORS regex for Cloud Run domains (all *.run.app subdomains)
    @property
    def ALLOWED_ORIGIN_REGEX(self) -> str:
        if self.IS_GCP:
            return r"https://.*\.run\.app"
        return None

    # Database - Cloud SQL in GCP (from Secret Manager), localhost otherwise
    @property
    def DATABASE_URL(self) -> str:
        if self.IS_GCP:
            # DATABASE_URL injected from Secret Manager in Cloud Run
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise RuntimeError("DATABASE_URL environment variable not set in GCP environment")
            return db_url
        return "postgresql://skinopathy:demo_password@localhost:5433/skinopathy_ad"

    # Storage paths
    @property
    def STORAGE_PATH(self) -> str:
        if self.IS_GCP:
            # Use local temp directory for GCP (Cloud Storage handled separately)
            return "/tmp/storage"
        # Local development: one level up from backend directory
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "storage")

    @property
    def ML_MODELS_PATH(self) -> str:
        if self.IS_GCP:
            return "/tmp/ml_models"
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "ml_models")

    # Image upload settings
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png"]

    # CNN Model settings
    @property
    def CNN_MODEL_PATH(self) -> str:
        if self.IS_GCP:
            # Use GCS path in production
            return f"gs://{self.GCS_BUCKET_NAME}/efficientnet_b7_ad.h5"
        return os.path.join(self.ML_MODELS_PATH, "efficientnet_b7_ad.h5")

    CNN_INPUT_SIZE: tuple = (600, 600)  # Fixed size from cnn_service.py
    CNN_CONFIDENCE_THRESHOLD: float = 0.7

    # VLM settings
    QWEN_MODEL_NAME: str = "Qwen/Qwen2.5-VL-7B-Instruct"

    @property
    def QWEN_MODEL_PATH(self) -> str:
        return os.path.join(self.ML_MODELS_PATH, "qwen")

    USE_LOCAL_VLM: bool = True

    # OpenAI API (fallback)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-vision-preview"

    # Activation Map settings
    ACTIVATION_MAP_LAYER_NAME: str = "top_conv"
    ACTIVATION_MAP_ALPHA: float = 0.4

    # Cloud Storage settings for saliency maps
    GCS_BUCKET_NAME: str = "total-furnace-288818-models"
    GCS_SALIENCY_MAPS_PREFIX: str = "saliency_maps/"

    @property
    def USE_CLOUD_STORAGE(self) -> bool:
        """Use Cloud Storage for saliency maps in GCP, local storage otherwise"""
        return self.IS_GCP

    # Flare detection thresholds
    FLARE_SPIKE_THRESHOLD: float = 0.40
    PRE_FLARE_ITCH_INCREASE: float = 0.20
    PRE_FLARE_DRYNESS_INCREASE: float = 0.15

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
