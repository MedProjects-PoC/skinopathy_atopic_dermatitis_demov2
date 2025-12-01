"""
GradCAM Service for Saliency Map Generation
Adapted from existing Skinopathy pytorch-gradcam implementation
"""
import numpy as np
import cv2
from PIL import Image
from typing import Optional
from loguru import logger
import os


class GradCAMService:
    """Generate saliency maps using GradCAM technique"""

    def __init__(self, alpha: float = 0.4):
        """
        Initialize GradCAM service

        Args:
            alpha: Transparency for heatmap overlay (0.0 to 1.0)
        """
        self.alpha = alpha
        self.is_available = False

    def generate_saliency_map(
        self,
        image_path: str,
        output_path: str,
        layer_name: str = 'top_conv'
    ) -> Optional[str]:
        """
        Generate saliency map using GradCAM

        Args:
            image_path: Path to input image
            output_path: Path to save saliency map
            layer_name: Target layer for GradCAM

        Returns:
            Path to saved saliency map, or None if generation failed
        """
        try:
            # For now, create a mock saliency map
            # Will integrate full GradCAM implementation later
            logger.info(f"Generating saliency map for: {image_path}")

            # Load original image
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Could not load image: {image_path}")
                return None

            # Create mock heatmap (random activation for demo)
            # In production, this will use actual GradCAM on the CNN
            h, w = img.shape[:2]
            heatmap = self._create_mock_heatmap(w, h)

            # Apply colormap
            heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

            # Overlay on original image
            overlayed = cv2.addWeighted(img, 1 - self.alpha, heatmap_colored, self.alpha, 0)

            # Save result
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cv2.imwrite(output_path, overlayed)

            logger.success(f"Saliency map saved to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating saliency map: {e}")
            return None

    def _create_mock_heatmap(self, width: int, height: int) -> np.ndarray:
        """
        Create a mock heatmap for demonstration
        In production, this will be replaced with actual GradCAM output
        """
        # Create a heatmap with central hotspot (simulating lesion attention)
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)

        # Gaussian-like activation pattern
        center_x, center_y = 0.2, 0.1  # Slightly off-center
        sigma = 0.5
        heatmap = np.exp(-((X - center_x)**2 + (Y - center_y)**2) / (2 * sigma**2))

        # Add secondary hotspot
        center_x2, center_y2 = -0.3, -0.2
        heatmap += 0.6 * np.exp(-((X - center_x2)**2 + (Y - center_y2)**2) / (2 * sigma**2))

        # Normalize to 0-255
        heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
        heatmap = (heatmap * 255).astype(np.uint8)

        return heatmap

    def generate_with_gradcam(self, model, image_array: np.ndarray, layer_name: str) -> np.ndarray:
        """
        Generate actual GradCAM heatmap (to be implemented with TensorFlow)

        Args:
            model: Keras model
            image_array: Preprocessed image
            layer_name: Target conv layer

        Returns:
            Heatmap array
        """
        try:
            import tensorflow as tf
            from tensorflow.keras import Model

            # Get the target layer output and model output
            grad_model = Model(
                inputs=[model.inputs],
                outputs=[model.get_layer(layer_name).output, model.output]
            )

            # Record gradients
            with tf.GradientTape() as tape:
                conv_outputs, predictions = grad_model(image_array)
                pred_index = tf.argmax(predictions[0])
                class_channel = predictions[:, pred_index]

            # Compute gradients
            grads = tape.gradient(class_channel, conv_outputs)

            # Pool gradients across spatial dimensions
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

            # Weight the feature maps
            conv_outputs = conv_outputs[0]
            heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
            heatmap = tf.squeeze(heatmap)

            # Normalize heatmap
            heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)

            return heatmap.numpy()

        except Exception as e:
            logger.error(f"Error in GradCAM generation: {e}")
            return None


# Global instance
gradcam_service = GradCAMService()
