# GCP Deployment Guide - Skinopathy AD Demo

Complete guide for deploying the Skinopathy Atopic Dermatitis Demo application to Google Cloud Platform.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Deployment Process](#deployment-process)
- [Configuration](#configuration)
- [Post-Deployment](#post-deployment)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Prerequisites

### Required Tools
- **Google Cloud SDK**: gcloud CLI installed and configured
- **Docker**: For local testing and building images
- **Git**: For version control
- **Python 3.11+**: For local development and testing

### GCP Project Setup
- **Project ID**: `total-furnace-288818`
- **Region**: `us-central1` (Iowa - cost-effective with good performance)
- **Billing**: Enabled and linked to project

### Required APIs
Enable the following APIs in your GCP project:
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

## Initial Setup

### 1. Install Google Cloud SDK

#### Download and Extract
```bash
# Download to Desktop
cd ~/Desktop
# Assume gcloud tar.gz is already downloaded

# Extract
tar -xzf google-cloud-sdk-*.tar.gz

# Install
cd google-cloud-sdk
./install.sh

# Initialize PATH (add to ~/.zshrc or ~/.bash_profile)
source ~/Desktop/google-cloud-sdk/path.zsh.inc
source ~/Desktop/google-cloud-sdk/completion.zsh.inc
```

#### Authenticate and Configure
```bash
# Login to GCP
gcloud auth login
# This will open browser for authentication

# Set project
gcloud config set project total-furnace-288818

# Set default region
gcloud config set compute/region us-central1
gcloud config set run/region us-central1

# Verify configuration
gcloud config list
```

### 2. Create Service Account

```bash
# Create service account for deployment
gcloud iam service-accounts create skinopathy-ad-deployer \
    --description="Service account for Skinopathy AD deployment" \
    --display-name="Skinopathy AD Deployer"

# Grant necessary roles
gcloud projects add-iam-policy-binding total-furnace-288818 \
    --member="serviceAccount:skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding total-furnace-288818 \
    --member="serviceAccount:skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com" \
    --role="roles/cloudsql.admin"

gcloud projects add-iam-policy-binding total-furnace-288818 \
    --member="serviceAccount:skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding total-furnace-288818 \
    --member="serviceAccount:skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding total-furnace-288818 \
    --member="serviceAccount:skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com" \
    --role="roles/secretmanager.admin"

gcloud projects add-iam-policy-binding total-furnace-288818 \
    --member="serviceAccount:skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Generate and download credentials
gcloud iam service-accounts keys create ~/Desktop/gcp-credentials.json \
    --iam-account=skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com

# Set application default credentials
export GOOGLE_APPLICATION_CREDENTIALS=~/Desktop/gcp-credentials.json
```

### 3. Upload ML Model to Cloud Storage

```bash
# Create models bucket (done automatically by deploy-gcp.sh, but can be done manually)
gcloud storage buckets create gs://total-furnace-288818-models \
    --location=us-central1

# Upload EfficientNet-B7 model (457.9 MB)
# From existing Skinopathy project
gcloud storage cp \
    ~/Desktop/SKINOPATHY/TO_BE_SORTED/CNN/INHOUSE/DB1_2/Trial7/efficientnet_b7_ad.h5 \
    gs://total-furnace-288818-models/efficientnet_b7_ad.h5

# Verify upload
gcloud storage ls gs://total-furnace-288818-models/
```

## Deployment Process

### Automated Deployment (Recommended)

The project includes an automated deployment script that handles all steps:

```bash
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2
./deploy-gcp.sh
```

The script performs the following steps:

#### Step 1: Authentication Check
- Verifies gcloud authentication
- Confirms project is set to `total-furnace-288818`

#### Step 2: Cloud Storage Setup
- Creates `total-furnace-288818-models` bucket
- Creates `total-furnace-288818-skinopathy-data` bucket
- Sets appropriate permissions

#### Step 3: Artifact Registry
- Creates Docker repository: `skinopathy-ad-repo`
- Configures Docker credential helper

#### Step 4: Cloud SQL Database
- Creates PostgreSQL 15 instance: `skinopathy-ad-db`
- Tier: `db-f1-micro` (1 vCPU, 614 MB RAM)
- Disk: 10 GB SSD
- Backups: Enabled
- Private IP: Disabled (can be enabled later)

**Note**: This step takes 10-15 minutes

#### Step 5: Database Configuration
- Creates database: `skinopathy_ad`
- Creates user: `skinopathy`
- Generates secure random password
- Displays password (save it!)

#### Step 6: Secret Manager
- Stores database connection string in Secret Manager
- Secret name: `skinopathy-ad-db-connection`
- Grants Cloud Run service account access

#### Step 7: Docker Build
- Builds Docker image using Cloud Build
- Base image: `tensorflow/tensorflow:2.15.0`
- Installs all Python dependencies
- Pushes to Artifact Registry

**Note**: This step takes 15-20 minutes (large TensorFlow image)

#### Step 8: Cloud Run Deployment
- Deploys container to Cloud Run
- Service name: `skinopathy-ad-api`
- Memory: 2 GiB
- CPU: 2
- Port: 8080
- Environment variables configured
- Cloud SQL connection enabled
- Unauthenticated access allowed (can be restricted later)

#### Step 9: Display Service URL
- Shows the public URL for the API
- Example: `https://skinopathy-ad-api-<hash>-uc.a.run.app`

### Manual Deployment Steps

If you need to deploy manually or troubleshoot:

#### 1. Build Docker Image Locally
```bash
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2/backend

# Build image
docker build -t skinopathy-ad-api:latest .

# Test locally
docker run -p 8080:8080 \
    -e PORT=8080 \
    -e ENVIRONMENT=development \
    skinopathy-ad-api:latest
```

#### 2. Push to Artifact Registry
```bash
# Tag image
docker tag skinopathy-ad-api:latest \
    us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad-repo/skinopathy-ad-api:latest

# Push
docker push us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad-repo/skinopathy-ad-api:latest
```

#### 3. Deploy to Cloud Run
```bash
gcloud run deploy skinopathy-ad-api \
    --image us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad-repo/skinopathy-ad-api:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 10 \
    --port 8080 \
    --set-env-vars "PORT=8080,ENVIRONMENT=production,GCP_PROJECT_ID=total-furnace-288818,GCP_REGION=us-central1,MODELS_BUCKET=total-furnace-288818-models,DATA_BUCKET=total-furnace-288818-skinopathy-data,CNN_MODEL_PATH=gs://total-furnace-288818-models/efficientnet_b7_ad.h5" \
    --add-cloudsql-instances total-furnace-288818:us-central1:skinopathy-ad-db \
    --service-account skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com
```

## Configuration

### Environment Variables

The following environment variables are configured in Cloud Run:

| Variable | Value | Description |
|----------|-------|-------------|
| `PORT` | 8080 | Cloud Run expects port 8080 |
| `ENVIRONMENT` | production | Runtime environment |
| `GCP_PROJECT_ID` | total-furnace-288818 | GCP project identifier |
| `GCP_REGION` | us-central1 | Deployment region |
| `MODELS_BUCKET` | total-furnace-288818-models | Cloud Storage bucket for ML models |
| `DATA_BUCKET` | total-furnace-288818-skinopathy-data | Bucket for user images & saliency maps |
| `CNN_MODEL_PATH` | gs://total-furnace-288818-models/efficientnet_b7_ad.h5 | Path to CNN model |

### Database Connection

Cloud Run connects to Cloud SQL via Unix socket:
```
/cloudsql/total-furnace-288818:us-central1:skinopathy-ad-db
```

Connection string is stored in Secret Manager:
```bash
# View secret (requires secretmanager.admin role)
gcloud secrets versions access latest --secret="skinopathy-ad-db-connection"
```

### Service Account Permissions

The Cloud Run service uses `skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com` with:
- Cloud SQL Client role (database access)
- Storage Object Admin role (read/write to buckets)
- Vertex AI User role (Gemini API access)
- Secret Manager Secret Accessor role (read secrets)

## Post-Deployment

### 1. Verify Deployment

#### Check Health Endpoint
```bash
# Get service URL
export SERVICE_URL=$(gcloud run services describe skinopathy-ad-api \
    --region us-central1 \
    --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health
# Expected: {"status": "healthy"}
```

#### Check API Documentation
Open in browser:
```
https://skinopathy-ad-api-<hash>-uc.a.run.app/api/v1/docs
```

### 2. Run Database Migrations

Connect to Cloud SQL and run migrations:

```bash
# Install Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.arm64
chmod +x cloud-sql-proxy

# Start proxy
./cloud-sql-proxy total-furnace-288818:us-central1:skinopathy-ad-db &

# In another terminal, run migrations
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2/backend
source venv/bin/activate

# Configure local connection
export DATABASE_URL="postgresql://skinopathy:<password>@127.0.0.1:5432/skinopathy_ad"

# Run migrations
alembic upgrade head
```

### 3. Test Full Pipeline

```bash
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2

# Update test_api.py with production URL
# Edit line: BASE_URL = os.getenv('API_URL', 'http://localhost:8000')

# Run test
export API_URL=$SERVICE_URL
python test_api.py
```

### 4. Update Flutter Frontend

Update the Flutter app to use the production API:

```dart
// frontend/lib/services/api_service.dart
class ApiService {
  // Change from localhost to production URL
  static const String baseUrl = 'https://skinopathy-ad-api-<hash>-uc.a.run.app/api/v1';

  // ... rest of code
}
```

### 5. Deploy Flutter Web App

#### Option A: Firebase Hosting (Recommended)
```bash
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2/frontend

# Build for web
flutter build web

# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize
firebase init hosting
# Select: total-furnace-288818
# Public directory: build/web
# Single-page app: Yes
# GitHub integration: No

# Deploy
firebase deploy --only hosting
```

#### Option B: Cloud Run (Static Site)
```bash
# Create simple Nginx Dockerfile in frontend/
cat > Dockerfile << 'EOF'
FROM nginx:alpine
COPY build/web /usr/share/nginx/html
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOF

# Build Flutter web
flutter build web

# Build and deploy
gcloud run deploy skinopathy-ad-web \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080
```

## Troubleshooting

### Issue: Cloud Build Timeout
**Symptom**: Build exceeds 10-minute default timeout
**Solution**: Increase timeout in deploy-gcp.sh:
```bash
gcloud builds submit --timeout=30m ...
```

### Issue: Cloud Run Cold Start
**Symptom**: First request after idle period takes 30-60 seconds
**Solutions**:
1. Set min-instances to 1 (costs more):
   ```bash
   gcloud run services update skinopathy-ad-api \
       --region us-central1 \
       --min-instances 1
   ```
2. Use startup CPU boost:
   ```bash
   gcloud run services update skinopathy-ad-api \
       --region us-central1 \
       --cpu-boost
   ```

### Issue: Out of Memory
**Symptom**: Container crashes with OOM error
**Solution**: Increase memory allocation:
```bash
gcloud run services update skinopathy-ad-api \
    --region us-central1 \
    --memory 4Gi
```

### Issue: CNN Model Download Fails
**Symptom**: Error loading model from GCS
**Solutions**:
1. Verify model exists:
   ```bash
   gcloud storage ls gs://total-furnace-288818-models/
   ```
2. Check service account permissions:
   ```bash
   gcloud storage buckets get-iam-policy gs://total-furnace-288818-models
   ```
3. Re-upload model:
   ```bash
   gcloud storage cp local_model.h5 gs://total-furnace-288818-models/efficientnet_b7_ad.h5
   ```

### Issue: Database Connection Failed
**Symptom**: Cannot connect to Cloud SQL
**Solutions**:
1. Verify Cloud SQL instance is running:
   ```bash
   gcloud sql instances describe skinopathy-ad-db
   ```
2. Check Cloud Run has Cloud SQL connection configured:
   ```bash
   gcloud run services describe skinopathy-ad-api \
       --region us-central1 \
       --format yaml | grep cloudsql
   ```
3. Verify credentials in Secret Manager

### Issue: Vertex AI Permission Denied
**Symptom**: Cannot access Gemini API
**Solution**: Grant Vertex AI User role to service account:
```bash
gcloud projects add-iam-policy-binding total-furnace-288818 \
    --member="serviceAccount:skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

## Maintenance

### Viewing Logs
```bash
# Real-time logs
gcloud run services logs tail skinopathy-ad-api --region us-central1

# Filter by severity
gcloud run services logs read skinopathy-ad-api \
    --region us-central1 \
    --filter="severity>=WARNING"

# Export to file
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=skinopathy-ad-api" \
    --limit 1000 \
    --format json > logs.json
```

### Monitoring
```bash
# Get service metrics
gcloud run services describe skinopathy-ad-api \
    --region us-central1 \
    --format yaml

# View in Cloud Console
# https://console.cloud.google.com/run/detail/us-central1/skinopathy-ad-api/metrics
```

### Updating the Service

#### Update Code
```bash
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2

# Make code changes

# Rebuild and redeploy
./deploy-gcp.sh
# Or manually:
gcloud builds submit --tag us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad-repo/skinopathy-ad-api:latest backend/
gcloud run deploy skinopathy-ad-api --image us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad-repo/skinopathy-ad-api:latest --region us-central1
```

#### Update Environment Variables
```bash
gcloud run services update skinopathy-ad-api \
    --region us-central1 \
    --update-env-vars "NEW_VAR=value"
```

#### Update Resource Allocation
```bash
# Increase memory
gcloud run services update skinopathy-ad-api \
    --region us-central1 \
    --memory 4Gi

# Add more CPUs
gcloud run services update skinopathy-ad-api \
    --region us-central1 \
    --cpu 4
```

### Database Backups

Cloud SQL automatically creates daily backups. To create manual backup:
```bash
gcloud sql backups create \
    --instance skinopathy-ad-db \
    --description "Manual backup before major update"
```

### Scaling Configuration

```bash
# Set autoscaling limits
gcloud run services update skinopathy-ad-api \
    --region us-central1 \
    --min-instances 1 \
    --max-instances 20
```

### Cost Optimization

#### Monitor Costs
```bash
# View billing for project
gcloud billing projects describe total-furnace-288818

# View detailed costs in console:
# https://console.cloud.google.com/billing/
```

#### Reduce Costs
1. **Use min-instances=0**: Only pay when service is used
2. **Reduce memory allocation**: Start with 2Gi, increase only if needed
3. **Use Gemini 1.5 Flash**: For less critical analysis steps
4. **Implement caching**: Cache common RAG queries
5. **Optimize model size**: Consider quantized CNN model

### Security Hardening

#### Enable Authentication
```bash
# Remove public access
gcloud run services update skinopathy-ad-api \
    --region us-central1 \
    --no-allow-unauthenticated

# Access requires authentication
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SERVICE_URL/health
```

#### Enable HTTPS Only
```bash
# Cloud Run uses HTTPS by default, but enforce:
gcloud run services update skinopathy-ad-api \
    --region us-central1 \
    --ingress all
```

#### Rotate Secrets
```bash
# Create new database password
NEW_PASSWORD=$(openssl rand -base64 32)

# Update Cloud SQL user
gcloud sql users set-password skinopathy \
    --instance skinopathy-ad-db \
    --password $NEW_PASSWORD

# Update secret
gcloud secrets versions add skinopathy-ad-db-connection \
    --data-file=- <<< "postgresql://skinopathy:$NEW_PASSWORD@/skinopathy_ad?host=/cloudsql/total-furnace-288818:us-central1:skinopathy-ad-db"

# Restart service to pick up new secret
gcloud run services update skinopathy-ad-api --region us-central1
```

## Reference Links

- **Cloud Run Documentation**: https://cloud.google.com/run/docs
- **Cloud SQL Documentation**: https://cloud.google.com/sql/docs
- **Vertex AI Documentation**: https://cloud.google.com/vertex-ai/docs
- **Cloud Build Documentation**: https://cloud.google.com/build/docs
- **GCP Pricing Calculator**: https://cloud.google.com/products/calculator

## Support

For deployment issues specific to this project, check:
1. GitHub Issues (if repository is public)
2. Main README.md troubleshooting section
3. Cloud Console logs and error messages
4. GCP support (if you have a support plan)
