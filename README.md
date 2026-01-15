# Skinopathy-AtopicDermatitis-Demov2

AI-powered Atopic Dermatitis (AD) monitoring application with dual reporting system (user-friendly + HCP clinical reports), streamlined 2-agent AI architecture, and pre-flare detection capabilities.

> **Note**: This system has been significantly streamlined for performance (60-70% faster). See [EXPERIMENTS.md](./EXPERIMENTS.md) for details on experiments and architectural evolution.

## Overview

Skinopathy AD Demo is a comprehensive web-based assessment tool that combines advanced AI models with clinically validated questionnaires to provide accurate atopic dermatitis severity assessment and intelligent recommendations.

### Key Features

- **Multi-Modal AI Analysis**: Combines CNN (EfficientNet-B7) with Vision Language Models (Gemini 2.5 Flash) for comprehensive skin assessment
- **RAG-Enhanced Intelligence**: Retrieval-Augmented Generation using clinical knowledge base (EASI guidelines, Hanifin & Rajka criteria, IGA scoring, differential diagnosis guides)
- **Dual Reporting System**:
  - User-friendly reports with actionable recommendations
  - Clinical reports with CNN severity assessment, Vision AI analysis, and SOAP notes
- **12-Question Clinical Questionnaire**: Validated questions covering diagnostic criteria, clinical data, and lifestyle management
- **GradCAM Saliency Maps**: Visual attention maps showing AI focus areas (HCP feature)
- **Pre-Flare Detection**: Tracking and early warning capabilities
- **Flutter Web Frontend**: Modern, responsive web interface
- **Cloud-Ready**: Deployed on Google Cloud Platform with auto-scaling

## Architecture

### System Components

```
skinopathy_atopic_dermatitis_demov2/
├── backend/                      # FastAPI backend
│   ├── app/
│   │   ├── api/v1/              # API endpoints
│   │   │   └── endpoints/
│   │   │       ├── upload.py    # Image & questionnaire upload
│   │   │       ├── analysis.py  # Analysis results
│   │   │       └── reports.py   # Dual report generation
│   │   ├── agents/              # Streamlined 2-agent AI system (v2.0)
│   │   │   ├── base_agent.py   # Base agent class
│   │   │   └── vision_agent.py # Vision analysis (Gemini 2.5 Flash + RAG)
│   │   ├── services/            # Business logic
│   │   │   ├── cnn_service.py  # EfficientNet-B7 CNN
│   │   │   ├── gradcam_service.py  # Saliency maps
│   │   │   └── analysis_service_multiagent.py  # Multi-agent orchestration
│   │   ├── rag/                 # RAG system
│   │   │   ├── rag_service.py  # Semantic search
│   │   │   └── rag_config.py   # Clinical knowledge base
│   │   ├── models/              # Database models
│   │   │   └── database.py     # SQLAlchemy models
│   │   └── core/                # Configuration
│   │       ├── config.py       # Local config
│   │       └── config_gcp.py   # GCP config
│   ├── ml_models/               # ML models storage (local)
│   └── storage/                 # Image & saliency map storage
├── frontend/                     # Flutter web app
│   ├── lib/
│   │   ├── main.dart           # App entry point
│   │   ├── screens/
│   │   │   ├── home_screen.dart         # Image upload
│   │   │   ├── questionnaire_screen.dart # 12 questions
│   │   │   └── results_screen.dart      # Dual reports display
│   │   ├── services/
│   │   │   └── api_service.dart # Backend API client
│   │   └── models/
│   │       └── questionnaire.dart # Data models
│   └── pubspec.yaml            # Flutter dependencies
├── deploy-gcp.sh                # GCP deployment script
├── test_api.py                  # API testing script
└── docker-compose.yml           # Docker orchestration
```

### AI Pipeline (Streamlined - v2.0)

