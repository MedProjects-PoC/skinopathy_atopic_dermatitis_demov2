# GCP Personal to Corporate Migration Guide

Quick migration from personal GCP project to company GCP project (easiest migration path).

---

## Executive Summary

**Difficulty: VERY EASY** (90% infrastructure is reusable)
**Time Required: 1-2 days**
**Downtime: 30 minutes (if done carefully)**
**Code Changes: 0 lines** (just config updates)

Moving from your personal GCP (`total-furnace-288818`) to company GCP is straightforward because:
- Same GCP platform and services
- No API changes
- Same authentication mechanisms
- Just copy resources between projects

---

## What Moves Where

| Resource | Current (Personal) | → Corporate Project | Effort |
|----------|-------------------|-------------------|--------|
| Code | GitHub | Same GitHub | None |
| Container Images | Artifact Registry | Artifact Registry | Copy |
| Database | Cloud SQL | Cloud SQL | Migrate |
| Storage | Cloud Storage (GCS) | Cloud Storage (GCS) | Copy |
| Models | GCS bucket | GCS bucket | Copy |
| Secrets | Secret Manager | Secret Manager | Recreate |
| Cloud Run | Deployed services | Deployed services | Redeploy |
| Vertex AI Access | Current project | Corporate project | Update credentials |

---

## Step-by-Step Migration

### Step 1: Setup Corporate GCP Project (Hour 1)

```bash
# Set corporate project ID
export CORP_PROJECT_ID="your-company-project-id"
export CORP_REGION="us-central1"

# Authenticate to corporate GCP
gcloud auth login
gcloud config set project $CORP_PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  storage-api.googleapis.com \
  compute.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com
```

### Step 2: Copy Container Images (15 minutes)

```bash
# Set variables
export PERSONAL_PROJECT="total-furnace-288818"
export CORP_REGISTRY="us-central1-docker.pkg.dev/${CORP_PROJECT_ID}/skinopathy"
export PERSONAL_REGISTRY="us-central1-docker.pkg.dev/${PERSONAL_PROJECT}/skinopathy-ad"

# Copy frontend image
gcloud container images copy \
  --source-image="${PERSONAL_REGISTRY}/skinopathy-atopic-dermatitis-demo2-web:latest" \
  --destination-image="${CORP_REGISTRY}/skinopathy-atopic-dermatitis-demo2-web:latest"

# Copy backend image
gcloud container images copy \
  --source-image="${PERSONAL_REGISTRY}/skinopathy-atopic-dermatitis-demo2-api:latest" \
  --destination-image="${CORP_REGISTRY}/skinopathy-atopic-dermatitis-demo2-api:latest"

# Verify
gcloud container images list --repository="${CORP_REGISTRY}"
```

### Step 3: Migrate Database (30 minutes)

```bash
# Create new Cloud SQL instance in corporate project
gcloud sql instances create skinopathy-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=$CORP_REGION \
  --storage-size=10GB

# Create database
gcloud sql databases create skinopathy_db \
  --instance=skinopathy-db

# Create user
gcloud sql users create skinopathy-user \
  --instance=skinopathy-db \
  --password

# Export from personal project
gcloud config set project $PERSONAL_PROJECT
pg_dump \
  -h <CLOUD_SQL_IP> \
  -U postgres \
  skinopathy_db > /tmp/skinopathy_backup.sql

# Import to corporate project
gcloud config set project $CORP_PROJECT_ID
psql \
  -h <CORP_CLOUD_SQL_IP> \
  -U skinopathy-user \
  skinopathy_db < /tmp/skinopathy_backup.sql

# Test connection
gcloud sql connect skinopathy-db --user=skinopathy-user
```

### Step 4: Copy Cloud Storage Buckets (20 minutes)

```bash
# List buckets to copy
export PERSONAL_BUCKET="total-furnace-288818-models"
export CORP_BUCKET="${CORP_PROJECT_ID}-models"

# Create corporate bucket
gsutil mb -p $CORP_PROJECT_ID gs://${CORP_BUCKET}

# Copy all models and data
gsutil -m cp -r gs://${PERSONAL_BUCKET}/* gs://${CORP_BUCKET}/

# Verify copy
gsutil ls -r gs://${CORP_BUCKET}/ | head -20
```

### Step 5: Setup Secrets (10 minutes)

```bash
# Create secrets in corporate Secret Manager
# You'll need to update these with corporate values:

# Database password
echo "skinopathy-password" | gcloud secrets create DATABASE_PASSWORD \
  --data-file=-

# API keys (update to corporate API keys)
gcloud secrets create OPENAI_API_KEY --data-file=-
gcloud secrets create VERTEX_AI_KEY --data-file=-

# Storage bucket name
echo $CORP_BUCKET | gcloud secrets create STORAGE_BUCKET --data-file=-

# Cloud SQL connection string
echo "postgresql://user:pass@IP:5432/db" | gcloud secrets create DATABASE_URL --data-file=-
```

