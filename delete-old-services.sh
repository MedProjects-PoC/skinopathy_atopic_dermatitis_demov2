#!/bin/bash
echo "Deleting old Cloud Run services..."
/Users/rakesh/google-cloud-sdk/bin/gcloud run services delete skinopathy-ad-api --region=us-central1 --quiet
/Users/rakesh/google-cloud-sdk/bin/gcloud run services delete skinopathy-ad-web --region=us-central1 --quiet
echo "Old services deleted!"