```
User Upload (Image + Questionnaire)
        ↓
[1/3] Parallel Execution (OPTIMIZED - Dec 2024)
    ├─> EfficientNet-B7 CNN Analysis
    │   - Severity prediction (0-100)
    │   - Body region distribution
    │   - Flare status detection
    │   - Differential diagnosis screening
    │   ⏱️ ~20-30 seconds
    │
    └─> Vision Agent (Gemini 2.5 Flash + RAG)
        - Clinical visual analysis
        - Pattern recognition
        - Lesion characterization
        - Context from clinical guidelines
        ⏱️ ~90-120 seconds
        ↓
[2/3] Save AI Results to Database
        ↓
[3/3] Generate Dual Reports
    ├─> User Report: CNN severity, lesion count, erythema %, Vision AI analysis
    ├─> HCP Report: CNN + Vision AI assessment + SOAP note
    └─> GradCAM Saliency Maps (Background, non-blocking)
        - Visual attention heatmaps
        - AI decision transparency

⏱️ Total Time: 2-3 minutes (down from 7-9 minutes)
📊 60-70% faster than previous architecture
```

**Key Changes (v2.0)**:
- Removed EASI agent for speed (see EXPERIMENTS.md)
- CNN + Vision AI run in parallel via `asyncio.gather()`
- Simplified reporting: focus on actionable insights
- Saliency maps no longer block report delivery

### Performance Optimizations (Dec 2024)

**Processing Time Improvements:**
- **Before**: 8-10 minutes per analysis (sequential processing)
- **After**: 3-4 minutes per analysis (parallel execution)
- **Reduction**: ~60% faster processing

**Key Optimizations:**
1. **Parallel Agent Execution** (`analysis_service_multiagent.py`):
   - CNN and Vision Agent now run concurrently using `asyncio.gather()`
   - GradCAM generation runs in background thread (`asyncio.to_thread()`)
   - Reduced pipeline from 5 sequential steps to 3 optimized steps

2. **Cloud Run Resource Optimization** (`deploy-gcp.sh`):
   - CPU: 2 vCPU → 4 vCPU (2x increase)
   - Memory: 2 GiB → 8 GiB (4x increase)
   - Timeout: 300s → 600s (extended for complex analysis)
   - Min instances: 0 → 1 (eliminates cold starts, always-warm)

3. **HCP Report Fix** (`reports.py`):
   - Removed strict Pydantic schema validation
   - Returns raw JSON to prevent 500 errors
   - Improved reliability and compatibility

**Cost Impact:**
- Idle cost: +$114/month (min-instances=1, eliminates 15-30s cold starts)
- Per-request cost: $0.029 → $0.024 (actually cheaper due to faster processing)
- Can be changed to min-instances=0 via GCP Console to eliminate idle cost

## 12-Question Clinical Questionnaire

### Section 1: Diagnostic Questions (7 questions)

1. **Itch Intensity** (Slider: 0-10)
   - 0 = No itch, 10 = Worst imaginable itch

2. **Chronic and Relapsing** (Yes/No)
   - Has this been going on for months/years with ups and downs?

3. **Atopic Triad History** (Yes/No)
   - Personal or family history of asthma, hay fever, or eczema

4. **Primary Location** (Dropdown)
   - Options: Flexural (elbows/knees inside), Extensor (elbows/knees outside), Face/Neck, Hands/Feet, Trunk, Widespread

5. **Household/Nighttime** (Yes/No)
   - Do others in your household have similar itching, or does it get worse at night?

6. **New Exposure Trigger** (Yes/No)
   - Did this start after exposure to something new? (soap, jewelry, plants, chemicals)

7. **Thick Silvery Scales** (Yes/No)
   - Are there thick, silvery scales on the rash? (suggests psoriasis)

### Section 2: Clinical Data Capture (3 questions)

8. **Nights Sleep Disturbed** (Slider: 0-7)
   - How many nights per week is your sleep disturbed by itching?

9. **Oozing Honey Crusts** (Yes/No)
   - Do you have oozing or honey-colored crusts? (suggests infection)