### Step 6: Deploy to Corporate Cloud Run (45 minutes)

#### 6.1 Deploy Backend

```bash
# Build and push
gcloud run deploy skinopathy-atopic-dermatitis-demo2-api \
  --image=${CORP_REGISTRY}/skinopathy-atopic-dermatitis-demo2-api:latest \
  --region=$CORP_REGION \
  --platform=managed \
  --memory=4Gi \
  --cpu=2 \
  --timeout=3600 \
  --set-env-vars=\
DATABASE_URL="postgresql://user:pass@<CORP_SQL_IP>:5432/skinopathy_db",\
STORAGE_BUCKET=$CORP_BUCKET,\
GCP_PROJECT_ID=$CORP_PROJECT_ID,\
GCP_REGION=$CORP_REGION

# Get service URL
gcloud run services describe skinopathy-atopic-dermatitis-demo2-api \
  --region=$CORP_REGION --format="value(status.url)"
```

#### 6.2 Deploy Frontend

```bash
# Get backend API URL from previous step
export CORP_API_URL="<from step above>"

gcloud run deploy skinopathy-atopic-dermatitis-demo2-web \
  --image=${CORP_REGISTRY}/skinopathy-atopic-dermatitis-demo2-web:latest \
  --region=$CORP_REGION \
  --platform=managed \
  --memory=1Gi \
  --cpu=1 \
  --set-env-vars=API_URL=$CORP_API_URL

# Get service URL
gcloud run services describe skinopathy-atopic-dermatitis-demo2-web \
  --region=$CORP_REGION --format="value(status.url)"
```

### Step 7: Verify Deployment (15 minutes)

```bash
# Test backend health
curl https://<backend-url>/health

# Test frontend
# Open frontend URL in browser
# Upload test image
# Verify PDF download works (if using develop branch)
# Verify saliency map appears

# Check logs
gcloud run services logs read skinopathy-atopic-dermatitis-demo2-api \
  --region=$CORP_REGION --limit=50

gcloud run services logs read skinopathy-atopic-dermatitis-demo2-web \
  --region=$CORP_REGION --limit=50
```

### Step 8: Update Configuration (5 minutes)

Update these files if needed:

```bash
# Update deploy script to point to corporate project
sed -i 's/total-furnace-288818/'$CORP_PROJECT_ID'/g' deploy-gcp-fast.sh

# Update Terraform/IaC if used
# (not in current project, but good practice for corporate)

# Update GitHub Actions (if using)
# Change artifact registry to corporate registry
```

---

## Minimal Migration (Emergency/Fast)

If you need to do this in 30 minutes:

```bash
# 1. Create Cloud SQL instance (parallel with other steps)
gcloud sql instances create skinopathy-db --tier=db-f1-micro --region=us-central1

# 2. Copy images (2 minutes)
gcloud container images copy --source-image=... --destination-image=...

# 3. Copy buckets (5 minutes)
gsutil -m cp -r gs://personal-bucket/* gs://corporate-bucket/

# 4. Deploy services (20 minutes total)
gcloud run deploy skinopathy-api --image=<image> --set-env-vars=...
gcloud run deploy skinopathy-web --image=<image> --set-env-vars=...

# 5. Test (3 minutes)
curl https://<url>/health
# Visit frontend URL in browser
```

---

## Zero-Downtime Migration (Recommended)

Run both in parallel, then switch DNS:

```bash
# 1. Setup corporate project (parallel)
# - Create all resources
# - Deploy services
# - Test thoroughly (1 hour)

# 2. Setup Load Balancer or use Cloud DNS to split traffic
# - 10% corporate, 90% personal (test)
# - 50% corporate, 50% personal (monitor)
# - 100% corporate (when confident)

# 3. Monitor metrics (2 hours)
# - Error rates
# - Latency
# - Database connections

# 4. Switch 100% to corporate
# - Update all DNS/LB rules
# - Monitor for 30 minutes

# 5. Decommission personal
# - Keep for 1 week backup
# - Delete after verification
```

---

## Important Configuration to Update

### In deploy-gcp-fast.sh

```bash
# Line 10: Change project ID
-PROJECT_ID="total-furnace-288818"
+PROJECT_ID="your-company-project-id"

# Line 14: Change repository name (optional)
-REPO_NAME="skinopathy-ad"
+REPO_NAME="skinopathy-ad"  # Keep same or change to company standard
```

### In Environment Variables

```bash
# Update all references to:
GCP_PROJECT_ID → corporate project ID
MODELS_BUCKET → gs://corporate-bucket
DATABASE_HOST → <new Cloud SQL IP>
DATABASE_USER → corporate database user
```

### In Code (if hardcoded)

