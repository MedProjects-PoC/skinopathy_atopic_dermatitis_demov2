# Fast Deployment Guide

## Overview

This guide covers **optimized deployment strategies** that reduce deployment time from **10+ minutes to 2-3 minutes** for code-only changes.

## Deployment Scripts Comparison

| Script | Use Case | Time | Features |
|--------|----------|------|----------|
| `./deploy-gcp.sh` | **Full production deployment** | 10-15 min | Complete infrastructure setup, no caching |
| `./deploy-gcp-fast.sh` | **Fast code-only deploys** | 2-3 min | Smart caching, skip unchanged steps |
| `./deploy-gcp-fast.sh --dev` | **Ultra-fast dev deploys** | 2-3 min | Skip infrastructure, code-only |
| `./deploy-gcp-fast.sh --parallel` | **Parallel frontend + backend** | 5-7 min | Build both simultaneously |

---

## Quick Start

### 1. First Time Setup (Full Deploy)
```bash
# Run ONCE for initial setup
./deploy-gcp.sh
```
This creates:
- Cloud Storage buckets
- Cloud SQL database
- Artifact Registry
- Secrets in Secret Manager

**Time**: 10-15 minutes

---

## Fast Deployment Modes

### 2. Dev Mode (Code-Only Changes) ⚡ FASTEST

**When to use:** You changed Python code in `backend/app/` only

```bash
./deploy-gcp-fast.sh --dev
```

**What it does:**
- ✓ Detects if dependencies changed (smart caching)
- ✓ Uses cached Docker layers if `requirements.txt` unchanged
- ✓ Skips infrastructure setup (SQL, buckets, etc.)
- ✓ Deploys to new revision without switching traffic (safe)

**Time**: 2-3 minutes

**Switch traffic to new revision:**
```bash
~/google-cloud-sdk/bin/gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 \
  --to-latest
```

---

### 3. Skip Build Mode (Config-Only Changes)

**When to use:** You only changed Cloud Run config (memory, CPU, env vars)

```bash
./deploy-gcp-fast.sh --dev --skip-build
```

**What it does:**
- ✓ Skips Docker build entirely
- ✓ Redeploys existing image with new config
- ✓ Updates environment variables, secrets, etc.

**Time**: 30-60 seconds

---

### 4. Parallel Build Mode (Frontend + Backend)

**When to use:** You changed both frontend and backend code

```bash
./deploy-gcp-fast.sh --parallel
```

**What it does:**
- ✓ Builds backend and frontend simultaneously in background
- ✓ Waits for both to complete
- ✓ Deploys both

**Time**: 5-7 minutes (vs 15+ minutes sequential)

---

## Smart Caching

### How It Works

The fast deployment script tracks file hashes:
- `backend/requirements.txt` → Dependency cache
- `backend/Dockerfile` → Build layer cache

**Cached Deploy Example:**
```
🔍 Dependencies changed - full rebuild required
[Only when requirements.txt changed]
```

vs

```
✓ Dependencies unchanged - using cache
[Skips pip install, reuses layers]
```

### Cache Location
Cache hashes stored in `.deploy-cache/`:
- `.deploy-cache/requirements.hash`
- `.deploy-cache/dockerfile.hash`

### Clear Cache
```bash
rm -rf .deploy-cache/
```

---

## Cloud Build Caching (Advanced)

For even faster builds, use the Cloud Build config with native layer caching:

```bash
cd backend
~/google-cloud-sdk/bin/gcloud builds submit --config=cloudbuild-cached.yaml
```

**Features:**
- Pulls previous image as cache
- Uses Docker `--cache-from` flag
- Tags with both `latest` and git SHA
- E2-HIGHCPU-8 machine for parallel builds

**Time**: 3-5 minutes (first build), 1-2 minutes (cached)

---

## Deployment Time Breakdown

### Full Deployment (./deploy-gcp.sh)
```
[1/9] Auth check           5s
[2/9] Set project          2s
[3/9] Create buckets       10s
[4/9] Artifact Registry    5s
[5/9] Cloud SQL setup      600s (10 min) ⚠️ SLOW
[6/9] Database + user      20s
[7/9] Secret Manager       10s
[8/9] Docker build         300s (5 min) ⚠️ SLOW
[9/9] Deploy to Cloud Run  60s

Total: ~12-15 minutes
```

### Fast Dev Deploy (./deploy-gcp-fast.sh --dev)
```
[1/2] Docker build (cached)  60-90s
[2/2] Deploy                 30-40s

Total: ~2-3 minutes
```

### Skip Build Deploy (--dev --skip-build)
```
[1/1] Deploy (no build)  30-40s

Total: <1 minute
```

---

## Best Practices

### 1. Use Dev Mode for Iteration
During development, always use `--dev` mode:
```bash
# Make code changes
vim backend/app/api/v1/endpoints/upload.py

# Deploy fast
./deploy-gcp-fast.sh --dev

# Test
curl https://your-api-url/health

# Switch traffic when ready
gcloud run services update-traffic ... --to-latest
```

### 2. Full Deploy Only When Needed
Run full deploy `./deploy-gcp.sh` only when:
- First time setup
- Infrastructure changes (SQL, buckets, secrets)
- Production releases

### 3. Use Parallel Builds for Multi-Service Changes
```bash
# Changed both frontend + backend
./deploy-gcp-fast.sh --parallel
```

### 4. Skip Builds for Config-Only Changes
```bash
# Changed only env vars or Cloud Run config
./deploy-gcp-fast.sh --dev --skip-build
```

---

## Troubleshooting

### Cache Not Working?
```bash
# Check cache status
ls -la .deploy-cache/
cat .deploy-cache/requirements.hash

# Clear cache and retry
rm -rf .deploy-cache/
./deploy-gcp-fast.sh --dev
```

### Build Still Slow?
```bash
# Use Cloud Build native caching
cd backend
gcloud builds submit --config=cloudbuild-cached.yaml

# Or use E2-HIGHCPU-8 machine
gcloud builds submit --machine-type=e2-highcpu-8
```

### Dependencies Changed But Not Detected?
```bash
# Force full rebuild
rm -rf .deploy-cache/
./deploy-gcp-fast.sh
```

---

## Performance Metrics

| Scenario | Old Script | Fast Script | Improvement |
|----------|-----------|-------------|-------------|
| **Code change only** | 10-12 min | 2-3 min | **70-80% faster** |
| **Dependency change** | 10-12 min | 5-6 min | **50% faster** |
| **Config change only** | 10-12 min | 30-60 sec | **95% faster** |
| **Frontend + Backend** | 20-25 min | 5-7 min | **75% faster** |

---

## Advanced: CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to GCP
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v0

      - name: Fast Deploy
        run: |
          if git diff HEAD^ --name-only | grep -q requirements.txt; then
            # Dependencies changed - full build
            ./deploy-gcp-fast.sh
          else
            # Code only - dev mode
            ./deploy-gcp-fast.sh --dev
          fi
```

---

## Summary

**For daily development:**
```bash
./deploy-gcp-fast.sh --dev
```

**For production releases:**
```bash
./deploy-gcp.sh
```

**For config tweaks:**
```bash
./deploy-gcp-fast.sh --dev --skip-build
```

**For multi-service changes:**
```bash
./deploy-gcp-fast.sh --parallel
```

---

**Questions?** Check the scripts directly:
- `./deploy-gcp-fast.sh --help`
- Full script: `./deploy-gcp.sh`
