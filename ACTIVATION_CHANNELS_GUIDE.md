# Activation Channel Segmentation - Implementation Guide

## Overview

This feature extracts learned feature channels from EfficientNet-B7 and uses them to **segment and highlight rash regions** with sharp, interpretable overlays in verdigris/teal colors.

**Key advantage over Grad-CAM:**
- ✓ **Sharp segmentation** instead of blurry color blobs
- ✓ **Interpretable**: "These channels detect rash features"
- ✓ **Clinically relevant**: Shows exact affected regions
- ✓ **All data tied to session ID** for complete traceability

---

## Quick Start

### Step 1: Analyze Your Images (One-Time)

```bash
python3 analyze_rash_channels.py \
  --images-dir /path/to/your/100/images \
  --model-path gs://total-furnace-288818-models/efficientnet_b7_ad.h5 \
  --output channel_analysis_report.json
```

### Step 2: Review Report

```bash
cat channel_analysis_report.json
```

Look for recommended channels (usually top 5).

### Step 3: Update Configuration

**File:** `backend/app/services/activation_channel_service.py`, line ~40:

```python
# CURRENT (verified on 123 images, Dec 11):
DEFAULT_RASH_CHANNELS = [60, 84, 40, 74, 85]  # Top 5 channels by score
```

**Empirical Results** (from `analyze_rash_channels.py`, 123 images tested):
- Channel 60: 0.1420 ⭐ (std: 0.0652)
- Channel 84: 0.1376 (std: 0.0586)
- Channel 40: 0.1348 (std: 0.0541)
- Channel 74: 0.1329 (std: 0.0571)
- Channel 85: 0.1316 (std: 0.0555)

### Step 4: Deploy

```bash
./deploy-gcp-fast.sh --dev
```

---

## Architecture

### Components

1. **activation_channel_service.py** - Channel extraction & visualization
2. **analyze_rash_channels.py** - One-time analysis script
3. **cnn_service.py** - Modified to generate overlays
4. **results_screen.dart** - Flutter UI display

### Data Flow

```
CNN inference
  ↓
Extract activation maps (19×19×2560)
  ↓
Select best channels [57, 62, 45, ...]
  ↓
Upscale 19×19 → 600×600
  ↓
Normalize & combine
  ↓
Apply verdigris colormap
  ↓
Blend with original + boundaries
  ↓
Save to GCS (tied to session_id)
  ↓
Display on HCP report
```

---

## Implementation Details

### ActivationChannelService Methods

```python
# Extract single channel
channel_map = service.extract_channel_map(image_array, channel_idx=57)

# Create segmentation from multiple channels
segmentation = service.create_rash_segmentation(image_array)

# Create colored overlay
overlay = service.create_overlay(original_path, segmentation, alpha=0.4)

# Save all data with session ID
files = service.save_segmentation_maps(
    session_id,
    original_path,
    segmentation,
    overlay,
    channel_data
)
```

### Channel Analysis Scoring

Analyzes each channel by computing:

1. **Texture correlation**: Does channel activate where skin has high texture?
2. **Redness correlation**: Does channel activate where skin is red/inflamed?
3. **Combined score**: 70% texture + 30% redness

Higher scores = better at detecting rash.

---

## Data Storage

All activation channel data tied to session ID:

```
gs://total-furnace-288818-skinopathy-data/activation_channels/{session_id}/
├── overlay.png           # Final visualization
├── segmentation.npy      # Raw segmentation
├── channel_*.npy         # Individual channels
└── metadata.json         # Parameters used
```

In database:
```
AIResult:
├── activation_channel_url     # URL to overlay PNG
├── activation_channels_used   # [57, 62, 45, ...]
├── activation_segmentation_path
└── activation_metadata_path
```

---

## Configuration

### Verdigris Colormap

```
Intensity 0.0 → (0, 0, 0)       Black
Intensity 0.2 → (100, 180, 160) Light teal
Intensity 0.4 → (67, 169, 140)  Medium verdigris
Intensity 0.6 → (45, 140, 120)  Verdigris
Intensity 0.8 → (30, 110, 100)  Dark verdigris
Intensity 1.0 → (20, 80, 80)    Deep verdigris
```

### Overlay Parameters

```python
alpha=0.4              # 40% overlay, 60% original
add_boundaries=True    # Draw contour outlines
threshold=0.4          # Boundary threshold
```

---

## Troubleshooting

### Analysis Too Slow?

Analyze subset first:
```bash
python3 analyze_rash_channels.py \
  --images-dir /path \
  --channel-range 50 70  # Just channels 50-70
```

### Segmentation Looks Wrong?

1. Check top channels in report
2. Adjust alpha (0.3 = transparent, 0.5 = opaque)
3. Adjust boundary threshold (0.3 = more, 0.5 = fewer)

### Overlay Not Showing?

1. Verify URL in database
2. Check Cloud Storage files exist
3. Check Cloud Run logs

---

## Performance

- Channel analysis: 30-60 min (100 images)
- Runtime per image: 200-300ms
- Storage: 2-3 MB per session

---

## Next Steps

1. Prepare 100 diverse AD images
2. Run channel analysis
3. Update backend with best channels
4. Deploy
5. Test end-to-end

See channel_analysis_report.json for detailed scores.
