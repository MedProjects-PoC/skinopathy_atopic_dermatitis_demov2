# Skinopathy AD API Documentation

AI-powered Atopic Dermatitis Assessment API with multi-agent analysis system.

## Base URL

```
https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app
```

## Interactive Documentation

**Swagger UI (Recommended):** https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app/docs

**ReDoc:** https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app/redoc

## Quick Start

### 1. Health Check

```bash
curl https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

### 2. Complete Analysis Workflow

#### Step 1: Upload Image + Questionnaire

```bash
curl -X POST https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app/api/v1/upload \
  -F "image=@/path/to/skin_image.jpg" \
  -F "questionnaire={
    \"itch_intensity\": 7,
    \"chronic_relapsing\": true,
    \"atopic_triad_history\": true,
    \"primary_location\": \"flexural areas\",
    \"household_itchy_or_nighttime_worse\": true,
    \"new_exposure_trigger\": false,
    \"thick_silvery_scales\": false,
    \"nights_sleep_disturbed\": 4,
    \"oozing_honey_crusts\": false,
    \"steroid_use_last_2weeks\": false,
    \"moisturizer_frequency\": \"twice_daily\",
    \"recent_stress_level\": 6
  }"
```

Response:
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Upload successful",
  "status": "processing"
}
```

#### Step 2: Check Analysis Status

```bash
curl https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app/api/v1/analysis/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

Response:
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "created_at": "2025-12-05T12:00:00Z"
}
```

#### Step 3: Get User Report

```bash
curl "https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app/api/v1/reports/a1b2c3d4-e5f6-7890-abcd-ef1234567890?type=user"
```

Response:
```json
{
  "type": "user",
  "severity": "Moderate",
  "summary": "Analysis complete. Your AD severity is moderate.",
  "key_findings": [
    "EASI Score: 18.5/72",
    "CNN Severity: 45.2/100",
    "Affected Area: 12.3%"
  ],
  "recommendations": [
    "Continue daily moisturizer routine",
    "Consult with your dermatologist about treatment",
    "Track symptoms and flare triggers"
  ]
}
```

#### Step 4: Get Clinical Report (HCP)

```bash
curl "https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app/api/v1/reports/a1b2c3d4-e5f6-7890-abcd-ef1234567890?type=hcp"
```

Response includes:
- Integrated CNN + Vision Agent + EASI assessment
- SOAP-formatted clinical note
- Detailed EASI breakdown
- AI attention map (saliency map)
- OpenCV lesion/erythema metrics
- Treatment recommendations

## API Endpoints

### Health & Info

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API info |
| GET | `/health` | Health check |

### Upload

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload skin image + questionnaire data |

**Request:** `multipart/form-data`
- `image`: Image file (JPG, PNG)
- `questionnaire`: JSON with patient data

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analysis/{session_id}` | Get analysis status |

**Response Status Values:**
- `processing`: Multi-agent analysis in progress (~2-3 min)
- `completed`: Analysis finished, reports available
- `failed`: Analysis failed

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reports/{session_id}?type=user` | Get patient-friendly report |
| GET | `/api/v1/reports/{session_id}?type=hcp` | Get clinical report |

### Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tracking/patient/{patient_id}` | Get patient's session history |

## Analysis Pipeline

The API uses a **multi-agent AI system**:

1. **CNN Analysis** (EfficientNet-B7)
   - Severity scoring (0-100)
   - Affected area percentage
   - Clinical features (inflammation, dryness, lichenification)

2. **Vision Agent** (Gemini 2.5 Flash + RAG)
   - Visual feature extraction
   - Body area analysis
   - Differential diagnosis support

3. **EASI Scoring Agent** (Gemini 2.5 Flash + RAG)
   - Formal EASI calculation (0-72 scale)
   - Regional breakdown
   - Clinical interpretation

4. **Fast Activation Map** (OpenCV + CNN activations)
   - Visual attention highlighting
   - Lesion count detection
   - Erythema percentage analysis

**Processing Time:** ~2-3 minutes (includes cold start on first request)

## Response Schemas

### User Report
```json
{
  "type": "user",
  "severity": "Mild | Moderate | Severe",
  "summary": "string",
  "key_findings": ["string"],
  "recommendations": ["string"],
  "when_to_seek_help": "string"
}
```

### HCP Report
```json
{
  "type": "hcp",
  "integrated_assessment": {
    "cnn_severity": 0-100,
    "easi_score": 0-72,
    "severity_category": "Mild | Moderate | Severe"
  },
  "clinical_note": {
    "chief_complaint": "string",
    "history_present_illness": "string",
    "objective_findings": "string",
    "assessment": "string",
    "plan": "string",
    "ai_insights": "string"
  },
  "easi_breakdown": {
    "head_neck": {...},
    "trunk": {...},
    "upper_limbs": {...},
    "lower_limbs": {...},
    "total_easi": 0-72
  },
  "cnn_analysis": {...},
  "vision_agent_findings": {...},
  "treatment_recommendations": [...],
  "saliency_map_url": "string",
  "saliency_map_metrics": {
    "lesion_count": 0,
    "erythema_percentage": 0.0,
    "gradcam_used": false
  }
}
```

