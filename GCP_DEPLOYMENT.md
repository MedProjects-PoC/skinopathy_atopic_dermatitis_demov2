# GCP Deployment Guide - Skinopathy AD Demo v2

## Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Service Account** credentials (`gcp-credentials.json`)
4. **Project ID**: `total-furnace-288818`
5. **Region**: `us-central1`

## Quick Start - Automated Deployment

The entire deployment is automated with one script:

```bash
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2
./deploy-gcp.sh
```

This script will:
1. ✅ Create Cloud Storage buckets (models + data)
2. ✅ Set up Artifact Registry
3. ✅ Create Cloud SQL PostgreSQL instance
4. ✅ Store database credentials in Secret Manager
5. ✅ Build Docker image
6. ✅ Deploy to Cloud Run

**Expected time**: 15-20 minutes (Cloud SQL creation is the slowest)

## What Gets Deployed

### Cloud Storage
- **Models Bucket**: `total-furnace-288818-models`
  - Stores ML models (EfficientNet-B7, QWEN)
- **Data Bucket**: `total-furnace-288818-skinopathy-data`
  - Stores uploaded images and saliency maps

### Cloud SQL
- **Instance**: `skinopathy-ad-db` (db-f1-micro tier)
- **Database**: `skinopathy_ad`
- **User**: `skinopathy`
- **Connection**: via Cloud SQL Proxy (automatic with Cloud Run)

### Artifact Registry
- **Repository**: `skinopathy-ad`
- **Image**: `us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-api`

### Cloud Run
- **Service**: `skinopathy-ad-api`
- **Region**: `us-central1`
- **Resources**: 2 vCPU, 2 GB RAM
- **Auto-scaling**: 0-10 instances
- **Access**: Public (unauthenticated)

## Manual Deployment Steps

If you prefer to deploy manually:

### 1. Authenticate with GCP

```bash
gcloud auth login
gcloud config set project total-furnace-288818
gcloud config set compute/region us-central1
```

### 2. Enable Required APIs

```bash
gcloud services enable \
  compute.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

### 3. Create Cloud Storage Buckets

```bash
# Models bucket
gsutil mb -p total-furnace-288818 -c STANDARD -l us-central1 gs://total-furnace-288818-models/

# Data bucket
gsutil mb -p total-furnace-288818 -c STANDARD -l us-central1 gs://total-furnace-288818-skinopathy-data/
```

### 4. Upload ML Models

```bash
# Upload EfficientNet-B7 model
gsutil cp ~/Desktop/SKINOPATHY/TO_BE_SORTED/CNN/INHOUSE/DB1_2/Trial7/Effnet7model_DB1_2_Trial7.h5 \
  gs://total-furnace-288818-models/efficientnet_b7_ad.h5

# (Optional) Upload QWEN VLM model
# gsutil -m cp -r /path/to/qwen/model gs://total-furnace-288818-models/qwen/
```

### 5. Create Cloud SQL Instance

```bash
gcloud sql instances create skinopathy-ad-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=$(openssl rand -base64 32) \
  --backup-start-time=03:00 \
  --storage-type=SSD \
  --storage-size=10GB
```

### 6. Create Database and User

```bash
# Create database
gcloud sql databases create skinopathy_ad --instance=skinopathy-ad-db

# Create user
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users create skinopathy \
  --instance=skinopathy-ad-db \
  --password=${DB_PASSWORD}

echo "Database password: ${DB_PASSWORD}"
# SAVE THIS PASSWORD!
```

### 7. Store Connection String in Secret Manager

```bash
CONNECTION_STRING="postgresql://skinopathy:${DB_PASSWORD}@/skinopathy_ad?host=/cloudsql/total-furnace-288818:us-central1:skinopathy-ad-db"

echo -n "${CONNECTION_STRING}" | gcloud secrets create skinopathy-ad-db-connection \
  --data-file=- \
  --replication-policy="automatic"

# Grant service account access
gcloud secrets add-iam-policy-binding skinopathy-ad-db-connection \
  --member="serviceAccount:skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 8. Create Artifact Registry Repository

```bash
gcloud artifacts repositories create skinopathy-ad \
  --repository-format=docker \
  --location=us-central1 \
  --description="Skinopathy AD Docker images"
```

### 9. Build and Push Docker Image

```bash
cd backend

# Authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build with Cloud Build (recommended)
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-api:latest \
  --timeout=20m
```

### 10. Deploy to Cloud Run

```bash
gcloud run deploy skinopathy-ad-api \
  --image us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-api:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --service-account skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com \
  --add-cloudsql-instances total-furnace-288818:us-central1:skinopathy-ad-db \
  --set-env-vars "ENVIRONMENT=production,PROJECT_ID=total-furnace-288818,MODELS_BUCKET=total-furnace-288818-models,DATA_BUCKET=total-furnace-288818-skinopathy-data" \
  --set-secrets "DATABASE_URL=skinopathy-ad-db-connection:latest" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0
```

## Accessing Your Deployment

After deployment, get your service URL:

```bash
gcloud run services describe skinopathy-ad-api --region=us-central1 --format="value(status.url)"
```

