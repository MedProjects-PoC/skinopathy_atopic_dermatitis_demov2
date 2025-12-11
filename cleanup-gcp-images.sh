#!/bin/bash
# GCP Docker Image Cleanup Script
# Safely removes old and obsolete Docker images from Artifact Registry
# Keeps latest 3 versions of each active service for rollback capability

set -e

PROJECT_ID="total-furnace-288818"
REGION="us-central1"
REPO="skinopathy-ad"

echo "🧹 GCP Docker Image Cleanup"
echo "================================"
echo ""
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Repository: $REPO"
echo ""

# Function to delete old images, keeping the latest N
cleanup_service() {
  local image_name=$1
  local keep_count=${2:-3}  # Default to keeping 3 versions

  echo "📦 Cleaning up: $image_name"
  echo "   Keeping latest $keep_count versions..."

  # Get all images sorted by update time (newest first)
  local images=$(gcloud artifacts docker images list \
    "us-central1-docker.pkg.dev/${PROJECT_ID}/${REPO}/${image_name}" \
    --sort-by="~UPDATE_TIME" \
    --limit=999 \
    --format="value(DIGEST)" 2>/dev/null || echo "")

  if [ -z "$images" ]; then
    echo "   ❌ No images found for $image_name"
    return 1
  fi

  # Convert to array
  local image_array=($images)
  local total_count=${#image_array[@]}

  if [ $total_count -le $keep_count ]; then
    echo "   ✅ Only $total_count version(s) exist (no cleanup needed)"
    return 0
  fi

  local to_delete=$((total_count - keep_count))
  echo "   📊 Total images: $total_count, will delete: $to_delete"

  # Delete old images (skip first N which are newest)
  local count=0
  for digest in "${image_array[@]:$keep_count}"; do
    count=$((count + 1))
    echo "   🗑️  Deleting ($count/$to_delete): $digest"
    gcloud artifacts docker images delete \
      "us-central1-docker.pkg.dev/${PROJECT_ID}/${REPO}/${image_name}@${digest}" \
      --quiet || echo "   ⚠️  Failed to delete $digest (may already be deleted)"
  done

  echo "   ✅ Cleanup complete for $image_name"
  echo ""
}

# Function to delete entire service image set
delete_all_service_images() {
  local image_name=$1

  echo "🗑️  DELETING ALL: $image_name"
  echo "   ⚠️  This will delete ALL versions. Use with caution!"
  echo ""

  read -p "   Are you sure? (type 'yes' to confirm): " -r confirm
  if [ "$confirm" != "yes" ]; then
    echo "   ❌ Cancelled"
    return 1
  fi

  # Get all digests
  local digests=$(gcloud artifacts docker images list \
    "us-central1-docker.pkg.dev/${PROJECT_ID}/${REPO}/${image_name}" \
    --format="value(DIGEST)" \
    --limit=999 2>/dev/null || echo "")

  if [ -z "$digests" ]; then
    echo "   ℹ️  No images found"
    return 0
  fi

  local count=0
  for digest in $digests; do
    count=$((count + 1))
    echo "   🗑️  Deleting ($count): $digest"
    gcloud artifacts docker images delete \
      "us-central1-docker.pkg.dev/${PROJECT_ID}/${REPO}/${image_name}@${digest}" \
      --quiet || echo "   ⚠️  Failed to delete"
  done

  echo "   ✅ All images deleted for $image_name"
  echo ""
}

# Main cleanup operations
echo "STEP 1: Cleanup active service images (keep latest 3)"
echo "======================================================="
cleanup_service "skinopathy-atopic-dermatitis-demo2-api" 3
cleanup_service "skinopathy-atopic-dermatitis-demo2-web" 3

echo ""
echo "STEP 2: Delete obsolete service images (old project names)"
echo "=========================================================="
read -p "Delete all skinopathy-ad-api images? (yes/no): " -r confirm
if [ "$confirm" = "yes" ]; then
  delete_all_service_images "skinopathy-ad-api"
fi

read -p "Delete all skinopathy-ad-web images? (yes/no): " -r confirm
if [ "$confirm" = "yes" ]; then
  delete_all_service_images "skinopathy-ad-web"
fi

echo ""
echo "✅ IMAGE CLEANUP COMPLETE"
echo "======================================================="
echo ""

# Show remaining images and storage
echo "📊 Current image storage:"
gcloud artifacts repositories describe $REPO \
  --location=$REGION \
  --format="table(sizeBytes.size(unit=GB))" \
  --flatten="sizeBytes" || echo "   (size calculation skipped)"

echo ""
echo "📋 Remaining images in $REPO:"
gcloud artifacts docker images list \
  "us-central1-docker.pkg.dev/${PROJECT_ID}/${REPO}" \
  --limit=999 \
  --format="table(IMAGE:30,DIGEST:40,UPDATE_TIME,SIZE(unit=GB))" || echo "   (no images)"

echo ""
echo "🚀 Safe to deploy!"
