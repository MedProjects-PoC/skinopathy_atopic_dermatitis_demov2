#!/bin/bash
set -e

echo "🔐 Skinopathy AD Frontend - Docker Image Push Script"
echo "=================================================="
echo ""

# Step 1: Authenticate gcloud (requires browser)
echo "Step 1: Authenticate with gcloud (will open browser)..."
gcloud auth login --no-launch-browser

# Step 2: Set project
echo ""
echo "Step 2: Setting GCP project to skin-demos..."
gcloud config set project skin-demos

# Step 3: Configure Docker auth
echo ""
echo "Step 3: Configuring Docker authentication for Artifact Registry..."
gcloud auth configure-docker us-central1-docker.pkg.dev

# Step 4: Push the image
echo ""
echo "Step 4: Pushing Docker image to GCP Artifact Registry..."
echo "Image: us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest"
docker push us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest

# Step 5: Deploy to Cloud Run
echo ""
echo "Step 5: Deploying to Cloud Run..."
gcloud run deploy skinopathy-atopic-dermatitis-demo2-web \
    --image us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10

echo ""
echo "✅ Frontend deployment complete!"
echo ""
echo "Your frontend is now available at:"
gcloud run services describe skinopathy-atopic-dermatitis-demo2-web --region us-central1 --format='value(status.url)'
