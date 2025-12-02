#!/bin/bash
# Deploy Flutter Web App to Cloud Run
# This script builds and deploys the Flutter web app to GCP Cloud Run

set -e  # Exit on error

# Set gcloud path
GCLOUD="${HOME}/google-cloud-sdk/bin/gcloud"

PROJECT_ID="total-furnace-288818"
REGION="us-central1"
SERVICE_NAME="skinopathy-atopic-dermatitis-demo2-web"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/skinopathy-ad/${SERVICE_NAME}"

echo "=================================================="
echo "  Flutter Web App - Cloud Run Deployment"
echo "=================================================="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check authentication
echo "[1/3] Checking authentication..."
${GCLOUD} auth list --filter=status:ACTIVE --format="value(account)" | head -1 || {
    echo "Error: Not authenticated. Run 'gcloud auth login' first."
    exit 1
}

# Set project
${GCLOUD} config set project ${PROJECT_ID}

# Build and push Docker image
echo "[2/3] Building and pushing Docker image..."
${GCLOUD} auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build with Cloud Build
${GCLOUD} builds submit \
    --tag ${IMAGE_NAME}:latest \
    --timeout=20m

echo "✓ Docker image built and pushed: ${IMAGE_NAME}:latest"

# Deploy to Cloud Run
echo "[3/3] Deploying to Cloud Run..."
${GCLOUD} run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 30 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080

SERVICE_URL=$(${GCLOUD} run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")

echo ""
echo "=================================================="
echo "  🎉 Deployment Complete!"
echo "=================================================="
echo "Web App URL: ${SERVICE_URL}"
echo ""
echo "To update API endpoint in Flutter app:"
echo "  Edit frontend/lib/config/app_config.dart"
echo "  Update apiBaseUrl to your backend URL"
echo ""
echo "=================================================="
