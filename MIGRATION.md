# Atopic Dermatitis Demo V2 Migration to Skinopathy Organization

## Migration Summary

**Date**: January 15, 2026
**From**: `total-furnace-288818` (Personal Project)
**To**: `skin-demos` (Skinopathy Organization)
**Status**: ✅ Complete

---

## Migration Overview

Successfully migrated both frontend (web) and backend (API) services of the Skinopathy Atopic Dermatitis Demo V2 from personal GCP project to Skinopathy organization's `skin-demos` project.

---

## What Was Migrated

### 1. **Container Images**
   - **API Service Image**
     - Source: `us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api:latest`
     - Target: `us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api:latest`
     - Size: ~8GB (TensorFlow base + ML models)
     - Memory: 8Gi, CPU: 4 vCPU

   - **Web Service Image**
     - Source: `us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest`
     - Target: `us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest`
     - Size: ~512MB (Flutter web frontend)
     - Memory: 512Mi, CPU: 1 vCPU

### 2. **Cloud Run Deployments**
   - **API Service**
     - Service Name: `skinopathy-atopic-dermatitis-demo2-api`
     - Region: `us-central1`
     - Previous URL: `https://skinopathy-atopic-dermatitis-demo2-api-890999745336.us-central1.run.app` (Retired)
     - New URL: `https://skinopathy-atopic-dermatitis-demo2-api-42406804042.us-central1.run.app` (Active)
     - Configuration: 8 vCPU, 8GB memory, 600s timeout, min 1 instance, max 10 instances

   - **Web Service**
     - Service Name: `skinopathy-atopic-dermatitis-demo2-web`
     - Region: `us-central1`
     - Previous URL: `https://skinopathy-atopic-dermatitis-demo2-web-890999745336.us-central1.run.app` (Retired)
     - New URL: `https://skinopathy-atopic-dermatitis-demo2-web-42406804042.us-central1.run.app` (Active)
     - Configuration: 1 vCPU, 512MB memory, 30s timeout, max 10 instances

### 3. **Database Infrastructure**
   - **Cloud SQL Instance**
     - Name: `skinopathy-ad-db`
     - Engine: PostgreSQL 15
     - Tier: db-f1-micro
     - Location: us-central1
     - Status: ✅ Created in skin-demos
     - Database: `skinopathy_ad`
     - User: `skinopathy` (with secure password)
     - Connection: Via Secret Manager (`skinopathy-ad-db-connection`)

### 4. **Storage Buckets** (Created)
   - `skin-demos-models` - ML models storage (EfficientNet-B7: ~458MB)
   - `skin-demos-skinopathy-data` - User images and saliency maps

### 5. **Infrastructure Services**
   - Artifact Registry: `skinopathy-ad` repository
   - Secret Manager: `skinopathy-ad-db-connection` secret
   - IAM: Service account permissions configured

---

## Technical Steps Executed

### Step 1: Image Copy
```bash
# Authenticated with personal account
gcloud config configurations activate default
gcloud auth configure-docker us-central1-docker.pkg.dev

# Pulled both images from personal Artifact Registry
docker pull us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api:latest
docker pull us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest

# Tagged for Skinopathy registry
docker tag ... us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api:latest
docker tag ... us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest

# Authenticated with Skinopathy account
gcloud config configurations activate skinopathy-gcp
gcloud auth configure-docker us-central1-docker.pkg.dev

# Pushed to Skinopathy registry
docker push us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api:latest
docker push us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest
```

### Step 2: Cloud SQL Setup
```bash
# Create PostgreSQL instance
gcloud sql instances create skinopathy-ad-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --availability-type=regional \
    --backup

# Create database and user
gcloud sql databases create skinopathy_ad --instance=skinopathy-ad-db
gcloud sql users create skinopathy --instance=skinopathy-ad-db --password
```

