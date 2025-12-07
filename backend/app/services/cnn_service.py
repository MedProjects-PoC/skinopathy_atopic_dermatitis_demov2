"""
CNN Service for AD Assessment using EfficientNet-B7
Adapted from existing Skinopathy codebase
"""
import numpy as np
import cv2
from PIL import Image
from typing import Dict, Tuple
from loguru import logger
import os

from app.core.config import settings

# We'll implement this with a lightweight fallback for now
# and add full TensorFlow integration later
class CNNService:
    """EfficientNet-B7 based AD assessment service"""

    def __init__(self, model_path: str = None):
        """
        Initialize CNN service

        Args:
            model_path: Path to the EfficientNet-B7 .h5 model file (local or gs://)
        """
        # Use provided path, otherwise use settings (which auto-detects GCP vs local)
        self.model_path = model_path or settings.CNN_MODEL_PATH
        self.model = None
        # IMPORTANT: Model trained with 600x600 input - DO NOT CHANGE
        self.input_size = (600, 600)
        self.is_loaded = False

    def load_model(self):
        """Load the pre-trained EfficientNet-B7 model"""
        try:
            # Import TensorFlow only when needed
            import tensorflow as tf
            from tensorflow import keras

            logger.info(f"Loading CNN model from: {self.model_path}")

            # Handle Cloud Storage paths
            local_model_path = self.model_path
            if self.model_path.startswith("gs://"):
                local_model_path = self._download_model_from_gcs(self.model_path)

            if not os.path.exists(local_model_path):
                logger.warning(f"Model not found at {local_model_path}, using mock predictions")
                self.is_loaded = False
                return

            self.model = keras.models.load_model(local_model_path, compile=False)
            self.is_loaded = True
            logger.success("CNN model loaded successfully!")

        except ImportError as e:
            logger.warning(f"TensorFlow not available: {e}. Using mock predictions.")
            self.is_loaded = False
        except Exception as e:
            logger.error(f"Error loading CNN model: {e}")
            self.is_loaded = False

    def _download_model_from_gcs(self, gcs_path: str) -> str:
        """
        Download model from Google Cloud Storage to local temp directory

        Args:
            gcs_path: GCS path (e.g., gs://bucket/path/to/model.h5)

        Returns:
            Local path to downloaded model
        """
        try:
            from google.cloud import storage

            # Parse GCS path
            path_parts = gcs_path.replace("gs://", "").split("/", 1)
            bucket_name = path_parts[0]
            blob_path = path_parts[1]

            # Create local temp directory
            temp_dir = "/tmp/skinopathy/models"
            os.makedirs(temp_dir, exist_ok=True)

            # Local file path
            local_path = os.path.join(temp_dir, os.path.basename(blob_path))

            # Download if not already cached
            if not os.path.exists(local_path):
                logger.info(f"Downloading model from GCS: {gcs_path}")
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                blob.download_to_filename(local_path)
                logger.success(f"Model downloaded to: {local_path}")
            else:
                logger.info(f"Using cached model: {local_path}")

            return local_path

        except Exception as e:
            logger.error(f"Error downloading model from GCS: {e}")
            raise

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for EfficientNet-B7 input

        Args:
            image_path: Path to the input image

        Returns:
            Preprocessed image array
        """
        try:
            # Load image
            img = Image.open(image_path)
            img = img.convert('RGB')

            # Resize to model input size
            img = img.resize(self.input_size)

            # Convert to array and normalize
            img_array = np.array(img, dtype=np.float32)
            img_array = img_array / 255.0  # Normalize to [0, 1]

            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)

            logger.debug(f"Preprocessed image shape: {img_array.shape}")
            return img_array

        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise

    def analyze_image(self, image_path: str, questionnaire_data: Dict) -> Dict:
        """
        Analyze skin image for AD assessment

        Args:
            image_path: Path to the uploaded image
            questionnaire_data: Dictionary with questionnaire responses

        Returns:
            Dictionary with AD assessment metrics
        """
        try:
            # Load model if not already loaded
            if not self.is_loaded:
                self.load_model()

            # Preprocess image
            img_array = self.preprocess_image(image_path)

            if self.is_loaded and self.model is not None:
                # Real CNN inference
                predictions = self.model.predict(img_array, verbose=0)
                logger.info(f"CNN prediction shape: {predictions.shape}")

                # Extract metrics from CNN output
                results = self._extract_metrics_from_cnn(predictions, questionnaire_data)
            else:
                # Mock predictions for development
                logger.warning("Using mock CNN predictions (model not loaded)")
                results = self._generate_mock_predictions(questionnaire_data)

            logger.success(f"AD assessment complete: Severity={results['severity_score']:.1f}")
            return results

        except Exception as e:
            logger.error(f"Error during CNN analysis: {e}")
            raise

    def _extract_metrics_from_cnn(self, predictions: np.ndarray, questionnaire: Dict) -> Dict:
        """
        Extract AD metrics from CNN predictions

        This method adapts the existing EfficientNet-B7 output to AD-specific metrics
        """
        # The existing model outputs class probabilities for skin lesions
        # We'll adapt this to AD-specific scoring

        # Calculate base scores from CNN output
        cnn_severity = float(np.max(predictions[0])) * 100

        # Adjust severity based on questionnaire DDx factors
        severity_multiplier = 1.0

        # Increase severity if strong AD indicators present
        if questionnaire.get('itch_intensity', 0) >= 7:
            severity_multiplier += 0.2
        if questionnaire.get('nights_sleep_disturbed', 0) >= 5:
            severity_multiplier += 0.15
        if questionnaire.get('chronic_relapsing'):
            severity_multiplier += 0.1
        if questionnaire.get('atopic_triad_history'):
            severity_multiplier += 0.1
        if questionnaire.get('oozing_honey_crusts'):
            severity_multiplier += 0.15

        # Decrease severity if DDx suggests other conditions
        if questionnaire.get('thick_silvery_scales'):  # Psoriasis
            severity_multiplier -= 0.3
        if questionnaire.get('household_itchy_or_nighttime_worse'):  # Scabies
            severity_multiplier -= 0.4
        if questionnaire.get('new_exposure_trigger'):  # Contact dermatitis
            severity_multiplier -= 0.2

        severity_multiplier = max(0.3, min(severity_multiplier, 1.5))
        adjusted_severity = min(cnn_severity * severity_multiplier, 100.0)

        # Estimate other metrics
        inflammation_score = min(adjusted_severity * 0.9, 100.0)
        dryness_score = min(adjusted_severity * 0.85, 100.0)
        lichenification_score = min(adjusted_severity * 0.6, 100.0) if questionnaire.get('chronic_relapsing') else adjusted_severity * 0.3

        # Determine flare status
        if adjusted_severity < 30:
            flare_status = "stable"
        elif adjusted_severity < 50:
            flare_status = "mild_activity"
        elif adjusted_severity < 70:
            flare_status = "active"
        else:
            # Check for pre-flare indicators
            if questionnaire.get('itch_intensity', 0) > 6 and questionnaire.get('recent_stress_level', 0) > 6:
                flare_status = "pre_flare"
            else:
                flare_status = "active"

        # Body region analysis based on primary location
        primary_loc = questionnaire.get('primary_location', 'flexural')
        body_regions = {
            primary_loc: "severe" if adjusted_severity > 70 else "moderate" if adjusted_severity > 40 else "mild"
        }

        # Calculate affected area
        affected_area_pct = min(adjusted_severity * 0.25, 35.0)

        return {
            "severity_score": round(adjusted_severity, 1),
            "affected_area_pct": round(affected_area_pct, 1),
            "inflammation_score": round(inflammation_score, 1),
            "dryness_score": round(dryness_score, 1),
            "lichenification_score": round(lichenification_score, 1),
            "excoriation_detected": questionnaire.get('itch_intensity', 0) >= 7,
            "flare_status": flare_status,
            "body_regions": body_regions,
            "cnn_confidence": round(float(np.max(predictions[0])), 2)
        }

    def _generate_mock_predictions(self, questionnaire: Dict) -> Dict:
        """
        Generate mock predictions based on questionnaire data
        Used when TensorFlow model is not available
        """
        # Base severity from itch intensity
        base_severity = questionnaire.get('itch_intensity', 5) * 10

        # Adjust based on other factors
        if questionnaire.get('chronic_relapsing'):
            base_severity += 10
        if questionnaire.get('nights_sleep_disturbed', 0) >= 5:
            base_severity += 15
        if questionnaire.get('atopic_triad_history'):
            base_severity += 5
        if questionnaire.get('oozing_honey_crusts'):
            base_severity += 10

        # Cap at 100
        severity_score = min(base_severity, 100.0)

        # Determine flare status
        if severity_score < 30:
            flare_status = "stable"
        elif severity_score < 50:
            flare_status = "mild_activity"
        elif severity_score < 70:
            flare_status = "active"
        else:
            flare_status = "pre_flare" if questionnaire.get('recent_stress_level', 0) > 7 else "active"

        primary_loc = questionnaire.get('primary_location', 'flexural')

        return {
            "severity_score": round(severity_score, 1),
            "affected_area_pct": round(severity_score * 0.2, 1),
            "inflammation_score": round(severity_score * 0.9, 1),
            "dryness_score": round(severity_score * 0.85, 1),
            "lichenification_score": round(severity_score * 0.5, 1),
            "excoriation_detected": questionnaire.get('itch_intensity', 0) >= 7,
            "flare_status": flare_status,
            "body_regions": {
                primary_loc: "severe" if severity_score > 70 else "moderate" if severity_score > 40 else "mild"
            },
            "cnn_confidence": 0.75  # Mock confidence
        }


# Global instance
cnn_service = CNNService()
