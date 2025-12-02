# Deployment Guide - Skinopathy Atopic Dermatitis Demo v2

## Updated Service Names

The GCP Cloud Run services have been renamed to:
- **Backend API**: `skinopathy-atopic-dermatitis-demo2-api`
- **Frontend Web**: `skinopathy-atopic-dermatitis-demo2-web`

## Changes Made

### 1. Backend Deployment Script
- **File**: `deploy-gcp.sh`
- **Change**: Service name updated to `skinopathy-atopic-dermatitis-demo2-api`

### 2. Frontend Deployment Script
- **File**: `frontend/deploy-cloud-run.sh`
- **Change**: Service name updated to `skinopathy-atopic-dermatitis-demo2-web`

### 3. Frontend Configuration
- **File**: `frontend/lib/config/app_config.dart`
- **Change**: Updated with placeholder for new backend URL
- **Action Required**: After deploying backend, update line 15 with actual Cloud Run URL

### 4. Cleanup Script
- **File**: `cleanup-old-services.sh`
- **Purpose**: Deletes old services before deploying new ones

## Deployment Steps

### Step 1: Clean Up Old Services (Optional but Recommended)
```bash
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2
./cleanup-old-services.sh
```

This will delete:
- `skinopathy-ad-api`
- `skinopathy-ad-web`

### Step 2: Deploy Backend API
```bash
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2
./deploy-gcp.sh
```

**Important**: At the end of deployment, you'll see:
```
Service URL: https://skinopathy-atopic-dermatitis-demo2-api-XXXXXX-uc.a.run.app
```

**COPY THIS URL** - you'll need it for the next step.

### Step 3: Update Frontend Configuration
Edit `frontend/lib/config/app_config.dart` line 15:

**Before:**
```dart
: 'https://YOUR-BACKEND-URL-HERE/api/v1';
```

**After:**
```dart
: 'https://skinopathy-atopic-dermatitis-demo2-api-XXXXXX-uc.a.run.app/api/v1';
```

Replace `XXXXXX` with the actual hash from your backend deployment.

### Step 4: Deploy Frontend Web App
```bash
cd ~/Desktop/GIT/skinopathy_atopic_dermatitis_demov2/frontend
./deploy-cloud-run.sh
```

At the end, you'll see:
```
Web App URL: https://skinopathy-atopic-dermatitis-demo2-web-XXXXXX-uc.a.run.app
```

**This is your final application URL.**

## Testing the Deployment

### 1. Test Backend API
```bash
curl https://skinopathy-atopic-dermatitis-demo2-api-XXXXXX-uc.a.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0"
}
```

### 2. Test Frontend Web App
Open in browser:
```
https://skinopathy-atopic-dermatitis-demo2-web-XXXXXX-uc.a.run.app
```

### 3. Test API Docs
```
https://skinopathy-atopic-dermatitis-demo2-api-XXXXXX-uc.a.run.app/api/v1/docs
```

## Rollback (if needed)

If you need to rollback to old services:

1. Revert the service names in deployment scripts:
   - `deploy-gcp.sh`: Change back to `skinopathy-ad-api`
   - `frontend/deploy-cloud-run.sh`: Change back to `skinopathy-ad-web`

2. Re-deploy both services

## Service URLs Reference

After deployment, your services will be accessible at:

| Service | URL Pattern |
|---------|-------------|
| Backend API | `https://skinopathy-atopic-dermatitis-demo2-api-<hash>-uc.a.run.app` |
| Frontend Web | `https://skinopathy-atopic-dermatitis-demo2-web-<hash>-uc.a.run.app` |
| API Docs | `https://skinopathy-atopic-dermatitis-demo2-api-<hash>-uc.a.run.app/api/v1/docs` |
| Health Check | `https://skinopathy-atopic-dermatitis-demo2-api-<hash>-uc.a.run.app/health` |

## Project Information

- **GCP Project**: `total-furnace-288818`
- **Region**: `us-central1`
- **Service Account**: `skinopathy-ad-deployer@total-furnace-288818.iam.gserviceaccount.com`
- **Artifact Registry**: `us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad`

## Deployment Time Estimates

- **Backend**: ~15-20 minutes (includes Cloud SQL setup if first deployment)
- **Frontend**: ~5-10 minutes
- **Total**: ~20-30 minutes

## Notes

- The backend deployment includes Cloud SQL database setup (first time only)
- Docker images are built using Cloud Build
- Services are configured with appropriate memory, CPU, and timeout settings
- Both services support auto-scaling (0-10 instances)
- CORS is configured to allow frontend-backend communication

## Support

For issues or questions:
1. Check Cloud Run logs: `gcloud run services logs read <service-name> --region=us-central1`
2. Check Cloud Build logs: `gcloud builds list --limit=5`
3. Verify service status: `gcloud run services describe <service-name> --region=us-central1`