```python
# backend/app/core/config.py
class Config:
    -GCP_PROJECT_ID = "total-furnace-288818"
    +GCP_PROJECT_ID = "your-company-project"
```

---

## Cost Comparison

### Personal GCP (Current)
- Cloud Run: ~$20-50/month
- Cloud SQL: ~$30-50/month
- Vertex AI: ~$10-20/month
- Cloud Storage: ~$5-10/month
- **Total: ~$65-130/month**

### Corporate GCP (Same)
- Same services = same cost
- But billing through company
- May have committed use discounts
- **Total: ~$65-130/month**

**No cost increase** - same services, same pricing!

---

## Rollback Plan

If corporate deployment fails:

```bash
# Switch users back to personal GCP
# Use Cloud DNS or Application Load Balancer to route to personal services
# Takes 5 minutes
```

Or just wait - personal project is still running!

---

## Validation Checklist

Before declaring migration complete:

- [ ] Backend API starts without errors
- [ ] Frontend loads and can reach API
- [ ] Test image upload works
- [ ] Analysis completes (2-3 minutes)
- [ ] PDF download works (if develop branch)
- [ ] Saliency maps appear (if develop branch)
- [ ] Database persists data
- [ ] Cloud Storage buckets accessible
- [ ] No API errors in logs
- [ ] Team can access new URLs

---

## Git Changes Needed

Almost none! Just update config files:

```bash
# 1. Update project ID in deploy script
./deploy-gcp-fast.sh  # will show new project in startup message

# 2. Optional: Update README with new URLs
# 3. Optional: Update GitHub Actions if used

# Commit:
git add deploy-gcp-fast.sh backend/app/core/config.py
git commit -m "Update GCP project to corporate [company-project-id]"
```

---

## Timeline

| Task | Time | Parallel |
|------|------|----------|
| Enable GCP APIs | 5 min | Yes |
| Copy container images | 15 min | Yes |
| Create Cloud SQL | 10 min | Yes (runs in background) |
| Export/Import database | 20 min | Partial (after SQL ready) |
| Copy Cloud Storage | 15 min | Yes |
| Setup secrets | 10 min | Yes |
| Deploy backend | 15 min | After SQL ready |
| Deploy frontend | 10 min | After backend ready |
| Verify | 15 min | Sequential |
| **Total (sequential)** | **125 min** | - |
| **Total (parallel)** | **45 min** | ✓ |

---

## Gotchas & Warnings

⚠️ **API Quotas**: Corporate project may have different quotas
- Check: `gcloud compute project-info describe --project=$CORP_PROJECT`

⚠️ **VPC/Firewall**: Ensure Cloud Run can reach Cloud SQL
- May need to allow traffic in firewall rules

⚠️ **IAM Permissions**: Ensure your corporate user has:
- Editor role on the project
- Service Account User role
- Secret Manager access

⚠️ **Billing Account**: Ensure corporate project has active billing
- Free tier won't work for Cloud Run

⚠️ **Regions**: Match regions for performance
- Personal uses us-central1
- Keep corporate on us-central1 too

---

## Common Issues & Fixes

**Issue: "Permission denied" when accessing Cloud SQL**
```bash
# Solution: Add Cloud Run service account to Cloud SQL Client role
gcloud projects add-iam-policy-binding $CORP_PROJECT_ID \
  --member=serviceAccount:<service-account>@appspot.gserviceaccount.com \
  --role=roles/cloudsql.client
```

**Issue: "Connection refused" from frontend to backend**
```bash
# Solution: Update CORS or API_URL in frontend
# Check that backend service URL is correct in frontend config
```

**Issue: "Bucket not found" errors**
```bash
# Solution: Verify bucket copy completed
gsutil ls gs://$CORP_BUCKET/
# Re-run copy if needed
```

**Issue: Database import timeout**
```bash
# Solution: Increase Cloud SQL tier temporarily, or import in chunks
gcloud sql instances patch skinopathy-db --tier=db-n1-standard-1
# Then retry import
```

---

## After Migration

1. **Keep personal GCP running for 1 week** (emergency rollback)
2. **Monitor corporate deployment daily** (error rates, latency)
3. **Update team documentation** (new URLs)
4. **Update DNS/load balancer** (if using)
5. **Decommission personal GCP** (after 1 week confidence)

---

## Questions?

**Q: Will the RAG system work?**
A: Yes, same Vertex AI APIs in corporate project

**Q: Do I need to retrain models?**
A: No, models are just files in GCS

**Q: Can I use corporate credentials?**
A: Yes, corporate GCP project uses corporate credentials automatically

**Q: What about GitHub secrets?**
A: Keep same GitHub secrets, they contain corporate project values

---

**Bottom Line**: This is the easiest migration possible. Same platform, same code, just move resources between GCP projects. **1-2 days from start to finish.**