10. **Steroid Use** (Yes/No)
    - Have you used topical steroids in the last 2 weeks?

### Section 3: Management & Lifestyle (2 questions)

11. **Moisturizer Frequency** (Dropdown)
    - Options: None, Once daily, Twice daily, More than twice daily

12. **Recent Stress Level** (Slider: 0-10)
    - 0 = No stress, 10 = Extremely stressed

## Technology Stack

### Backend
- **FastAPI** 0.110.0 - Modern Python web framework
- **PostgreSQL** 15 - Relational database (Cloud SQL in production)
- **SQLAlchemy** 2.0.25 - ORM
- **Pydantic** 2.6.1 - Data validation
- **Uvicorn** 0.27.1 - ASGI server

### AI/ML
- **TensorFlow** 2.15.0 - CNN inference (EfficientNet-B7)
- **PyTorch** 2.1.2 - GradCAM implementation
- **LangChain** 0.2.16 - Multi-agent framework
- **Gemini 2.5 Flash** - Vision & EASI analysis agents (latest stable model)
- **Gemini 2.5 Pro** - Advanced analysis when needed
- **Gemini 2.0 Flash** - Experimental features
- **Vertex AI** - Managed AI platform
- **Vertex AI Text Embeddings (text-embedding-005)** - RAG semantic search
- **OpenCV** 4.9.0 - Image processing

### Frontend
- **Flutter** 3.24.5 - Cross-platform UI framework
- **Dart** 3.x - Programming language
- **HTTP** package - API communication
- **File Picker** - Image upload

### Infrastructure
- **Docker** & **Docker Compose** - Containerization
- **Google Cloud Platform**:
  - Cloud Run (serverless containers)
  - Cloud SQL (PostgreSQL 15)
  - Cloud Storage (models & images)
  - Artifact Registry (Docker images)
  - Secret Manager (credentials)
  - Vertex AI (AI/ML platform)

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Flutter SDK 3.24.5+ (for frontend development)
- Google Cloud SDK (for GCP deployment)

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Start PostgreSQL (using Docker)
docker run -d -p 5433:5432 \
  -e POSTGRES_DB=skinopathy_ad \
  -e POSTGRES_USER=skinopathy \
  -e POSTGRES_PASSWORD=demo_password \
  --name skinopathy-ad-db \
  postgres:15-alpine

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Get Flutter dependencies
flutter pub get

# Run on web (Chrome)
flutter run -d chrome

# Build for production
flutter build web
```

### Using Docker Compose (Recommended for Local Testing)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

The API will be available at: http://localhost:8000
API documentation: http://localhost:8000/api/v1/docs
Frontend: http://localhost:8080 (if configured)

## GCP Deployment

### Prerequisites

1. **Google Cloud Project**: skin-demos (Skinopathy Organization)
2. **Region**: us-central1
3. **Service Account**: 42406804042-compute@developer.gserviceaccount.com
4. **Required APIs Enabled**:
   - Cloud Run API
   - Cloud SQL Admin API
   - Cloud Storage API
   - Artifact Registry API
   - Secret Manager API
   - Vertex AI API

### Deployment Steps

```bash
# 1. Authenticate with GCP
gcloud auth login
gcloud config set project total-furnace-288818