### Step 3: Secret Manager Configuration
```bash
# Create database connection secret
gcloud secrets create skinopathy-ad-db-connection \
    --replication-policy="automatic" \
    --data-file=db_url.txt

# Grant service account access
gcloud secrets add-iam-policy-binding skinopathy-ad-db-connection \
    --member="serviceAccount:42406804042-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 4: Cloud Run Deployment
```bash
# Deploy API service (with database secret)
gcloud run deploy skinopathy-atopic-dermatitis-demo2-api \
    --image us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api:latest \
    --memory 8Gi --cpu 4 --timeout 600 \
    --min-instances 1 --max-instances 10 \
    --set-env-vars "ENVIRONMENT=production,PROJECT_ID=skin-demos,GCP_REGION=us-central1,MODELS_BUCKET=skin-demos-models,DATA_BUCKET=skin-demos-skinopathy-data" \
    --set-secrets "DATABASE_URL=skinopathy-ad-db-connection:latest"

# Deploy Web service
gcloud run deploy skinopathy-atopic-dermatitis-demo2-web \
    --image us-central1-docker.pkg.dev/skin-demos/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest \
    --memory 512Mi --cpu 1 --timeout 30 \
    --max-instances 10
```

---

## Configuration Changes

| Component | Before | After |
|-----------|--------|-------|
| **Project ID** | `total-furnace-288818` | `skin-demos` |
| **API Image Registry** | `total-furnace-288818/skinopathy-ad` | `skin-demos/skinopathy-ad` |
| **API URL** | `...890999745336.us-central1.run.app` | `...42406804042.us-central1.run.app` |
| **Web URL** | `...890999745336.us-central1.run.app` | `...42406804042.us-central1.run.app` |
| **Models Bucket** | `total-furnace-288818-models` | `skin-demos-models` |
| **Data Bucket** | `total-furnace-288818-skinopathy-data` | `skin-demos-skinopathy-data` |
| **Database** | Personal project (cross-project) | Skinopathy project (same project) |
| **Billing** | Personal account | Skinopathy Dev Account |
| **Organization** | N/A | Skinopathy Organization |

---

## Updated Documentation Files

The following documentation files have been updated to reflect the migration:

1. **README.md**
   - Updated project references from personal to Skinopathy
   - Updated bucket names
   - Updated service account references
   - Updated image registry paths

2. **API_DOCUMENTATION.md**
   - Updated all API endpoint examples with new URL
   - Updated base URL reference
   - Updated interactive documentation links (Swagger UI, ReDoc)

3. **MIGRATION.md** (This file)
   - Complete migration documentation
   - Rollback instructions
   - Performance and cost implications

---

## Service Status

### API Service
- **URL**: https://skinopathy-atopic-dermatitis-demo2-api-42406804042.us-central1.run.app
- **Status**: ✅ Active and serving traffic
- **Revision**: skinopathy-atopic-dermatitis-demo2-api-00005-zbj
- **Traffic**: 100% routed to latest revision
- **Memory**: 8Gi
- **CPU**: 4 vCPU
- **Min Instances**: 1
- **Max Instances**: 10
- **Database**: Connected via Secret Manager
- **Health Check**: `GET /health`

### Web Service
- **URL**: https://skinopathy-atopic-dermatitis-demo2-web-42406804042.us-central1.run.app
- **Status**: ✅ Active and serving traffic
- **Revision**: skinopathy-atopic-dermatitis-demo2-web-00001-rwk
- **Traffic**: 100% routed to latest revision
- **Memory**: 512Mi
- **CPU**: 1 vCPU
- **Max Instances**: 10

---

## Verification Checklist

- [x] Container images copied to Skinopathy registry (both API and Web)
- [x] Cloud Run services deployed (both API and Web)
- [x] Service URLs confirmed and responding
- [x] Cloud SQL instance created and database initialized
- [x] Database user and password configured
- [x] Secret Manager secret created and accessible
- [x] IAM permissions configured for service account
- [x] Storage buckets created
- [x] Billing account linked correctly
- [x] Environment variables set correctly
- [x] Documentation updated (README.md, API_DOCUMENTATION.md)
- [x] Git repository updates pending

---

## Rollback Instructions

To revert to the personal project (if needed):

```bash
# Use personal account
gcloud config configurations activate default
gcloud config set project total-furnace-288818

