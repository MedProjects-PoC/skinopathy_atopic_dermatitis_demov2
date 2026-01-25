#!/bin/bash

# Deploy Skinopathy AD Frontend to Google Cloud Run
# Usage: ./deploy-frontend.sh

set -e

# Set gcloud path (like AD-Chatbot project)
GCLOUD="${HOME}/google-cloud-sdk/bin/gcloud"

# Configuration
PROJECT_ID="skin-demos"
REGION="us-central1"
SERVICE_NAME="skinopathy-atopic-dermatitis-demo2-web"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "========================================="
echo "  Deploying Skinopathy AD Frontend"
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
    containerregistry.googleapis.com

# Build the Docker image (using pre-built Flutter web app)
echo ""
echo "🏗️  Building Docker image..."
${GCLOUD} builds submit --tag ${IMAGE_NAME} -f frontend/Dockerfile.optimized frontend/

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."
${GCLOUD} run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 30 \
    --max-instances 10 \
    --min-instances 0

# Get the service URL
SERVICE_URL=$(${GCLOUD} run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "========================================="
echo "  ✅ Deployment Complete!"
echo "========================================="
echo ""
echo "🌐 Your frontend is live at:"
echo "   ${SERVICE_URL}"
echo ""
echo "📊 Logs:"
echo "   ${GCLOUD} run services logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "⚙️  Manage:"
echo "   https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}"
echo ""
echo "🔗 Backend API:"
echo "   https://skinopathy-atopic-dermatitis-demo2-api-42406804042.us-central1.run.app"
echo ""
