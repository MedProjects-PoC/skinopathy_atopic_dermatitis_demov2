#!/bin/bash

# Deploy Skinopathy AD Frontend to Google Cloud Run
# Usage: ./deploy-frontend.sh

set -e

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
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/install"
    exit 1
fi

# Authenticate
echo "🔐 Checking authentication..."
gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1 || {
    echo "❌ Not authenticated. Running: gcloud auth login"
    gcloud auth login
}

# Set project
echo "📦 Setting project: ${PROJECT_ID}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com

# Build the Docker image (using pre-built Flutter web app)
echo ""
echo "🏗️  Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} -f frontend/Dockerfile.optimized frontend/

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
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
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "========================================="
echo "  ✅ Deployment Complete!"
echo "========================================="
echo ""
echo "🌐 Your frontend is live at:"
echo "   ${SERVICE_URL}"
echo ""
echo "📊 Logs:"
echo "   gcloud run services logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "⚙️  Manage:"
echo "   https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}"
echo ""
echo "🔗 Backend API:"
echo "   https://skinopathy-atopic-dermatitis-demo2-api-42406804042.us-central1.run.app"
echo ""
