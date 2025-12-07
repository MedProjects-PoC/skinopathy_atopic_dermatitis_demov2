"""
activation Service for Saliency Map Generation
Adapted from existing Skinopathy pytorch-activation implementation
"""
import numpy as np
import cv2
from PIL import Image
from typing import Optional, Tuple, Dict
from loguru import logger
import os
from app.core.config import settings


class activationService:
    """Generate saliency maps using activation technique"""

    def __init__(self, alpha: float = 0.4):
        """
        Initialize activation service

        Args:
            alpha: Transparency for heatmap overlay (0.0 to 1.0)
        """
        self.alpha = alpha
        self.is_available = False

    def generate_saliency_map(
        self,
        image_path: str,
        output_path: str,
        model=None,
        layer_name: str = 'top_conv',
        session_id: str = None
    ) -> Optional[Dict]:
        """
        Generate comprehensive saliency map with:
        - activation activation maps (model attention)
        - Lesion counting via edge detection
        - Erythema detection with skin tone awareness
        All combined into a single overlay visualization

        Args:
            image_path: Path to input image
            output_path: Path to save saliency map
            model: Optional Keras model for real activation (if None, uses mock)
            layer_name: Target layer for activation

        Returns:
            Dict with path and metrics, or None if generation failed
        """
        try:
            logger.info(f"Generating comprehensive saliency map for: {image_path}")

            # Load original image
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Could not load image: {image_path}")
                return None

            h, w = img.shape[:2]

            # Step 1: Detect lesions using edge detection
            logger.info("Step 1/3: Detecting lesions with OpenCV edge detection")
            edge_map, lesion_count = self._detect_lesions(img)

            # Step 2: Detect erythema with skin tone awareness
            logger.info("Step 2/3: Detecting erythema (skin tone aware)")
            erythema_mask, erythema_pct = self._detect_erythema(img)

            # Step 3: Generate activation heatmap
            logger.info("Step 3/3: Generating activation activation map")
            heatmap_uint8 = None
            activation_used = False

            # Try to use real activation if model is available
            if model is not None:
                try:
                    logger.info("Using real activation with CNN model")

                    # Preprocess image for model input (600x600 for EfficientNet-B7)
                    from PIL import Image as PILImage
                    img_pil = PILImage.open(image_path).convert('RGB')
                    img_pil = img_pil.resize((600, 600))
                    img_array = np.array(img_pil, dtype=np.float32) / 255.0
                    img_array = np.expand_dims(img_array, axis=0)

                    # Find the appropriate layer name for EfficientNet-B7
                    target_layer = None
                    for layer_candidate in ['top_conv', 'block7a_project_conv', 'top_activation']:
                        try:
                            model.get_layer(layer_candidate)
                            target_layer = layer_candidate
                            logger.info(f"Using activation layer: {target_layer}")
                            break
                        except:
                            continue

                    if target_layer is None:
                        # Fallback: find the last convolutional layer
                        for layer in reversed(model.layers):
                            if 'conv' in layer.name.lower():
                                target_layer = layer.name
                                logger.info(f"Using fallback layer: {target_layer}")
                                break

                    if target_layer:
                        # Generate FAST activation map with intelligent channel selection
                        # This is 10-100x faster than full activation!
                        heatmap = self.generate_fast_activation_map(model, img_array, target_layer, auto_select=True)

                        if heatmap is not None:
                            # Resize heatmap to match original image dimensions
                            heatmap_resized = cv2.resize(heatmap, (w, h))
                            heatmap_uint8 = (heatmap_resized * 255).astype(np.uint8)
                            activation_used = True
                            logger.success("Fast activation map generated successfully")
                        else:
                            logger.warning("Fast activation map returned None")
                    else:
                        logger.warning("No suitable conv layer found")

                except Exception as e:
                    logger.warning(f"Real activation failed: {e}, falling back to mock")

            # Fallback to mock heatmap if activation failed
            if heatmap_uint8 is None:
                logger.info("Using mock heatmap")
                heatmap_uint8 = self._create_mock_heatmap(w, h)
                activation_used = False

            # Create composite visualization
            logger.info("Combining activation + lesion edges + erythema into overlay")

            # Start with the original image
            result = img.copy()

            # 1. Apply activation heatmap (base layer - model attention)
            heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
            result = cv2.addWeighted(result, 0.6, heatmap_colored, 0.4, 0)

            # 2. Overlay lesion edges in white (high contrast)
            # Convert edge map to 3-channel
            edges_colored = cv2.cvtColor(edge_map, cv2.COLOR_GRAY2BGR)
            edges_colored = np.where(edges_colored > 0, [255, 255, 255], [0, 0, 0]).astype(np.uint8)
            result = cv2.addWeighted(result, 1.0, edges_colored, 0.3, 0)

            # 3. Overlay erythema mask in cyan (stands out on red activation)
            erythema_colored = np.zeros_like(img)
            erythema_colored[:, :, 1] = erythema_mask  # Green channel
            erythema_colored[:, :, 2] = erythema_mask  # Blue channel (cyan = green + blue)
            result = cv2.addWeighted(result, 1.0, erythema_colored, 0.2, 0)

            # Save result locally first
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cv2.imwrite(output_path, result)

            logger.success(f"Comprehensive saliency map saved to: {output_path}")
            logger.info(f"  - Lesion count: {lesion_count}")
            logger.info(f"  - Erythema coverage: {erythema_pct:.1f}%")
            logger.info(f"  - activation: {'Real' if activation_used else 'Mock'}")

            # Upload to Cloud Storage if in GCP environment
            public_url = None
            if settings.USE_CLOUD_STORAGE and session_id:
                try:
                    from app.services.cloud_storage_service import cloud_storage_service
                    public_url = cloud_storage_service.upload_saliency_map(output_path, session_id)
                    if public_url:
                        logger.success(f"Saliency map uploaded to Cloud Storage: {public_url}")
                except Exception as e:
                    logger.warning(f"Failed to upload to Cloud Storage: {e}")

            return {
                "path": output_path,
                "public_url": public_url,  # GCS URL for production, None for local
                "lesion_count": lesion_count,
                "erythema_percentage": round(erythema_pct, 2),
                "activation_used": activation_used
            }

        except Exception as e:
            logger.error(f"Error generating saliency map: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _detect_lesions(self, img: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Detect lesions using OpenCV edge detection

        Args:
            img: Input image (BGR format)

        Returns:
            Tuple of (edge map, lesion count)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Use adaptive thresholding to handle varying lighting
            adaptive_thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )

            # Morphological operations to clean up noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_OPEN, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)

            # Canny edge detection
            edges = cv2.Canny(blurred, 30, 100)

            # Combine threshold and edges
            combined = cv2.bitwise_or(cleaned, edges)

            # Find contours for lesion counting
            contours, _ = cv2.findContours(
                combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Filter contours by area to remove noise (lesions typically > 100 pixels)
            min_area = 100
            max_area = img.shape[0] * img.shape[1] * 0.1  # Max 10% of image
            lesion_contours = [
                c for c in contours
                if min_area < cv2.contourArea(c) < max_area
            ]

            lesion_count = len(lesion_contours)

            logger.info(f"Detected {lesion_count} lesions")
            return combined, lesion_count

        except Exception as e:
            logger.error(f"Error in lesion detection: {e}")
            # Return empty edge map
            return np.zeros(img.shape[:2], dtype=np.uint8), 0

    def _detect_erythema(self, img: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Detect erythema (redness) with skin tone awareness
        Accounts for darker skin where erythema appears brownish-purple

        Args:
            img: Input image (BGR format)

        Returns:
            Tuple of (erythema mask, erythema percentage)
        """
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Convert to LAB color space for skin tone detection
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)

            # Estimate skin tone from L channel (lightness)
            mean_lightness = np.mean(l_channel)

            # Define color ranges based on skin tone
            # For lighter skin (higher L): classic red/pink erythema
            # For darker skin (lower L): brownish-purple erythema

            if mean_lightness > 140:  # Light skin
                # Red/pink hues
                lower1 = np.array([0, 40, 40])
                upper1 = np.array([10, 255, 255])
                lower2 = np.array([160, 40, 40])
                upper2 = np.array([180, 255, 255])

                mask1 = cv2.inRange(hsv, lower1, upper1)
                mask2 = cv2.inRange(hsv, lower2, upper2)
                erythema_mask = cv2.bitwise_or(mask1, mask2)

            elif mean_lightness > 100:  # Medium skin tone
                # Broader range including reddish-brown
                lower1 = np.array([0, 30, 30])
                upper1 = np.array([20, 255, 255])
                lower2 = np.array([150, 30, 30])
                upper2 = np.array([180, 255, 255])

                mask1 = cv2.inRange(hsv, lower1, upper1)
                mask2 = cv2.inRange(hsv, lower2, upper2)
                erythema_mask = cv2.bitwise_or(mask1, mask2)

            else:  # Darker skin
                # Focus on purple/violet hues (erythema on dark skin)
                # Also include brownish-red tones
                lower_purple = np.array([125, 20, 20])
                upper_purple = np.array([155, 255, 255])
                lower_brown_red = np.array([0, 20, 20])
                upper_brown_red = np.array([25, 255, 200])

                mask1 = cv2.inRange(hsv, lower_purple, upper_purple)
                mask2 = cv2.inRange(hsv, lower_brown_red, upper_brown_red)
                erythema_mask = cv2.bitwise_or(mask1, mask2)

            # Morphological operations to clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            erythema_mask = cv2.morphologyEx(erythema_mask, cv2.MORPH_OPEN, kernel)
            erythema_mask = cv2.morphologyEx(erythema_mask, cv2.MORPH_CLOSE, kernel)

            # Calculate erythema percentage
            total_pixels = img.shape[0] * img.shape[1]
            erythema_pixels = np.count_nonzero(erythema_mask)
            erythema_pct = (erythema_pixels / total_pixels) * 100

            logger.info(f"Detected erythema: {erythema_pct:.1f}% (skin tone L={mean_lightness:.0f})")
            return erythema_mask, erythema_pct

        except Exception as e:
            logger.error(f"Error in erythema detection: {e}")
            # Return empty mask
            return np.zeros(img.shape[:2], dtype=np.uint8), 0.0

    def _create_mock_heatmap(self, width: int, height: int) -> np.ndarray:
        """
        Create a mock heatmap for demonstration
        In production, this will be replaced with actual activation output
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

    def select_best_activation_channel(self, activations: np.ndarray, sample_channels: int = 20) -> Tuple[int, float]:
        """
        Intelligently select the best activation channel by analyzing feature content using OpenCV

        Args:
            activations: Activation tensor (1, height, width, num_channels)
            sample_channels: Number of channels to sample and evaluate

        Returns:
            Tuple of (best_channel_idx, feature_score)
        """
        num_channels = activations.shape[-1]

        # Sample channels evenly across the range (focus on middle-to-later channels)
        # Later channels often capture higher-level features like lesions
        start_ch = max(0, num_channels // 4)  # Start at 25% through
        end_ch = num_channels
        channel_indices = np.linspace(start_ch, end_ch - 1, min(sample_channels, end_ch - start_ch), dtype=int)

        best_channel = channel_indices[0]
        best_score = 0.0

        logger.info(f"Evaluating {len(channel_indices)} activation channels from {num_channels} total...")

        for ch_idx in channel_indices:
            # Extract channel
            channel = activations[0, :, :, ch_idx]

            # Normalize and convert to uint8 for OpenCV
            channel_norm = np.maximum(channel, 0)  # ReLU
            if channel_norm.max() > 0:
                channel_norm = channel_norm / channel_norm.max()
            channel_uint8 = (channel_norm * 255).astype(np.uint8)

            # Apply edge detection to measure feature content
            edges = cv2.Canny(channel_uint8, 30, 100)

            # Count edge pixels
            edge_count = np.count_nonzero(edges)

            # Also measure variance (higher variance = more varied features)
            variance = np.var(channel_norm)

            # Compute feature score (weighted combination)
            feature_score = edge_count + (variance * 10000)  # Weight variance to scale with edge count

            if feature_score > best_score:
                best_score = feature_score
                best_channel = ch_idx

        logger.success(f"Selected channel {best_channel}/{num_channels} with feature score: {best_score:.1f}")
        return best_channel, best_score

    def generate_fast_activation_map(self, model, image_array: np.ndarray, layer_name: str, auto_select: bool = True) -> np.ndarray:
        """
        FAST activation map generation - extracts the best channel without gradients
        This is 10-100x faster than full activation!

        Args:
            model: Keras model
            image_array: Preprocessed image
            layer_name: Target conv layer
            auto_select: If True, automatically select best channel using OpenCV feature analysis

        Returns:
            Heatmap array
        """
        try:
            import tensorflow as tf
            from tensorflow.keras import Model

            # Create model that outputs the target layer activations
            # NO GRADIENT COMPUTATION - just a forward pass!
            activation_model = Model(
                inputs=model.inputs,
                outputs=model.get_layer(layer_name).output
            )

            # Single forward pass - no backpropagation needed!
            activations = activation_model.predict(image_array, verbose=0)

            # activations shape: (1, height, width, num_channels)
            num_channels = activations.shape[-1]
            logger.info(f"Layer '{layer_name}' has {num_channels} channels")

            # Intelligently select best channel
            if auto_select:
                best_channel_idx, feature_score = self.select_best_activation_channel(activations)
            else:
                # Fallback to channel 57 or mid-range channel
                best_channel_idx = min(57, num_channels - 1)
                logger.info(f"Using default channel {best_channel_idx}")

            # Extract the best channel
            channel_activation = activations[0, :, :, best_channel_idx]

            # Normalize to 0-1 range
            channel_activation = np.maximum(channel_activation, 0)  # ReLU
            if channel_activation.max() > 0:
                channel_activation = channel_activation / channel_activation.max()

            logger.success(f"Fast activation map generated from channel {best_channel_idx}/{num_channels}")
            return channel_activation

        except Exception as e:
            logger.error(f"Error in fast activation map generation: {e}")
            return None

    def generate_with_activation(self, model, image_array: np.ndarray, layer_name: str) -> np.ndarray:
        """
        Generate actual activation heatmap (SLOW - requires gradient computation)

        NOTE: This is kept for reference but we now use generate_fast_activation_map()
        which is 10-100x faster and often produces similar results.

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
            logger.error(f"Error in activation generation: {e}")
            return None


# Global instance
activation_service = activationService()