# 2. Run deployment script
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2
./deploy-gcp.sh
```

The deployment script will:
1. ✓ Authenticate and set project
2. ✓ Create Cloud Storage buckets (models & data)
3. ✓ Create Artifact Registry repository
4. ✓ Create Cloud SQL PostgreSQL instance
5. ✓ Create database and user
6. ✓ Store secrets in Secret Manager
7. ✓ Build and push Docker image
8. ✓ Deploy to Cloud Run
9. ✓ Display service URL

### GCP Resources Created

#### Cloud Storage Buckets
- **skin-demos-models**: ML models (EfficientNet-B7: 457.9 MB)
- **skin-demos-skinopathy-data**: User images and saliency maps

#### Cloud SQL Instance
- **Name**: skinopathy-ad-db
- **Type**: PostgreSQL 15
- **Tier**: db-f1-micro (upgradeable)
- **Database**: skinopathy_ad
- **User**: skinopathy
- **Region**: us-central1

#### Cloud Run Service
- **Name**: skinopathy-atopic-dermatitis-demo2-api
- **Image**: us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api:latest
- **Memory**: 8 GiB (optimized for performance)
- **CPU**: 4 vCPU (optimized for parallel processing)
- **Port**: 8080
- **Concurrency**: 80
- **Timeout**: 600s (extended for complex analysis)
- **Min Instances**: 1 (always-warm for instant response)
- **Max Instances**: 10
- **CPU Throttling**: Enabled

#### Artifact Registry
- **Repository**: skinopathy-ad-repo
- **Format**: Docker
- **Location**: us-central1

#### Secret Manager
- **Secret**: skinopathy-ad-db-connection
- **Contains**: Cloud SQL connection string

### Environment Variables (Cloud Run)

```bash
PORT=8080
ENVIRONMENT=production
DATABASE_URL=<Cloud SQL connection via Unix socket>
GCP_PROJECT_ID=skin-demos
GCP_REGION=us-central1
MODELS_BUCKET=skin-demos-models
DATA_BUCKET=skin-demos-skinopathy-data
CNN_MODEL_PATH=gs://skin-demos-models/efficientnet_b7_ad.h5
```

## API Endpoints

### Upload
`POST /api/v1/upload/`
- Upload skin image + AD questionnaire (12 questions)
- Request body:
  ```json
  {
    "image": "data:image/jpeg;base64,<base64_string>",
    "questionnaire": {
      "itch_intensity": 7,
      "chronic_relapsing": true,
      "atopic_triad_history": true,
      "primary_location": "flexural",
      "household_itchy_or_nighttime_worse": false,
      "new_exposure_trigger": false,
      "thick_silvery_scales": false,
      "nights_sleep_disturbed": 4,
      "oozing_honey_crusts": false,
      "steroid_use_last_2weeks": true,
      "moisturizer_frequency": "twice_daily",
      "recent_stress_level": 6
    }
  }
  ```
- Returns: `{"session_id": "uuid"}`
- Triggers multi-agent analysis pipeline in background

### Analysis Status
`GET /api/v1/analysis/{session_id}`
- Get current analysis status
- Returns:
  ```json
  {
    "session_id": "uuid",
    "status": "processing|completed|failed",
    "created_at": "2025-12-01T12:00:00Z"
  }
  ```

### User Report
`GET /api/v1/reports/user/{session_id}`
- Get user-friendly report
- Returns:
  ```json
  {
    "severity": "Moderate",
    "summary": "Your skin shows signs of moderate atopic dermatitis...",
    "recommendations": [
      "Apply moisturizer at least twice daily",
      "Continue using prescribed topical steroids as directed",
      "Consider identifying and avoiding stress triggers"
    ],
    "ai_insights": {
      "severity_score": 68,
      "affected_area_pct": 15,
      "flare_status": "active"
    }
  }
  ```

### HCP Report
`GET /api/v1/reports/hcp/{session_id}`
- Get clinical HCP report with CNN + Vision AI assessment and SOAP note
- Returns:
  ```json
  {
    "integrated_assessment": {
      "cnn_severity": 68,
      "severity_category": "Moderate",
      "lesion_count": 12,
      "erythema_percentage": 45.3
    },
    "soap_note": {
      "subjective": "Patient reports itch intensity 7/10...",
      "objective": "CNN Analysis: Severity 68/100...",
      "assessment": "Atopic Dermatitis - Moderate severity",
      "plan": "Continue emollients, consider topical corticosteroids..."
    },
    "cnn_analysis": {
      "severity_score": 68,
      "body_region_distribution": {...},
      "flare_status": "active"
    },
    "vision_agent_findings": {
      "clinical_assessment": "...",
      "differential_diagnosis": "...",
      "key_features": [...]
    }
  }
  ```

## ML Models

### EfficientNet-B7 (CNN)
- **Location**: `gs://total-furnace-288818-models/efficientnet_b7_ad.h5`
- **Size**: 457.9 MB
- **Input**: 600x600 RGB images
- **Architecture**: EfficientNet-B7 (pretrained on ImageNet, fine-tuned on AD dataset)
- **Outputs**:
  - Severity score (0-100)
  - Body region distribution
  - Flare status (pre-flare, active, improving, resolved)
  - AD probability (differential diagnosis)