## Questionnaire Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `itch_intensity` | int (0-10) | Itch severity | 7 |
| `chronic_relapsing` | boolean | Chronic/relapsing pattern | true |
| `atopic_triad_history` | boolean | History of asthma/hay fever/eczema | true |
| `primary_location` | string | Body area affected | "flexural areas" |
| `household_itchy_or_nighttime_worse` | boolean | Family history or worse at night | true |
| `new_exposure_trigger` | boolean | Recent trigger exposure | false |
| `thick_silvery_scales` | boolean | Psoriasis-like scales | false |
| `nights_sleep_disturbed` | int (0-7) | Nights with sleep disruption | 4 |
| `oozing_honey_crusts` | boolean | Infection signs | false |
| `steroid_use_last_2weeks` | boolean | Recent steroid use | false |
| `moisturizer_frequency` | string | Moisturizer use | "twice_daily" |
| `recent_stress_level` | int (0-10) | Stress level | 6 |

## Python Example

```python
import requests
import json

BASE_URL = "https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app"

# Step 1: Upload
with open("skin_image.jpg", "rb") as image_file:
    questionnaire = {
        "itch_intensity": 7,
        "chronic_relapsing": True,
        "atopic_triad_history": True,
        "primary_location": "flexural areas",
        "household_itchy_or_nighttime_worse": True,
        "new_exposure_trigger": False,
        "thick_silvery_scales": False,
        "nights_sleep_disturbed": 4,
        "oozing_honey_crusts": False,
        "steroid_use_last_2weeks": False,
        "moisturizer_frequency": "twice_daily",
        "recent_stress_level": 6
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/upload",
        files={"image": image_file},
        data={"questionnaire": json.dumps(questionnaire)}
    )

    session_id = response.json()["session_id"]
    print(f"Session ID: {session_id}")

# Step 2: Poll for completion
import time
while True:
    status_response = requests.get(f"{BASE_URL}/api/v1/analysis/{session_id}")
    status = status_response.json()["status"]

    if status == "completed":
        break
    elif status == "failed":
        raise Exception("Analysis failed")

    print(f"Status: {status}")
    time.sleep(5)

# Step 3: Get reports
user_report = requests.get(f"{BASE_URL}/api/v1/reports/{session_id}?type=user").json()
hcp_report = requests.get(f"{BASE_URL}/api/v1/reports/{session_id}?type=hcp").json()

print(f"Severity: {user_report['severity']}")
print(f"EASI Score: {hcp_report['integrated_assessment']['easi_score']}")
```

## JavaScript/Node.js Example

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const BASE_URL = 'https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app';

async function analyzeImage(imagePath) {
  // Step 1: Upload
  const form = new FormData();
  form.append('image', fs.createReadStream(imagePath));
  form.append('questionnaire', JSON.stringify({
    itch_intensity: 7,
    chronic_relapsing: true,
    atopic_triad_history: true,
    primary_location: "flexural areas",
    household_itchy_or_nighttime_worse: true,
    new_exposure_trigger: false,
    thick_silvery_scales: false,
    nights_sleep_disturbed: 4,
    oozing_honey_crusts: false,
    steroid_use_last_2weeks: false,
    moisturizer_frequency: "twice_daily",
    recent_stress_level: 6
  }));

  const uploadResponse = await axios.post(`${BASE_URL}/api/v1/upload`, form, {
    headers: form.getHeaders()
  });

  const sessionId = uploadResponse.data.session_id;
  console.log(`Session ID: ${sessionId}`);

  // Step 2: Poll for completion
  let status = 'processing';
  while (status === 'processing') {
    await new Promise(resolve => setTimeout(resolve, 5000));

    const statusResponse = await axios.get(`${BASE_URL}/api/v1/analysis/${sessionId}`);
    status = statusResponse.data.status;
    console.log(`Status: ${status}`);
  }

  // Step 3: Get reports
  const userReport = await axios.get(`${BASE_URL}/api/v1/reports/${sessionId}?type=user`);
  const hcpReport = await axios.get(`${BASE_URL}/api/v1/reports/${sessionId}?type=hcp`);

  return {
    user: userReport.data,
    hcp: hcpReport.data
  };
}

// Usage
analyzeImage('./skin_image.jpg')
  .then(reports => {
    console.log('Severity:', reports.user.severity);
    console.log('EASI Score:', reports.hcp.integrated_assessment.easi_score);
  })
  .catch(console.error);
```

## Rate Limiting & Costs

- No authentication required (demo environment)
- Processing time: ~2-3 minutes per analysis
- Recommended: Implement polling with 5-second intervals
- Cold start may add 30-60 seconds on first request

**AI Model Costs (per analysis):**
- Vision Agent: ~$0.0002
- EASI Agent: ~$0.0003
- **Total: ~$0.0005 per analysis**

## CORS

CORS is enabled for all origins in the demo environment.

## Support

For issues or questions, contact the API administrator or check the interactive docs at:
https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app/docs

---

**Version:** 2.0.0
**Last Updated:** December 2025
