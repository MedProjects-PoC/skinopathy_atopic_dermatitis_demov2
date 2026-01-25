#!/bin/bash

# Deploy Skinopathy AD Backend to Google Cloud Run
# Usage: ./deploy-backend.sh

set -e

# Set gcloud path (like old deploy-gcp.sh)
GCLOUD="${HOME}/google-cloud-sdk/bin/gcloud"

# Configuration
PROJECT_ID="skin-demos"
REGION="us-central1"
SERVICE_NAME="skinopathy-atopic-dermatitis-demo2-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "========================================="
echo "  Deploying Skinopathy AD Backend API"
echo "========================================="
echo ""
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check if gcloud is installed
if [ ! -f "${GCLOUD}" ]; then
    echo "❌ gcloud CLI not found at: ${GCLOUD}"
    echo "Please install Google Cloud SDK"
    exit 1
fi

# Authenticate
echo "🔐 Checking authentication..."
${GCLOUD} auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1 || {
    echo "❌ Not authenticated. Running: ${GCLOUD} auth login"
    ${GCLOUD} auth login
}

# Set project (skip if already configured)
CURRENT_PROJECT=$(${GCLOUD} config get-value project 2>/dev/null || echo "")
if [ "${CURRENT_PROJECT}" != "${PROJECT_ID}" ]; then
    echo "📦 Setting project: ${PROJECT_ID}"
    ${GCLOUD} config set project ${PROJECT_ID}
else
    echo "📦 Project already set to: ${PROJECT_ID}"
fi

# Enable required APIs
echo "🔧 Enabling required APIs..."
${GCLOUD} services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    sqladmin.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com \
    storage.googleapis.com

# Build the Docker image
echo ""
echo "🏗️  Building Docker image (this may take 5-10 minutes)..."
${GCLOUD} builds submit --tag ${IMAGE_NAME} backend/

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."
${GCLOUD} run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --region ${REGION} \
    --platform managed \
    --memory 8Gi \
    --cpu 4 \
    --timeout 600 \
    --max-instances 10 \
    --min-instances 1 \
    --set-env-vars "ENVIRONMENT=production,PROJECT_ID=${PROJECT_ID},GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},MODELS_BUCKET=skin-demos-models,DATA_BUCKET=skin-demos-skinopathy-data" \
    --set-secrets "DATABASE_URL=skinopathy-ad-db-connection:latest" \
    --no-allow-unauthenticated

# Get the service URL
SERVICE_URL=$(${GCLOUD} run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "========================================="
echo "  ✅ Deployment Complete!"
echo "========================================="
echo ""
echo "🌐 Your API is live at:"
echo "   ${SERVICE_URL}"
echo ""
echo "📚 API Docs:"
echo "   ${SERVICE_URL}/api/v1/docs"
echo ""
echo "📊 Logs:"
echo "   ${GCLOUD} run services logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "⚙️  Manage:"
echo "   https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}"
echo ""
echo "💾 Database:"
echo "   Instance: skinopathy-ad-db"
echo "   Database: skinopathy_ad"
echo "   Connection: via Secret Manager (skinopathy-ad-db-connection)"
echo ""