### Gemini 2.5 Flash (Vision Agent)
- **Model**: gemini-2.5-flash via Vertex AI
- **Purpose**: Clinical visual analysis with RAG enhancement
- **Context**: 1M tokens
- **Features**:
  - Multimodal input (image + text)
  - Clinical pattern recognition
  - RAG-augmented with EASI/IGA guidelines
  - Differential diagnosis reasoning
  - Improved accuracy over 1.5 Pro

### Report Generation (Integrated)
- **Approach**: Direct report generation in `analysis_service_multiagent.py`
- **Features**:
  - User-friendly reports with actionable recommendations
  - HCP clinical reports with SOAP notes
  - Integrated CNN + Vision AI findings
  - Cost-effective inline generation (no additional API calls)

### RAG Knowledge Base (Vertex AI Embeddings)
- **Model**: text-embedding-005 (latest, November 2024)
- **Sources**: 6 clinical documents
  1. Hanifin & Rajka diagnostic criteria
  2. Official EASI scoring system
  3. IGA scoring guidelines
  4. Differential diagnosis guide (psoriasis, scabies, contact dermatitis)
  5. Treatment guidelines (2023 AAD)
  6. Pre-flare detection patterns
- **Vector Similarity**: Cosine similarity
- **Top-K Retrieval**: 2-3 most relevant passages per query

### GradCAM
- **Framework**: PyTorch
- **Target Layer**: Last convolutional layer
- **Purpose**: Saliency map visualization for HCPs
- **Overlay Alpha**: 0.4

## Cost Estimates (GCP)

### Per Assessment (Single User) - v2.0 Streamlined
- **CNN Inference**: ~$0.0001 (Cloud Storage + compute)
- **Vision Agent (Gemini 2.5 Flash)**: ~$0.008 (input + output tokens)
- **RAG Embeddings**: ~$0.0005 (text-embedding-005)
- **Cloud Storage**: ~$0.001 (image + results storage)
- **Database Operations**: ~$0.0001 (Cloud SQL queries)

**Total per assessment: ~$0.01** (66% cost reduction vs previous 3-agent architecture)

### Monthly Estimates (100 users, 10 assessments/month) - v2.0
- **Compute**: 1,000 assessments × $0.01 = $10
- **Cloud SQL**: db-f1-micro = $7/month
- **Cloud Storage**: ~50 GB = $1.15/month
- **Cloud Run**: Minimal (serverless, pay-per-use) = ~$5/month

**Total: ~$23/month for 1,000 assessments** (40% cheaper than previous 3-agent architecture)

## Development Status

### ✅ Completed Features

**Phase 1: Backend Infrastructure**
- [x] FastAPI backend with RESTful API
- [x] PostgreSQL database with SQLAlchemy ORM
- [x] Docker & Docker Compose setup
- [x] Database migrations with Alembic
- [x] 12-question clinical questionnaire schema

**Phase 2: AI/ML Integration**
- [x] EfficientNet-B7 CNN service (600x600 input)
- [x] Multi-agent architecture (Vision + EASI + Report agents)
- [x] RAG system with Vertex AI embeddings
- [x] Clinical knowledge base integration
- [x] GradCAM saliency map generation
- [x] Differential diagnosis logic

