#!/usr/bin/env python3
"""
Activation Channel Analysis Script

Analyzes EfficientNet-B7 activation channels to identify which ones best
highlight dermatitis/rash regions. Should be run on 100+ diverse AD images.

Usage:
    python3 analyze_rash_channels.py --images-dir /path/to/images --output report.json
"""

import sys
import os
import json
import argparse
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, List, Tuple
import tensorflow as tf
from tensorflow.keras.preprocessing import image as keras_image

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.cnn_service import cnn_service
from app.services.activation_channel_service import ActivationChannelService


class RashChannelAnalyzer:
    """Analyzes activation channels to find rash detectors"""

    def __init__(self, model_path: str = None):
        """
        Initialize analyzer with CNN model

        Args:
            model_path: Path to EfficientNet-B7 .h5 model
        """
        self.cnn_service = cnn_service
        if model_path:
            self.cnn_service.model_path = model_path

        # Load model
        self.cnn_service.load_model()
        if not self.cnn_service.is_loaded:
            raise RuntimeError("Failed to load CNN model")

        self.activation_service = ActivationChannelService(self.cnn_service.model)
        self.input_size = (600, 600)
        self.feature_map_size = (19, 19)

        # Results storage
        self.channel_scores = {}
        self.analysis_results = {}

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for model input

        Args:
            image_path: Path to image file

        Returns:
            Preprocessed image array (1, 600, 600, 3)
        """
        from PIL import Image
        img = Image.open(image_path).convert('RGB')
        img = img.resize(self.input_size)
        img_array = np.array(img, dtype=np.float32) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        return img_array

    def correlate_with_visible_rash(
        self,
        channel_map: np.ndarray,
        original_image_path: str,
        edge_threshold: float = 0.15
    ) -> float:
        """
        Score how well a channel activation correlates with visible rash

        Uses edge detection to identify skin regions with high texture/activity,
        then checks if channel has high activation in those regions.

        Args:
            channel_map: Normalized channel map (600, 600)
            original_image_path: Path to original image
            edge_threshold: Threshold for edge detection

        Returns:
            Correlation score 0-1 (higher = better at detecting rash)
        """
        try:
            # Load original image
            from PIL import Image
            original = Image.open(original_image_path).convert('RGB')
            original = np.array(original.resize(self.input_size))
            original_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)

            # Detect edges/texture (rash has high texture variation)
            edges = cv2.Canny(original_gray, 50, 150)
            edges_normalized = edges.astype(float) / 255.0

            # Compute correlation: do high channel activations align with high texture?
            correlation = np.corrcoef(
                channel_map.flatten(),
                edges_normalized.flatten()
            )[0, 1]

            # Handle NaN correlation
            if np.isnan(correlation):
                correlation = 0.0

            # Also check color: rash often has redness
            red = original[:, :, 0].astype(float) / 255.0
            green = original[:, :, 1].astype(float) / 255.0
            blue = original[:, :, 2].astype(float) / 255.0

            # Redness metric: R > G and R > B
            redness = np.maximum(0, red - np.maximum(green, blue))
            redness_normalized = redness / (np.max(redness) + 1e-8)

            # Check if channel activates on red regions
            red_correlation = np.corrcoef(
                channel_map.flatten(),
                redness_normalized.flatten()
            )[0, 1]
            if np.isnan(red_correlation):
                red_correlation = 0.0

            # Combine: 70% texture + 30% redness
            combined_score = 0.7 * max(0, correlation) + 0.3 * max(0, red_correlation)

            return float(combined_score)

        except Exception as e:
            print(f"Error computing correlation: {e}")
            return 0.0

    def analyze_channel(
        self,
        channel_idx: int,
        image_paths: List[str],
        verbose: bool = False
    ) -> Tuple[int, float, List[float]]:
        """
        Analyze single channel across multiple images

        Args:
            channel_idx: Channel index (0-2559)
            image_paths: Paths to test images
            verbose: Print progress

        Returns:
            Tuple of (channel_id, mean_score, all_scores)
        """
        if verbose:
            print(f"Analyzing channel {channel_idx}...", end=" ", flush=True)

        scores = []

        for img_path in image_paths:
            try:
                # Preprocess image
                img_array = self.preprocess_image(img_path)

                # Extract channel
                channel_map = self.activation_service.extract_channel_map(
                    img_array,
                    channel_idx,
                    layer_name='top_conv'
                )

                # Score correlation with visible rash
                score = self.correlate_with_visible_rash(channel_map, img_path)
                scores.append(score)

            except Exception as e:
                if verbose:
                    print(f"\n  Error on {img_path}: {e}")
                continue

        mean_score = float(np.mean(scores)) if scores else 0.0

        if verbose:
            print(f"Score: {mean_score:.4f} (n={len(scores)})")

        return channel_idx, mean_score, scores

    def analyze_all_channels(
        self,
        image_paths: List[str],
        channel_range: Tuple[int, int] = (30, 100),
        verbose: bool = True
    ) -> Dict[int, Dict]:
        """
        Analyze all channels in specified range

        Args:
            image_paths: Paths to test images
            channel_range: Tuple of (min_channel, max_channel) to analyze
            verbose: Print progress

        Returns:
            Dict mapping channel_id to score data
        """
        min_ch, max_ch = channel_range
        results = {}

        print(f"\n{'='*80}")
        print(f"Analyzing channels {min_ch}-{max_ch} on {len(image_paths)} images")
        print(f"{'='*80}\n")

        for ch_idx in range(min_ch, max_ch):
            ch_id, mean_score, scores = self.analyze_channel(
                ch_idx,
                image_paths,
                verbose=verbose
            )

            results[ch_id] = {
                'channel_id': ch_id,
                'mean_score': mean_score,
                'std_score': float(np.std(scores)) if scores else 0.0,
                'n_images': len(scores),
                'all_scores': scores
            }

        return results

    def find_top_channels(
        self,
        analysis_results: Dict,
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Find top K channels by score

        Args:
            analysis_results: Results from analyze_all_channels
            top_k: Number of top channels to return

        Returns:
            List of (channel_id, score) tuples, sorted by score descending
        """
        sorted_channels = sorted(
            analysis_results.items(),
            key=lambda x: x[1]['mean_score'],
            reverse=True
        )

        return [(ch_id, data['mean_score']) for ch_id, data in sorted_channels[:top_k]]

    def save_report(
        self,
        analysis_results: Dict,
        output_path: str,
        top_k: int = 10
    ):
        """
        Save analysis report to JSON file

        Args:
            analysis_results: Results from analyze_all_channels
            output_path: Path to save report
            top_k: Number of top channels to highlight
        """
        # Find top channels
        top_channels = self.find_top_channels(analysis_results, top_k)

        # Prepare report
        report = {
            'summary': {
                'total_channels_analyzed': len(analysis_results),
                'top_channels': [
                    {'channel': ch, 'score': float(score)}
                    for ch, score in top_channels
                ],
                'recommended_channels': [ch for ch, _ in top_channels[:5]],
            },
            'detailed_results': {}
        }

        # Add detailed results for top channels
        for ch_id in [ch for ch, _ in top_channels]:
            report['detailed_results'][str(ch_id)] = {
                'channel_id': ch_id,
                'mean_score': analysis_results[ch_id]['mean_score'],
                'std_score': analysis_results[ch_id]['std_score'],
                'n_images': analysis_results[ch_id]['n_images'],
            }

        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n{'='*80}")
        print(f"Report saved to: {output_path}")
        print(f"{'='*80}\n")

        # Print summary
        print("TOP 10 RASH-DETECTING CHANNELS:")
        print("-" * 80)
        for i, (ch, score) in enumerate(top_channels, 1):
            print(f"{i:2d}. Channel {ch:4d}: {score:.4f}")

        print("\nRECOMMENDED CHANNELS FOR PRODUCTION:")
        print("-" * 80)
        recommended = [ch for ch, _ in top_channels[:5]]
        print(f"Use channels: {recommended}")
        print("\nIn activation_channel_service.py, set:")
        print(f"DEFAULT_RASH_CHANNELS = {recommended}")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze EfficientNet-B7 activation channels for rash detection'
    )
    parser.add_argument(
        '--images-dir',
        required=True,
        help='Directory containing test images'
    )
    parser.add_argument(
        '--model-path',
        default=None,
        help='Path to .h5 model file (optional, uses default if not specified)'
    )
    parser.add_argument(
        '--output',
        default='channel_analysis_report.json',
        help='Output JSON report path'
    )
    parser.add_argument(
        '--channel-range',
        type=int,
        nargs=2,
        default=[30, 100],
        help='Channel range to analyze (min max)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=10,
        help='Number of top channels to report'
    )

    args = parser.parse_args()

    # Validate input directory
    images_dir = Path(args.images_dir)
    if not images_dir.exists():
        print(f"Error: Images directory not found: {images_dir}")
        sys.exit(1)

    # Get image paths
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    image_paths = [
        str(p) for p in images_dir.rglob('*')
        if p.is_file() and p.suffix.lower() in image_extensions
    ]

    if not image_paths:
        print(f"Error: No images found in {images_dir}")
        sys.exit(1)

    print(f"\nFound {len(image_paths)} images in {images_dir}")

    # Initialize analyzer
    print("\nLoading CNN model...")
    analyzer = RashChannelAnalyzer(model_path=args.model_path)

    # Analyze channels
    results = analyzer.analyze_all_channels(
        image_paths,
        channel_range=tuple(args.channel_range),
        verbose=True
    )

    # Save report
    analyzer.save_report(results, args.output, top_k=args.top_k)

    print("\n✅ Channel analysis complete!")
    print(f"\nNext steps:")
    print(f"1. Review the report: {args.output}")
    print(f"2. Update backend/app/services/activation_channel_service.py")
    print(f"3. Set DEFAULT_RASH_CHANNELS to the recommended channels")
    print(f"4. Redeploy backend")


if __name__ == '__main__':
    main()