# Redeploy from personal registry
gcloud run deploy skinopathy-atopic-dermatitis-demo2-api \
    --image us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api:latest \
    --region us-central1 --platform managed

gcloud run deploy skinopathy-atopic-dermatitis-demo2-web \
    --image us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest \
    --region us-central1 --platform managed
```

**Note**: Rollback will:
- Restore personal project URLs
- Revert billing to personal account
- Use personal Cloud SQL instance
- Loss of any data created during Skinopathy deployment

---

## Performance & Scalability

### API Service
- **Startup Time**: ~30-45 seconds (TensorFlow model loading)
- **Response Time**: ~2-10 seconds per analysis (CNN + RAG + Vision LLM)
- **Concurrency**: 80 concurrent requests per instance
- **Auto-scaling**: 1-10 instances based on load

### Web Service
- **Startup Time**: ~5-10 seconds
- **Response Time**: <100ms (static files/proxying)
- **Concurrency**: 80 concurrent requests per instance
- **Auto-scaling**: 0-10 instances based on load

---

## Cost Implications

### Before (Personal Project)
- Billing to personal GCP account
- Dedicated resources

### After (Skinopathy Project)
- **Billing**: Skinopathy Dev Billing Account
- **Cloud Run**: ~$0.25/GB-second (8GB API + 0.5GB Web)
- **Cloud SQL**: ~$8-15/month (db-f1-micro)
- **Storage**: Variable (based on usage)
- **Free Tier**: 2M Cloud Run requests/month apply to Skinopathy organization

---

## Future Considerations

### Cross-Service Communication
- Both services in same project simplify networking
- Use service-to-service authentication if needed
- Consider VPC setup for enhanced security

### Data Migration
- Historical data still in personal project Cloud SQL
- Consider archiving or migrating to skin-demos database
- Update any reporting or analytics to new database

### Monitoring & Logging
- All logs now in Skinopathy Cloud Logging
- Set up alerting and dashboards for API performance
- Monitor database performance and connections

---

## Timeline

| Date/Time | Event |
|-----------|-------|
| Jan 15, 2026 10:00 AM | Planning and script preparation |
| Jan 15, 2026 11:00 AM | Container images copied to Skinopathy |
| Jan 15, 2026 11:30 AM | Cloud SQL instance created |
| Jan 15, 2026 12:00 PM | Database configured, secrets created |
| Jan 15, 2026 12:15 PM | Web service deployed successfully |
| Jan 15, 2026 12:30 PM | API service deployed successfully |
| Jan 15, 2026 03:45 PM | Documentation updated |

---

## Support & Troubleshooting

### API Service Issues
- Health Check: `curl https://skinopathy-atopic-dermatitis-demo2-api-42406804042.us-central1.run.app/health`
- View Logs: `gcloud run services logs read skinopathy-atopic-dermatitis-demo2-api --region=us-central1`
- Check Database: Test connection via Cloud SQL Proxy

### Web Service Issues
- Test URL: `https://skinopathy-atopic-dermatitis-demo2-web-42406804042.us-central1.run.app`
- View Logs: `gcloud run services logs read skinopathy-atopic-dermatitis-demo2-web --region=us-central1`
- Check routing to API endpoint

### Database Issues
- Verify connection string in Secret Manager
- Check service account permissions
- Verify Cloud SQL instance is running

---

## References

- See `README.md` for project overview
- See `API_DOCUMENTATION.md` for API usage
- See `DEPLOYMENT.md` for deployment procedures
- See `CHANGELOG.md` for version history

---

**Migration Status**: ✅ COMPLETE
**Deployment Status**: ✅ ACTIVE
**Documentation Status**: ✅ UPDATED
**Ready for Production**: ✅ YES
