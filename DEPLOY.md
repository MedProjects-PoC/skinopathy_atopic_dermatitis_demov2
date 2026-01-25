# Skinopathy AD Demo v2 - Deployment Guide

## Prerequisites

- ✅ Google Cloud SDK installed at `~/google-cloud-sdk/`
- ✅ GCP Project: `skin-demos` (Skinopathy Organization)
- ✅ Billing enabled on GCP project
- ✅ gcloud authenticated with `rakesh@skinopathy.com` account

---

## Quick Deploy (2 Commands)

### 1. Deploy Frontend (Flutter Web App)

```bash
bash deploy-frontend.sh
```

**What it does:**
- Builds Flutter web app via Cloud Build
- Deploys to Cloud Run service: `skinopathy-atopic-dermatitis-demo2-web`
- Serves on port 8080 via nginx
- Configuration: 512Mi memory, 1 CPU, max 10 instances

**Time:** ~5-10 minutes (first build takes longer)

**Output:**
```
🌐 Your frontend is live at:
   https://skinopathy-atopic-dermatitis-demo2-web-XXXXXX.us-central1.run.app
```

### 2. Deploy Backend (FastAPI API)

```bash
bash deploy-backend.sh
```

**What it does:**
- Builds backend API via Cloud Build (includes ML models)
- Deploys to Cloud Run service: `skinopathy-atopic-dermatitis-demo2-api`
- Configuration: 8Gi memory, 4 CPU, min 1 instance (always-warm)
- Sets environment variables and database secret
- Requires database connection secret already configured

**Time:** ~10-15 minutes (builds ML models, larger image)

**Output:**
```
🌐 Your API is live at:
   https://skinopathy-atopic-dermatitis-demo2-api-XXXXXX.us-central1.run.app

📚 API Docs:
   https://skinopathy-atopic-dermatitis-demo2-api-XXXXXX.us-central1.run.app/api/v1/docs
```

---

## Authentication

### First Run (Browser Required)

If this is your first deployment, gcloud will prompt:

```
❌ Not authenticated. Running: gcloud auth login
```

**What to do:**
1. Click the browser link shown
2. Sign in with `rakesh@skinopathy.com`
3. Grant permissions when prompted
4. Copy the verification code
5. Paste it back into the terminal

### Subsequent Runs

Once authenticated, the scripts will use cached credentials:
- ✅ No browser prompt needed
- ✅ Deploys automatically
- ✅ Can be scheduled/automated

---

## After Deployment

### View Logs

```bash
# Frontend logs
gcloud run services logs read skinopathy-atopic-dermatitis-demo2-web --region us-central1

# Backend logs
gcloud run services logs read skinopathy-atopic-dermatitis-demo2-api --region us-central1
```

### Manage via Console

- **Frontend**: https://console.cloud.google.com/run/detail/us-central1/skinopathy-atopic-dermatitis-demo2-web
- **Backend**: https://console.cloud.google.com/run/detail/us-central1/skinopathy-atopic-dermatitis-demo2-api

### Test the App

1. Open frontend URL in browser
2. Upload an image
3. Fill out the 12-question questionnaire
4. Submit and wait for results

The frontend will automatically call the backend API to:
- Run CNN analysis (EfficientNet-B7)
- Run Vision AI analysis (Gemini 2.5 Flash + RAG)
- Generate dual reports (user + HCP)

---

## Troubleshooting

### "Authentication failed"

```bash
# Re-authenticate
gcloud auth login

# Set account if multiple exist
gcloud config set account rakesh@skinopathy.com

# Set project
gcloud config set project skin-demos
```

### "Container image not found"

The Cloud Build might still be building. Check progress:

```bash
gcloud builds list --limit 5
```

### "Service failed to start"

Check logs for errors:

```bash
# Frontend
gcloud run services logs read skinopathy-atopic-dermatitis-demo2-web --limit 50

# Backend
gcloud run services logs read skinopathy-atopic-dermatitis-demo2-api --limit 50
```

### "Database connection failed"

Verify the secret exists:

```bash
gcloud secrets list | grep skinopathy-ad-db-connection

# View secret value (for debugging)
gcloud secrets versions access latest --secret=skinopathy-ad-db-connection
```

---

## Cost Estimate

### Frontend Service
- **Memory:** 512Mi @ ~$0.00001667/hour = ~$2/month
- **Requests:** Free tier covers 2M/month
- **Storage:** Minimal (~10MB)
- **Total:** ~$2-3/month

### Backend Service
- **Memory:** 8Gi @ ~$0.0002667/hour = ~$20/month
- **Min Instance:** Always 1 running = ~$15/month
- **Requests:** ~$0.01-0.05 per analysis
- **Storage:** Models (~500MB) + images (~$0.02/GB used)
- **Database:** db-f1-micro = ~$8/month
- **Total:** ~$50-100/month (100 analyses)

---

## Migration Info

**Migration Date:** Jan 15, 2026
**From:** `total-furnace-288818` (Personal GCP Project)
**To:** `skin-demos` (Skinopathy Organization)

**Updated References:**
- Frontend API URL: Now points to new Cloud Run service (42406804042)
- Backend config: Uses `skin-demos-models` bucket
- RAG system: Uses `skin-demos` project for embeddings
- Database: `skinopathy-ad-db` in skin-demos project

---

## Related Documentation

- **README.md** - Project overview and architecture
- **API_DOCUMENTATION.md** - API endpoint reference
- **MIGRATION.md** - Migration details from personal to organization GCP
- **DEPLOYMENT.md** - Old deployment guide (pre-migration)
