#!/bin/bash
# Cleanup script to delete old Cloud Run services
# Run this BEFORE deploying with new service names

set -e

GCLOUD="${HOME}/google-cloud-sdk/bin/gcloud"
PROJECT_ID="total-furnace-288818"
REGION="us-central1"

OLD_BACKEND_SERVICE="skinopathy-ad-api"
OLD_FRONTEND_SERVICE="skinopathy-ad-web"

echo "=================================================="
echo "  Cleaning Up Old Cloud Run Services"
echo "=================================================="
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Set project
${GCLOUD} config set project ${PROJECT_ID}

# Check if old backend service exists
echo "[1/2] Checking for old backend service: ${OLD_BACKEND_SERVICE}"
if ${GCLOUD} run services describe ${OLD_BACKEND_SERVICE} --region=${REGION} --format="value(status.url)" 2>/dev/null; then
    echo "Found ${OLD_BACKEND_SERVICE}, deleting..."
    ${GCLOUD} run services delete ${OLD_BACKEND_SERVICE} --region=${REGION} --quiet
    echo "✓ Deleted ${OLD_BACKEND_SERVICE}"
else
    echo "Service ${OLD_BACKEND_SERVICE} not found (already deleted or never existed)"
fi

# Check if old frontend service exists
echo ""
echo "[2/2] Checking for old frontend service: ${OLD_FRONTEND_SERVICE}"
if ${GCLOUD} run services describe ${OLD_FRONTEND_SERVICE} --region=${REGION} --format="value(status.url)" 2>/dev/null; then
    echo "Found ${OLD_FRONTEND_SERVICE}, deleting..."
    ${GCLOUD} run services delete ${OLD_FRONTEND_SERVICE} --region=${REGION} --quiet
    echo "✓ Deleted ${OLD_FRONTEND_SERVICE}"
else
    echo "Service ${OLD_FRONTEND_SERVICE} not found (already deleted or never existed)"
fi

echo ""
echo "=================================================="
echo "  Cleanup Complete!"
echo "=================================================="
echo "You can now deploy with the new service names:"
echo "  ./deploy-gcp.sh"
echo "  cd frontend && ./deploy-cloud-run.sh"
echo "=================================================="
