"""
Activation Channel Segmentation Service

Extracts learned feature channels from CNN and uses them to segment and highlight
rash regions. This provides sharper, more interpretable segmentation than Grad-CAM.

Saves all intermediate data (activation channels, overlays, etc.) tied to session ID.
"""

import numpy as np
import cv2
from typing import List, Tuple, Dict, Optional
from loguru import logger
from PIL import Image
import tensorflow as tf
from io import BytesIO
import os


class ActivationChannelService:
    """
    Extracts and visualizes specific activation channels from EfficientNet-B7
    to segment dermatitis-affected regions.

    Saves all data to Cloud Storage with session ID for traceability.
    """

    # Verdigris/Teal colormap (custom)
    VERDIGRIS_CMAP = {
        0.0: np.array([0, 0, 0]),           # Black (no activation)
        0.2: np.array([100, 180, 160]),     # Light teal
        0.4: np.array([67, 169, 140]),      # Medium verdigris (#43A98C)
        0.6: np.array([45, 140, 120]),      # Verdigris
        0.8: np.array([30, 110, 100]),      # Dark verdigris
        1.0: np.array([20, 80, 80]),        # Deep verdigris
    }

    # Best rash-detecting channels (empirically determined from 123 AD images)
    # Scoring: 70% texture correlation (cv2.Canny edges) + 30% redness (R>G AND R>B)
    # Analysis date: 2025-12-10
    DEFAULT_RASH_CHANNELS = [60, 84, 40, 74, 85]

    def __init__(self, cnn_model=None, storage_service=None):
        """
        Initialize activation channel service

        Args:
            cnn_model: Loaded EfficientNet-B7 Keras model
            storage_service: Cloud storage service for saving files
        """
        self.model = cnn_model
        self.storage_service = storage_service
        self.rash_channels = self.DEFAULT_RASH_CHANNELS
        self.input_size = (600, 600)
        self.feature_map_size = (19, 19)
        self.activation_model = None

    def set_rash_channels(self, channel_indices: List[int]):
        """
        Set the channels to use for rash segmentation

        Args:
            channel_indices: List of channel indices (e.g., [57, 62, 45])
        """
        self.rash_channels = channel_indices
        logger.info(f"Rash detection channels set to: {channel_indices}")

    def _get_activation_model(self, layer_name='top_conv'):
        """
        Create a model that outputs intermediate activations

        Args:
            layer_name: Name of the convolutional layer to extract

        Returns:
            Keras model that outputs activations
        """
        if self.activation_model is not None:
            return self.activation_model

        if self.model is None:
            logger.error("CNN model not loaded")
            raise ValueError("CNN model not available")

        try:
            activation_layer = self.model.get_layer(layer_name)
            logger.info(f"Creating activation model for layer: {layer_name}")
            logger.debug(f"Activation layer output shape: {activation_layer.output_shape}")

            self.activation_model = tf.keras.Model(
                inputs=self.model.input,
                outputs=activation_layer.output
            )
            return self.activation_model

        except Exception as e:
            logger.error(f"Error creating activation model: {e}")
            raise

    def extract_channel_map(
        self,
        image_array: np.ndarray,
        channel_idx: int,
        layer_name='top_conv'
    ) -> np.ndarray:
        """
        Extract a single activation channel and upscale to original image size

        Args:
            image_array: Preprocessed image array (1, 600, 600, 3)
            channel_idx: Index of channel to extract (0-2559)
            layer_name: Name of convolutional layer

        Returns:
            Upscaled channel activation map (600, 600)
        """
        try:
            activation_model = self._get_activation_model(layer_name)
            activations = activation_model.predict(image_array, verbose=0)

            # Extract specific channel (shape: 19x19)
            channel_map = activations[0, :, :, channel_idx]

            # Normalize to 0-1
            channel_min = np.min(channel_map)
            channel_max = np.max(channel_map)
            if channel_max > channel_min:
                channel_map = (channel_map - channel_min) / (channel_max - channel_min)
            else:
                channel_map = np.zeros_like(channel_map)

            # Upscale to original image size
            upscaled = cv2.resize(
                channel_map,
                self.input_size,
                interpolation=cv2.INTER_CUBIC
            )

            logger.debug(f"Extracted channel {channel_idx}: min={np.min(upscaled):.3f}, max={np.max(upscaled):.3f}")
            return upscaled

        except Exception as e:
            logger.error(f"Error extracting channel map: {e}")
            raise

    def create_rash_segmentation(
        self,
        image_array: np.ndarray,
        layer_name='top_conv'
    ) -> np.ndarray:
        """
        Create segmentation map from rash-detecting channels

        Args:
            image_array: Preprocessed image array (1, 600, 600, 3)
            layer_name: Name of convolutional layer

        Returns:
            Segmentation map (600, 600), values 0-1
        """
        try:
            if not self.rash_channels:
                logger.warning("No rash channels configured, using default [57]")
                self.rash_channels = [57]

            logger.info(f"Creating segmentation from channels: {self.rash_channels}")

            channel_maps = []
            for channel_idx in self.rash_channels:
                try:
                    channel_map = self.extract_channel_map(image_array, channel_idx, layer_name)
                    channel_maps.append(channel_map)
                except Exception as e:
                    logger.warning(f"Error extracting channel {channel_idx}: {e}")
                    continue

            if not channel_maps:
                logger.error("No channels extracted successfully")
                return np.zeros(self.input_size)

            # Combine channels (average for robustness)
            if len(channel_maps) == 1:
                combined = channel_maps[0]
            else:
                combined = np.mean(channel_maps, axis=0)

            # Normalize to 0-1
            combined = (combined - np.min(combined)) / (np.max(combined) - np.min(combined) + 1e-8)

            logger.success(f"Segmentation created: shape={combined.shape}, range=[{np.min(combined):.3f}, {np.max(combined):.3f}]")
            return combined

        except Exception as e:
            logger.error(f"Error creating segmentation: {e}")
            raise

    def apply_verdigris_colormap(
        self,
        segmentation_map: np.ndarray,
        alpha: float = 0.4
    ) -> np.ndarray:
        """
        Apply custom verdigris colormap to segmentation

        Args:
            segmentation_map: Normalized segmentation (0-1)
            alpha: Opacity for overlay (0-1)

        Returns:
            RGB image with verdigris coloring (600, 600, 3)
        """
        try:
            if len(segmentation_map.shape) != 2:
                segmentation_map = segmentation_map[:, :, 0]

            h, w = segmentation_map.shape
            colored = np.zeros((h, w, 3), dtype=np.uint8)

            # Apply colormap with interpolation
            for i in range(h):
                for j in range(w):
                    intensity = segmentation_map[i, j]

                    if intensity < 0.2:
                        color = self.VERDIGRIS_CMAP[0.0] * (intensity / 0.2)
                    elif intensity < 0.4:
                        t = (intensity - 0.2) / 0.2
                        color = (1 - t) * self.VERDIGRIS_CMAP[0.2] + t * self.VERDIGRIS_CMAP[0.4]
                    elif intensity < 0.6:
                        t = (intensity - 0.4) / 0.2
                        color = (1 - t) * self.VERDIGRIS_CMAP[0.4] + t * self.VERDIGRIS_CMAP[0.6]
                    elif intensity < 0.8:
                        t = (intensity - 0.6) / 0.2
                        color = (1 - t) * self.VERDIGRIS_CMAP[0.6] + t * self.VERDIGRIS_CMAP[0.8]
                    else:
                        t = (intensity - 0.8) / 0.2
                        color = (1 - t) * self.VERDIGRIS_CMAP[0.8] + t * self.VERDIGRIS_CMAP[1.0]

                    colored[i, j] = np.uint8(color)

            colored = cv2.cvtColor(colored, cv2.COLOR_RGB2BGR)
            logger.debug(f"Applied verdigris colormap")
            return colored

        except Exception as e:
            logger.error(f"Error applying colormap: {e}")
            raise

    def create_overlay(
        self,
        original_image_path: str,
        segmentation_map: np.ndarray,
        alpha: float = 0.4,
        add_boundaries: bool = True
    ) -> np.ndarray:
        """
        Create overlay image combining original and segmentation

        Args:
            original_image_path: Path to original image
            segmentation_map: Segmentation map (0-1)
            alpha: Opacity for overlay
            add_boundaries: Whether to add boundary outlines

        Returns:
            RGB image with overlay
        """
        try:
            original = Image.open(original_image_path).convert('RGB')
            original = original.resize(self.input_size)
            original_cv = cv2.cvtColor(np.array(original), cv2.COLOR_RGB2BGR)

            colored = self.apply_verdigris_colormap(segmentation_map, alpha)

            result = cv2.addWeighted(
                original_cv,
                1.0 - alpha,
                colored,
                alpha,
                0
            )

            if add_boundaries:
                result = self._add_boundaries(result, segmentation_map)

            logger.success("Overlay created successfully")
            return result

        except Exception as e:
            logger.error(f"Error creating overlay: {e}")
            raise

    def _add_boundaries(
        self,
        image: np.ndarray,
        segmentation_map: np.ndarray,
        threshold: float = 0.4
    ) -> np.ndarray:
        """
        Add boundary contours to image

        Args:
            image: Image to add boundaries to
            segmentation_map: Segmentation map
            threshold: Threshold for binary mask

        Returns:
            Image with boundaries drawn
        """
        try:
            binary_mask = (segmentation_map > threshold).astype(np.uint8) * 255

            contours, _ = cv2.findContours(
                binary_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            verdigris_bgr = (80, 110, 100)
            cv2.drawContours(
                image,
                contours,
                -1,
                verdigris_bgr,
                thickness=2
            )

            logger.debug(f"Added {len(contours)} boundary contours")
            return image

        except Exception as e:
            logger.error(f"Error adding boundaries: {e}")
            return image

    def save_segmentation_maps(
        self,
        session_id: str,
        original_image_path: str,
        segmentation_map: np.ndarray,
        overlay_image: np.ndarray,
        channel_data: Dict[str, np.ndarray]
    ) -> Dict[str, str]:
        """
        Save all activation channel data tied to session ID

        Args:
            session_id: Session identifier
            original_image_path: Path to original image
            segmentation_map: Raw segmentation (0-1)
            overlay_image: Final overlay image (BGR)
            channel_data: Dict of individual channel maps {channel_id: map_array}

        Returns:
            Dict with paths/URLs to all saved files
        """
        try:
            saved_files = {}

            # 1. Save segmentation map (numpy)
            segmentation_path = f"activation_channels/{session_id}/segmentation.npy"
            if self.storage_service:
                self.storage_service.upload_array(
                    segmentation_map,
                    segmentation_path
                )
            saved_files['segmentation_npy'] = segmentation_path

            # 2. Save overlay image (PNG)
            overlay_path = f"activation_channels/{session_id}/overlay.png"
            overlay_pil = Image.fromarray(
                cv2.cvtColor(overlay_image, cv2.COLOR_BGR2RGB)
            )
            if self.storage_service:
                buffer = BytesIO()
                overlay_pil.save(buffer, format='PNG', quality=95)
                buffer.seek(0)
                self.storage_service.upload_bytes(buffer, overlay_path)
            saved_files['overlay_image'] = overlay_path

            # 3. Save individual channel maps
            for channel_id, channel_map in channel_data.items():
                channel_path = f"activation_channels/{session_id}/channel_{channel_id}.npy"
                if self.storage_service:
                    self.storage_service.upload_array(channel_map, channel_path)
                saved_files[f'channel_{channel_id}'] = channel_path

            # 4. Save metadata (channels used, alpha, etc.)
            metadata = {
                'session_id': str(session_id),
                'rash_channels': self.rash_channels,
                'overlay_alpha': 0.4,
                'add_boundaries': True,
                'colormap': 'verdigris'
            }
            metadata_path = f"activation_channels/{session_id}/metadata.json"
            if self.storage_service:
                import json
                self.storage_service.upload_text(
                    json.dumps(metadata, indent=2),
                    metadata_path
                )
            saved_files['metadata'] = metadata_path

            logger.success(f"All activation channel data saved for session {session_id}")
            logger.info(f"Saved files: {saved_files}")

            return saved_files

        except Exception as e:
            logger.error(f"Error saving segmentation maps: {e}")
            raise

    def overlay_to_bytes(self, overlay_image: np.ndarray) -> BytesIO:
        """
        Convert overlay image to bytes

        Args:
            overlay_image: OpenCV image (BGR)

        Returns:
            BytesIO object with PNG data
        """
        try:
            rgb_image = cv2.cvtColor(overlay_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)

            buffer = BytesIO()
            pil_image.save(buffer, format='PNG', quality=95)
            buffer.seek(0)

            logger.debug(f"Converted overlay to PNG ({buffer.getbuffer().nbytes} bytes)")
            return buffer

        except Exception as e:
            logger.error(f"Error converting overlay to bytes: {e}")
            raise


# Global instance
activation_channel_service = ActivationChannelService()
