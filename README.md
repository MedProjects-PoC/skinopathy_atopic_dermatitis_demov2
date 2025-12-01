# Skinopathy-AtopicDermatitis-Demov2

AI-powered Atopic Dermatitis monitoring application with dual reporting (user/HCP) and pre-flare detection capabilities.

## Overview

This application combines:
- **CNN (EfficientNet-B7)** for AD severity assessment
- **Vision Language Model (QWEN 2.5-VL-7B)** for intelligent dual report generation
- **GradCAM** for saliency map visualization (HCP feature)
- **Tracking dashboard** with pre-flare detection algorithms

## Architecture

```
skinopathy_atopic_dermatitis_demov2/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/v1/      # API endpoints
│   │   ├── services/    # Business logic & AI services
│   │   ├── models/      # Database models & schemas
│   │   └── core/        # Configuration
│   ├── ml_models/       # ML models storage
│   └── storage/         # Image & saliency map storage
├── flutter_frontend/    # Flutter web app (TBD)
└── docker-compose.yml   # Docker orchestration
```

## Features

### Phase 1 (MVP) - In Progress
- [x] FastAPI backend skeleton
- [x] PostgreSQL database schema
- [x] Image upload & questionnaire endpoint
- [ ] EfficientNet-B7 CNN integration
- [ ] QWEN VLM integration
- [ ] Basic user report generation

### Phase 2 (Planned)
- [ ] GradCAM saliency maps
- [ ] Dual reports (user + HCP)
- [ ] Role-based access

### Phase 3 (Planned)
- [ ] Tracking dashboard
- [ ] Pre-flare detection algorithm
- [ ] Historical trend analysis

### Phase 4 (Planned)
- [ ] Flutter web frontend
- [ ] Complete Docker deployment
- [ ] End-to-end testing

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)

### Using Docker (Recommended)

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

### Local Development (Backend Only)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start PostgreSQL (using Docker)
docker run -d -p 5432:5432 \
  -e POSTGRES_DB=skinopathy_ad \
  -e POSTGRES_USER=skinopathy \
  -e POSTGRES_PASSWORD=demo_password \
  postgres:15-alpine

# Run the application
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Upload
`POST /api/v1/upload/`
- Upload skin image + AD questionnaire
- Returns session_id for tracking

### Analysis
`GET /api/v1/analysis/{session_id}`
- Get CNN analysis results
- Returns severity scores, saliency map URL

### Reports
`GET /api/v1/reports/{session_id}?type=user|hcp`
- Get user-friendly or HCP report
- VLM-generated insights and recommendations

### Tracking
`GET /api/v1/tracking/{user_id}`
- Get historical data and trends
- Pre-flare alerts and statistics

## Database Schema

Key tables:
- **users** - User accounts (user/HCP roles)
- **sessions** - Analysis sessions (image + timestamp)
- **questionnaires** - AD-specific questionnaire responses
- **ai_results** - CNN analysis results
- **reports** - Dual reports (user/HCP)
- **alerts** - Pre-flare warnings and notifications

## Technology Stack

### Backend
- **FastAPI** 0.110+ - Modern Python web framework
- **PostgreSQL** 15+ - Relational database
- **SQLAlchemy** 2.0+ - ORM
- **Pydantic** 2.6+ - Data validation

### AI/ML
- **TensorFlow** 2.15 - CNN inference
- **PyTorch** 2.1 - GradCAM implementation
- **Transformers** 4.37 - QWEN VLM
- **OpenCV** - Image processing

### Infrastructure
- **Docker** & **Docker Compose** - Containerization
- **Redis** - Caching (optional)
- **Nginx** - Static file serving

## ML Models

### EfficientNet-B7 (CNN)
- Path: `/app/ml_models/efficientnet_b7_ad.h5`
- Input: 224x224 RGB images
- Outputs: Severity scores, body region distribution, flare status

### QWEN 2.5-VL-7B (VLM)
- Path: `/app/ml_models/qwen`
- Purpose: Dual report generation (user/HCP)
- Fallback: OpenAI GPT-4V (requires API key)

### GradCAM
- Layer: `top_conv`
- Purpose: Visual attention maps for HCPs
- Alpha: 0.4 (overlay transparency)

## Development Status

**Current Phase:** Phase 1 - MVP
**Status:** Backend skeleton complete, AI services in progress

Next steps:
1. Integrate EfficientNet-B7 from existing Skinopathy codebase
2. Setup QWEN VLM for report generation
3. Implement GradCAM service
4. Test end-to-end flow

## References

Leverages existing Skinopathy infrastructure:
- EfficientNet-B7 model: `~/Desktop/SKINOPATHY/TO_BE_SORTED/CNN/INHOUSE/DB1_2/Trial7/`
- GradCAM implementation: `~/Desktop/SKINOPATHY/TO_BE_SORTED/CNN_sMap_GuidedSurgery_IP/`
- QWEN VLM code: `~/Desktop/SKINOPATHY/MultiModal_AI/ALL_CODES_RJ/QWEN2_5_3_7B_SKINLESION_March2025.ipynb`

## License

Proprietary - Skinopathy Research Project

## Contact

For questions or issues, please refer to the main Skinopathy documentation.