**Phase 3: Frontend Development**
- [x] Flutter web application
- [x] Image upload with file picker
- [x] 12-question questionnaire UI
- [x] Dual report display (user + HCP)
- [x] Auto-polling for results
- [x] Responsive design (max-width 800px)

**Phase 4: GCP Deployment**
- [x] Cloud Storage setup (models + data)
- [x] Cloud SQL PostgreSQL instance
- [x] Artifact Registry repository
- [x] Secret Manager integration
- [x] Cloud Run deployment
- [x] Automated deployment script

### 🚧 Pending Tasks

**Phase 5: Testing & Optimization**
- [ ] End-to-end integration testing
- [ ] Load testing and performance optimization
- [ ] Error handling improvements
- [ ] Logging and monitoring setup
- [ ] Frontend deployment to GCP (Firebase Hosting or Cloud Run)

**Phase 6: Advanced Features**
- [ ] User authentication and authorization
- [ ] Historical tracking dashboard
- [ ] Pre-flare alert system
- [ ] Multi-user support
- [ ] Export reports (PDF)
- [ ] Mobile app (Flutter Android/iOS)

## Testing

### Local API Testing (Without Frontend)

```bash
# Activate virtual environment
cd backend
source venv/bin/activate

# Start the backend
uvicorn app.main:app --reload --port 8000

# In another terminal, run test script
python test_api.py
```

The test script will:
1. Check health endpoint
2. Upload test image + questionnaire
3. Poll for analysis completion
4. Retrieve user report
5. Retrieve HCP report

### Frontend Testing

```bash
cd frontend

# Run tests
flutter test

# Run on web
flutter run -d chrome
```

## References

### Medical Guidelines
- **EASI Scoring**: Official Eczema Area and Severity Index methodology
- **IGA Scoring**: 5-point Investigator's Global Assessment scale
- **Hanifin & Rajka Criteria**: Validated AD diagnostic criteria
- **AAD Guidelines**: American Academy of Dermatology 2023 treatment guidelines

### Existing Skinopathy Infrastructure
- **CNN Model**: Adapted from `~/Desktop/SKINOPATHY/TO_BE_SORTED/CNN/INHOUSE/DB1_2/Trial7/`
- **GradCAM**: Implemented from `~/Desktop/SKINOPATHY/TO_BE_SORTED/CNN_sMap_GuidedSurgery_IP/`
- **Multi-Agent System**: Adapted from `~/Desktop/GIT/psoriasis/` PASI agent architecture

### Academic Sources
- Hanifin JM, Rajka G. Diagnostic features of atopic dermatitis. Acta Derm Venereol Suppl (Stockh). 1980;92:44-7.
- Severity scoring of atopic dermatitis: the SCORAD index. Consensus Report of the European Task Force on Atopic Dermatitis. Dermatology. 1993;186(1):23-31.
- Leshem YA, Hajar T, Hanifin JM, Simpson EL. What the Eczema Area and Severity Index score tells us about the severity of atopic dermatitis: an interpretability study. Br J Dermatol. 2015;172(5):1353-7.

## Security & Privacy

- **Data Encryption**: All data encrypted in transit (HTTPS) and at rest (Cloud Storage encryption)
- **Secret Management**: Database credentials stored in GCP Secret Manager
- **Authentication**: Cloud Run with optional IAM-based authentication
- **HIPAA Consideration**: For production use, enable HIPAA compliance on GCP services
- **Data Retention**: Configurable retention policies for user data

## License

Proprietary - Skinopathy Research Project
© 2025 Skinopathy. All rights reserved.

## Contact & Support

For questions, issues, or contributions:
- **GitHub Issues**: Report bugs or request features
- **Documentation**: Refer to this README and inline code documentation
- **Main Skinopathy Project**: See parent project documentation

## Acknowledgments

- **TensorFlow**: EfficientNet-B7 implementation
- **Google Cloud**: Vertex AI and managed infrastructure
- **LangChain**: Multi-agent framework
- **Flutter**: Cross-platform UI framework
- **FastAPI**: Modern Python web framework