### API Endpoints

- **Health Check**: `https://YOUR-SERVICE-URL/health`
- **API Documentation**: `https://YOUR-SERVICE-URL/api/v1/docs`
- **Upload Endpoint**: `POST https://YOUR-SERVICE-URL/api/v1/upload/`
- **Analysis**: `GET https://YOUR-SERVICE-URL/api/v1/analysis/{session_id}`
- **Reports**: `GET https://YOUR-SERVICE-URL/api/v1/reports/{session_id}?type=user|hcp`

### Test Your Deployment

```bash
# Health check
curl https://YOUR-SERVICE-URL/health

# View API docs
open https://YOUR-SERVICE-URL/api/v1/docs
```

## Cost Estimates (us-central1)

### Development/Testing (Low Usage)
- **Cloud Run**: Free tier (2M requests/month)
- **Cloud SQL** (db-f1-micro): ~$10/month
- **Cloud Storage**: ~$0.50/month (assuming < 25 GB)
- **Artifact Registry**: Free (< 0.5 GB)
- **Total**: ~**$10-12/month**

### Production (Moderate Usage)
- **Cloud Run**: ~$20-50/month (depends on traffic)
- **Cloud SQL** (db-n1-standard-1): ~$50/month
- **Cloud Storage**: ~$2-5/month
- **Total**: ~**$75-100/month**

## Monitoring & Logs

### View Logs

```bash
# Cloud Run logs
gcloud run services logs read skinopathy-ad-api --region=us-central1 --limit=50

# Cloud SQL logs
gcloud sql operations list --instance=skinopathy-ad-db --limit=10
```

### Monitor in Console

- **Cloud Run**: https://console.cloud.google.com/run
- **Cloud SQL**: https://console.cloud.google.com/sql/instances
- **Cloud Storage**: https://console.cloud.google.com/storage/browser
- **Logs**: https://console.cloud.google.com/logs

## Database Management

### Connect to Cloud SQL

```bash
# Via Cloud SQL Proxy
gcloud sql connect skinopathy-ad-db --user=skinopathy --database=skinopathy_ad
```

### Run Migrations

```bash
# If you need to reset/initialize the database
gcloud run services update skinopathy-ad-api \
  --region=us-central1 \
  --add-env-vars "RUN_MIGRATIONS=true"
```

## Updating Your Deployment

### Update Code Only

```bash
cd backend
gcloud builds submit --tag us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-api:latest
gcloud run services update skinopathy-ad-api --region=us-central1 --image us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-api:latest
```

### Update Environment Variables

```bash
gcloud run services update skinopathy-ad-api \
  --region=us-central1 \
  --set-env-vars "NEW_VAR=value"
```

### Update Models

```bash
# Upload new model
gsutil cp /path/to/new_model.h5 gs://total-furnace-288818-models/efficientnet_b7_ad.h5

# Restart Cloud Run service to reload
gcloud run services update skinopathy-ad-api --region=us-central1 --image us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-api:latest
```

## Troubleshooting

### Issue: Service won't start

**Check logs:**
```bash
gcloud run services logs read skinopathy-ad-api --region=us-central1 --limit=100
```

**Common causes:**
- Database connection issues (check Secret Manager has correct connection string)
- Missing environment variables
- Model files not found in Cloud Storage

### Issue: Database connection errors

**Verify Cloud SQL connection:**
```bash
gcloud sql instances describe skinopathy-ad-db
gcloud sql databases list --instance=skinopathy-ad-db
```

**Check secret:**
```bash
gcloud secrets versions access latest --secret=skinopathy-ad-db-connection
```

### Issue: Permission denied errors

**Grant service account permissions:**
```bash
gcloud projects add-iam-policy-binding total-furnace-288818 \
  --member="serviceAccount:skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

## Cleanup (Delete All Resources)

**⚠️ WARNING: This will delete ALL resources and data!**

```bash
# Delete Cloud Run service
gcloud run services delete skinopathy-ad-api --region=us-central1 --quiet

# Delete Cloud SQL instance
gcloud sql instances delete skinopathy-ad-db --quiet

# Delete Cloud Storage buckets
gsutil -m rm -r gs://total-furnace-288818-models/
gsutil -m rm -r gs://total-furnace-288818-skinopathy-data/

# Delete Artifact Registry repository
gcloud artifacts repositories delete skinopathy-ad --location=us-central1 --quiet

# Delete Secret
gcloud secrets delete skinopathy-ad-db-connection --quiet
```

## Security Best Practices

1. **Never commit credentials** - use Secret Manager
2. **Enable Cloud Audit Logs** for compliance
3. **Use Cloud Armor** for DDoS protection (production)
4. **Enable Binary Authorization** for container image validation
5. **Implement authentication** for production use
6. **Set up VPC** for private networking (production)
7. **Rotate service account keys** regularly

## Support

For issues or questions:
- Check Cloud Run logs: `gcloud run services logs read...`
- Review API docs: `https://YOUR-URL/api/v1/docs`
- GCP Documentation: https://cloud.google.com/docs

---

*Generated for Project: total-furnace-288818*
*Last Updated: December 2025*
