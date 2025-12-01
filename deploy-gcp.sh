#!/bin/bash
# GCP Deployment Script for Skinopathy AD Demo v2
# Project: total-furnace-288818
# Region: us-central1

set -e  # Exit on error

PROJECT_ID="total-furnace-288818"
REGION="us-central1"
SERVICE_NAME="skinopathy-ad-api"
SERVICE_ACCOUNT="skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com"

# Storage buckets
MODELS_BUCKET="${PROJECT_ID}-models"
DATA_BUCKET="${PROJECT_ID}-skinopathy-data"

# Cloud SQL
SQL_INSTANCE_NAME="skinopathy-ad-db"
DB_NAME="skinopathy_ad"
DB_USER="skinopathy"

# Artifact Registry
REPO_NAME="skinopathy-ad"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"

echo "=================================================="
echo "  Skinopathy AD Demo - GCP Deployment Script"
echo "=================================================="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check if gcloud is authenticated
echo "[1/9] Checking authentication..."
gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 || {
    echo "Error: Not authenticated. Run 'gcloud auth login' first."
    exit 1
}

# Set project
echo "[2/9] Setting project..."
gcloud config set project ${PROJECT_ID}

# Create Storage Buckets
echo "[3/9] Creating Cloud Storage buckets..."
gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${REGION} gs://${MODELS_BUCKET}/ 2>/dev/null || echo "Models bucket already exists"
gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${REGION} gs://${DATA_BUCKET}/ 2>/dev/null || echo "Data bucket already exists"

# Set bucket permissions
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:objectAdmin gs://${MODELS_BUCKET}/
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:objectAdmin gs://${DATA_BUCKET}/

echo "✓ Buckets created: ${MODELS_BUCKET}, ${DATA_BUCKET}"

# Create Artifact Registry repository
echo "[4/9] Creating Artifact Registry repository..."
gcloud artifacts repositories create ${REPO_NAME} \
    --repository-format=docker \
    --location=${REGION} \
    --description="Skinopathy AD Docker images" 2>/dev/null || echo "Repository already exists"

echo "✓ Artifact Registry ready"

# Create Cloud SQL instance (this takes ~10 minutes)
echo "[5/9] Creating Cloud SQL instance (this may take 10+ minutes)..."
gcloud sql instances create ${SQL_INSTANCE_NAME} \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=${REGION} \
    --root-password=$(openssl rand -base64 32) \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    --storage-type=SSD \
    --storage-size=10GB 2>/dev/null || echo "SQL instance already exists"

# Wait for instance to be ready
echo "Waiting for SQL instance to be ready..."
gcloud sql operations wait $(gcloud sql operations list --instance=${SQL_INSTANCE_NAME} --limit=1 --format="value(name)") --project=${PROJECT_ID} 2>/dev/null || true

# Create database and user
echo "[6/9] Creating database and user..."
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql databases create ${DB_NAME} --instance=${SQL_INSTANCE_NAME} 2>/dev/null || echo "Database already exists"
gcloud sql users create ${DB_USER} --instance=${SQL_INSTANCE_NAME} --password=${DB_PASSWORD} 2>/dev/null || echo "User already exists"

echo "✓ Cloud SQL ready: ${SQL_INSTANCE_NAME}"
echo "  Database: ${DB_NAME}"
echo "  User: ${DB_USER}"
echo "  Password: ${DB_PASSWORD}"
echo ""
echo "⚠️  IMPORTANT: Save this password! It won't be shown again."
echo ""

# Store connection info in Secret Manager
echo "[7/9] Storing secrets in Secret Manager..."
CONNECTION_STRING="postgresql://${DB_USER}:${DB_PASSWORD}@/cloudsql/${PROJECT_ID}:${REGION}:${SQL_INSTANCE_NAME}/${DB_NAME}"

echo -n "${CONNECTION_STRING}" | gcloud secrets create skinopathy-ad-db-connection \
    --data-file=- \
    --replication-policy="automatic" 2>/dev/null || {
    echo "Secret already exists, updating..."
    echo -n "${CONNECTION_STRING}" | gcloud secrets versions add skinopathy-ad-db-connection --data-file=-
}

# Grant service account access to secret
gcloud secrets add-iam-policy-binding skinopathy-ad-db-connection \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

echo "✓ Secrets stored"

# Build and push Docker image
echo "[8/9] Building and pushing Docker image..."
cd backend

# Configure Docker to use gcloud credentials
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build with Cloud Build (faster and doesn't use local Docker)
gcloud builds submit \
    --tag ${IMAGE_NAME}:latest \
    --timeout=20m

echo "✓ Docker image built and pushed: ${IMAGE_NAME}:latest"

# Deploy to Cloud Run
echo "[9/9] Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --service-account ${SERVICE_ACCOUNT} \
    --add-cloudsql-instances ${PROJECT_ID}:${REGION}:${SQL_INSTANCE_NAME} \
    --set-env-vars "ENVIRONMENT=production" \
    --set-env-vars "PROJECT_ID=${PROJECT_ID}" \
    --set-env-vars "MODELS_BUCKET=${MODELS_BUCKET}" \
    --set-env-vars "DATA_BUCKET=${DATA_BUCKET}" \
    --set-secrets "DATABASE_URL=skinopathy-ad-db-connection:latest" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo "=================================================="
echo "  🎉 Deployment Complete!"
echo "=================================================="
echo "Service URL: ${SERVICE_URL}"
echo "API Docs: ${SERVICE_URL}/api/v1/docs"
echo ""
echo "Test the API:"
echo "  curl ${SERVICE_URL}/health"
echo ""
echo "Cloud Storage Buckets:"
echo "  Models: gs://${MODELS_BUCKET}"
echo "  Data: gs://${DATA_BUCKET}"
echo ""
echo "Cloud SQL:"
echo "  Instance: ${SQL_INSTANCE_NAME}"
echo "  Database: ${DB_NAME}"
echo "  Connection: See Secret Manager > skinopathy-ad-db-connection"
echo ""
echo "To upload ML models:"
echo "  gsutil cp /path/to/model.h5 gs://${MODELS_BUCKET}/"
echo ""
echo "=================================================="
