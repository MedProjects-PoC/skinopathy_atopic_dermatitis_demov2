# Changelog

All notable changes to the Skinopathy Atopic Dermatitis v2 system are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.1] - 2025-12-09 - DOCUMENTATION CLEANUP

### Changed
- **Clarified GradCAM/Saliency Map Status**: Documentation now accurately reflects that activation channel visualization is a pending feature, not implemented
- **Removed misleading references** to GradCAM from:
  - `README.md` (architecture, pipeline, tech stack, references, completed features)
  - `API_DOCUMENTATION.md` (response schema, analysis pipeline, examples)
  - `backend/app/services/analysis_service_multiagent.py` (pipeline documentation, saliency map path creation)

### Removed
- **GradCAM references** from feature list (was noted as HCP feature but not implemented)
- **`saliency_map_path` field** from AIResult database model creation
- **`saliency_map_metrics` dictionary** from HCP report schema
- **"Fast Activation Map" step** from analysis pipeline documentation
- **PyTorch dependency reference** (was listed for GradCAM but not actually used)
- **References to gradcam_service.py** (file doesn't exist, was only referenced in .pyc)

### Rationale
The codebase previously claimed GradCAM saliency map generation was implemented, but the actual implementation was missing. A `gradcam_service.py` file was never created (only a compiled `.pyc` exists), and no saliency maps were actually being generated. This cleanup clarifies the current state and documents activation channel visualization as a future enhancement rather than a completed feature.

### Technical Details
- The `saliency_map_path` was created in `AIResult` but never populated with actual generated images
- Analysis pipeline comment referenced "Activation Map Saliency Maps" as step 5 but this step never executed
- HCP reports included empty `saliency_map_metrics` that duplicated Vision AI lesion/erythema findings
- Documentation listed GradCAM as completed feature but implementation was not present

### Future Work
Activation channel visualization from the EfficientNet-B7 model remains as a pending enhancement for future implementation when prioritized.

---

## [2.0.0] - 2024-12-07 - STREAMLINED ARCHITECTURE

### Major Changes
This is a **significant architectural simplification** focused on speed, cost, and maintainability. The system was streamlined from a 3-agent architecture to a 2-agent architecture with 60-70% performance improvement.

### Added
- **EXPERIMENTS.md**: Comprehensive documentation of all failed experiments and lessons learned
- **Parallel execution** of CNN + Vision AI using `asyncio.gather()`
- **Integrated SOAP note generation** directly in `analysis_service_multiagent.py`
- **Simplified reporting system** focusing on actionable insights
- **Background saliency map generation** (non-blocking)

### Changed
- **Pipeline simplified from 5 steps to 3 steps**:
  - Step 1: CNN + Vision AI (parallel)
  - Step 2: Save AI results
  - Step 3: Generate reports
- **Processing time: 2-3 minutes** (down from 7-9 minutes with EASI agent)
- **Cost per assessment: ~$0.01** (66% reduction from 3-agent architecture)
- **File structure cleaned up**: Removed 8 unused/experimental files
- **README.md updated** to reflect v2.0 streamlined architecture
- **API cost estimates updated** to reflect 2-agent system

### Removed
- **EASI Scoring Agent** (primary performance bottleneck - see EXPERIMENTS.md for details)
  - Removed `backend/app/agents/easi_agent.py`
  - Removed `backend/app/prompts/easi_agent_prompts.py`
  - Reason: Added 3-5 minutes to processing, redundant with CNN severity scores for MVP
  - User feedback: Requested faster, simpler results
- **VLM Service Layer** (over-engineered abstraction)
  - Removed `backend/app/services/vlm_service.py`
  - Reason: Only ever used Gemini, abstraction added complexity without value
- **Clinical Note Service** (unnecessary separation)
  - Removed `backend/app/services/clinical_note_service.py`
  - Reason: Simple SOAP note generation better integrated inline
- **Activation Map Service** (experimental visualization)
  - Removed `backend/app/services/activation_map_service.py`
  - Reason: Standard GradCAM approach sufficient and well-understood
- **Old Analysis Service** (replaced by multiagent version)
  - Removed `backend/app/services/analysis_service.py`
  - Reason: Sequential processing, not parallel
- **Duplicate GCP Config** (consolidated)
  - Removed `backend/app/core/config_gcp.py`
  - Reason: Main config.py handles GCP detection automatically
- **Old Vision Agent Prompts** (cleanup)
  - Removed `backend/app/prompts/vision_agent_prompts_OLD.py`
  - Reason: Backup file, no longer needed
- **EASI agent imports** from `backend/app/agents/__init__.py`

### Performance Improvements
| Metric | Before (v1.x) | After (v2.0) | Improvement |
|--------|---------------|--------------|-------------|
| **Total Processing Time** | 7-9 minutes | 2-3 minutes | **60-70%** |
| **Agent Count** | 3 (CNN+Vision+EASI) | 2 (CNN+Vision) | -33% |
| **Gemini API Calls** | 2-3 per analysis | 1 per analysis | -50 to -66% |
| **Cost per Assessment** | ~$0.015-0.02 | ~$0.01 | -33 to -50% |
| **Code Complexity** | 8+ service files | 4 service files | -50% |

### Fixed
- N/A (no bugs fixed in this release, focus was architectural cleanup)

### Deployment
- **Cloud Run revision**: 00019-lh9
- **Region**: us-central1
- **CPU**: 4 vCPU
- **Memory**: 8 GiB
- **Min Instances**: 1 (always-warm)

---

## [1.2.0] - 2024-12-06 - DATABASE SESSION FIX

### Fixed
- **Critical: Background task database session management**
  - Issue: Background analysis tasks were using request-scoped database sessions that closed prematurely
  - Fix: Create dedicated `SessionLocal()` instance for background tasks in `analysis_service_multiagent.py`
  - Impact: Eliminated "InterfaceError: connection already closed" errors
  - Files changed:
    - `backend/app/services/analysis_service_multiagent.py` (lines 36-38, 169-170)

### Changed
- Database session lifecycle properly managed for async background tasks
- Explicit `db.close()` in `finally` block to ensure cleanup

---

## [1.1.0] - 2024-12-05 - PARALLEL EXECUTION OPTIMIZATION

### Added
- **Parallel execution of CNN and Vision Agent** using `asyncio.gather()`
- **Background GradCAM generation** using `asyncio.to_thread()`
- Performance monitoring and logging improvements

### Changed
- Pipeline steps reduced from 5 to 3 (major simplification):
  - Old: CNN → Vision → EASI → Reports → GradCAM
  - New: (CNN + Vision in parallel) → Save Results → Reports (GradCAM in background)
- Processing time reduced from 8-10 minutes to ~4 minutes (60% improvement)

### Technical Details
- Used `asyncio.to_thread()` for CPU-bound CNN operations
- Used `asyncio.gather()` for concurrent task execution
- GradCAM moved to non-blocking background generation

---

## [1.0.0] - 2024-11-28 - INITIAL MULTI-AGENT RELEASE

### Added - Core Features
- **Multi-agent AI architecture** with LangChain orchestration:
  - CNN Agent (EfficientNet-B7)
  - Vision Agent (Gemini 1.5 Pro + RAG)
  - EASI Agent (Gemini 1.5 Pro + RAG)
- **RAG system** with Vertex AI embeddings (text-embedding-005)
- **Clinical knowledge base** (6 documents):
  - Hanifin & Rajka diagnostic criteria
  - EASI scoring system
  - IGA guidelines
  - Differential diagnosis guide
  - Treatment guidelines (AAD 2023)
  - Pre-flare detection patterns
- **Dual reporting system**:
  - User-friendly reports
  - HCP clinical reports with EASI scores
- **GradCAM saliency maps** for AI explainability
- **12-question clinical questionnaire** covering diagnostic criteria, clinical data, and lifestyle management

### Added - Backend Infrastructure
- FastAPI backend with RESTful API
- PostgreSQL database with SQLAlchemy ORM
- Docker & Docker Compose setup
- Alembic database migrations
- Background task processing with asyncio

### Added - Frontend
- Flutter web application
- Image upload with file picker
- Interactive questionnaire UI
- Dual report display
- Auto-polling for results
- Responsive design (max-width 800px)

### Added - Cloud Infrastructure
- Google Cloud Platform deployment:
  - Cloud Run (serverless containers)
  - Cloud SQL (PostgreSQL 15)
  - Cloud Storage (models + data)
  - Artifact Registry (Docker images)
  - Secret Manager (credentials)
  - Vertex AI (Gemini + embeddings)

### Technical Stack
- **Backend**: FastAPI 0.110.0, Python 3.11, SQLAlchemy 2.0.25
- **AI/ML**: TensorFlow 2.15.0, PyTorch 2.1.2, LangChain 0.2.16
- **Vision Models**: Gemini 1.5 Pro, Gemini 2.5 Flash (later upgrade)
- **Frontend**: Flutter 3.24.5, Dart 3.x
- **Infrastructure**: Docker, GCP (Cloud Run, Cloud SQL, Vertex AI)

---

## [0.9.0] - 2024-11-20 - BETA TESTING PHASE

### Added - Experimental Features (Later Removed)
These features were tested but ultimately removed in v2.0. See EXPERIMENTS.md for details.

- **Two-stage analysis pipeline** (abandoned)
  - Stage 1: Quick CNN preview
  - Stage 2: Deep analysis with all agents
  - Reason for removal: Added complexity without clear benefit, confused users

- **Activation channel maps** (replaced)
  - Alternative to GradCAM for saliency visualization
  - Reason for removal: No clear advantage over standard GradCAM

- **Custom PostgreSQL optimizations** (reverted)
  - Custom indexes and materialized views
  - Reason for removal: Database wasn't the bottleneck (API calls were 95% of latency)

- **VLM service abstraction layer** (deprecated)
  - Support for multiple vision model providers (Qwen, Gemini)
  - Reason for removal: Only Gemini used in production, abstraction unnecessary

- **Separate clinical note service** (removed)
  - Dedicated service for SOAP note generation
  - Reason for removal: Simple enough to inline, no benefit from separation

### Technical Learnings
- Identified that API latency (Gemini calls) was the primary bottleneck, not database
- User feedback indicated preference for speed over comprehensive EASI scoring
- Simpler architecture easier to maintain and debug

---

## [0.5.0] - 2024-11-10 - PROOF OF CONCEPT

### Added
- Initial CNN model integration (EfficientNet-B7)
- Basic Gemini API integration
- Simple Flask API prototype
- Database schema design
- Basic image upload functionality

### Technical Details
- Adapted CNN from existing Skinopathy research: `~/Desktop/SKINOPATHY/TO_BE_SORTED/CNN/INHOUSE/DB1_2/Trial7/`
- GradCAM implementation from: `~/Desktop/SKINOPATHY/TO_BE_SORTED/CNN_sMap_GuidedSurgery_IP/`
- Multi-agent pattern adapted from psoriasis PASI agent architecture

---

## Development Principles & Lessons Learned

Based on the experimental journey documented in EXPERIMENTS.md:

1. **Speed > Completeness** for user engagement - Users prefer fast, actionable results over comprehensive clinical scores
2. **Simple > Clever** for maintainability - Straightforward code is easier to debug and extend
3. **Measure first**, optimize second - Database wasn't the bottleneck; Gemini API calls were
4. **YAGNI (You Aren't Gonna Need It)** - Don't build for flexibility you don't need (e.g., VLM abstraction)
5. **Listen to users** - Direct feedback led to EASI removal and 60-70% speedup
6. **Parallel processing matters** - `asyncio.gather()` gave significant speedup
7. **Good enough is perfect** for MVP scope - Standard GradCAM beats experimental approaches
8. **Commit to good tools** - Gemini works well; stop hedging with abstractions
9. **Managed services handle optimization** - Cloud SQL, Cloud Run handle scale automatically
10. **Document failures** - EXPERIMENTS.md exists because learning from failures is valuable

---

## Upgrade Guide

### From v1.x to v2.0

**Code Changes:**
- EASI agent removed: Update any code referencing `easi_agent` or `EASIReasoningAgent`
- Report schema changed: HCP reports no longer include `easi_score` field
- New report fields: `cnn_severity`, `lesion_count`, `erythema_percentage`, `soap_note`

**API Changes:**
- `/api/v1/reports/hcp/{session_id}` response schema updated (see README.md)
- Processing time reduced: Update any timeout configurations to expect 2-3 minutes instead of 7-9 minutes

**Performance:**
- 60-70% faster processing
- 33-50% lower cost per assessment
- Simpler error handling (fewer API calls = fewer failure points)

**No Breaking Changes:**
- Upload endpoint remains unchanged
- User report schema remains backward compatible
- Database migrations handle schema updates automatically

---

## Future Roadmap

### Considered for v2.1+
- **EASI scoring** as optional deep analysis for research users (opt-in, non-blocking)
- **Two-stage analysis** with better UX ("Quick result ready, detailed analysis in progress")
- **Advanced visualizations** if user base requests it (A/B test different approaches)
- **Database optimization** only if scale requires (current setup handles 100s of concurrent users)

### Planned Features
- User authentication and authorization
- Historical tracking dashboard
- Pre-flare alert system
- Multi-user support
- PDF report export
- Mobile app (Flutter Android/iOS)
- Load testing and performance benchmarking
- Comprehensive integration tests

---

## References

- **EXPERIMENTS.md**: Detailed analysis of failed experiments and lessons learned
- **README.md**: Current system architecture and deployment guide
- **Cloud Run Revision**: 00019-lh9 (production deployment)
- **GCP Project**: total-furnace-288818

---

**Last Updated**: December 7, 2024
**Current Version**: v2.0.0 (Streamlined)
**Status**: Production-ready, deployed to Cloud Run
