"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "Skinopathy-AtopicDermatitis-Demov2"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://127.0.0.1:3000"
    ]

    # Database
    DATABASE_URL: str = "postgresql://skinopathy:demo_password@localhost:5433/skinopathy_ad"

    # Storage paths (one level up from backend directory)
    STORAGE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "storage")
    ML_MODELS_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "ml_models")

    # Image upload settings
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png"]

    # CNN Model settings
    CNN_MODEL_PATH: str = os.path.join(ML_MODELS_PATH, "efficientnet_b7_ad.h5") if ML_MODELS_PATH else "./ml_models/efficientnet_b7_ad.h5"
    CNN_INPUT_SIZE: tuple = (224, 224)
    CNN_CONFIDENCE_THRESHOLD: float = 0.7

    # VLM settings
    QWEN_MODEL_NAME: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    QWEN_MODEL_PATH: str = os.path.join(ML_MODELS_PATH, "qwen") if ML_MODELS_PATH else "./ml_models/qwen"
    USE_LOCAL_VLM: bool = True

    # OpenAI API (fallback)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-vision-preview"

    # GradCAM settings
    GRADCAM_LAYER_NAME: str = "top_conv"
    GRADCAM_ALPHA: float = 0.4

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
