# Deployment Quick Reference

## Current Status

| Component | Branch | Commit | Deployed As | Features | Status |
|-----------|--------|--------|-------------|----------|--------|
| **Main** | Main | f497bda | 00018-svv (web) | Core AD analysis | ✅ Stable |
| | | | 00026-txn (api) | No timer issue | |
| **Develop** | develop | d7eb379 | 00019-wgj (web) | PDF, saliency, HCP UI | ✅ Ready |
| | | | 00027-bm4 (api) | Timer fix applied | |

## Deploy to Cloud Run

### Deploy Main Branch (Stable)
```bash
git checkout Main
git pull
./deploy-gcp-fast.sh --dev
```
Then switch traffic (if needed):
```bash
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-latest

gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-latest
```

### Deploy Develop Branch (All Features + Timer Fix)
```bash
git checkout develop
git pull
./deploy-gcp-fast.sh --dev
```
Then switch traffic:
```bash
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-latest

gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-latest
```

## Quick Traffic Operations

### View Current Traffic Split
```bash
# Frontend
gcloud run services describe skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --format="table(status.traffic[*].revisionName,status.traffic[*].percent)"

# Backend
gcloud run services describe skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --format="table(status.traffic[*].revisionName,status.traffic[*].percent)"
```

### 50/50 A/B Test (Main vs Develop)
```bash
# Frontend
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00018-svv=50,00019-wgj=50

# Backend
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00026-txn=50,00027-bm4=50
```

### 90% Develop, 10% Main (Safe Production Rollout)
```bash
# Frontend
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00019-wgj=90,00018-svv=10

# Backend
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00027-bm4=90,00026-txn=10
```

### 100% Main (Full Rollback)
```bash
# Frontend
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00018-svv=100

# Backend
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00026-txn=100
```

### 100% Develop (Production Switch)
```bash
# Frontend
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00019-wgj=100

# Backend
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00027-bm4=100
```

## Feature Differences

### Main Branch (Stable)
- ✅ Core AD analysis pipeline (CNN + Vision AI)
- ✅ User severity assessment
- ✅ HCP report generation
- ❌ PDF download buttons
- ❌ Activation channel saliency visualization
- ❌ Timer hang fix
- ⚠️ **Timer hangs when switching browser tabs**

### Develop Branch (All Features)
- ✅ Core AD analysis pipeline
- ✅ User severity assessment
- ✅ HCP report generation
- ✅ **PDF download (user + HCP reports)**
- ✅ **Activation channel saliency visualization**
- ✅ **Improved HCP UI (skin tone assessment)**
- ✅ **Timer fix (works correctly with tab switches)**

## Testing Checklist

After deploying, verify:

```bash
# Health check
curl https://skinopathy-atopic-dermatitis-demo2-api-[hash].us-central1.run.app/health

# Upload test image
# 1. Go to https://skinopathy-atopic-dermatitis-demo2-web-[hash].us-central1.run.app
# 2. Upload a test image
# 3. If develop branch:
#    - Verify PDF download buttons appear
#    - Verify saliency map overlay visible
#    - Switch tabs during analysis, verify timer works
# 4. If main branch:
#    - Verify analysis completes
#    - Test timer (expected to show issue when switching tabs)
```

## Emergency Rollback

If critical issue found:

```bash
# Immediate rollback to Main (1 second downtime)
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00018-svv=100

gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00026-txn=100

# Verify traffic switched
gcloud run services describe skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --format="table(status.traffic[*].revisionName)"
```

## Git Workflow

### Switch Branch
```bash
git checkout Main    # Switch to stable
git checkout develop # Switch to features
```

### Pull Latest
```bash
git pull origin Main    # Update from remote
git pull origin develop
```

### View Branch Info
```bash
git branch -v          # Show all branches and status
git log --oneline -5   # Show recent commits
git log Main -1        # Show Main branch tip
git log develop -1     # Show develop branch tip
```

## Useful Commands

```bash
# Check current branch
git branch --show-current

# See what changed between branches
git diff Main develop

# See deploy script branch info
./deploy-gcp-fast.sh --help  # Shows description

# List all Cloud Run revisions
gcloud run revisions list --service=skinopathy-atopic-dermatitis-demo2-web --region=us-central1
```

## Notes

- Deployments are **instantaneous for traffic switching** (no rebuild needed)
- Old revisions remain in Cloud Run forever - you can rollback anytime
- Code-only changes take ~2-3 minutes with `--dev` flag
- Dependency changes take ~5-7 minutes (full Docker build)
- Both Main and develop branches are kept up-to-date in git
- No separate infrastructure needed - same URLs, different revisions
