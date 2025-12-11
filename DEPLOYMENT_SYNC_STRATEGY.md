# Deployment Synchronization Strategy

## Branch-to-Cloud-Run Mapping

### Overview
With the new branch structure, we maintain synchronized deployments:

```
┌─────────────────────────────────────────────────────────────┐
│                     GIT BRANCHES                             │
├─────────────────────────────────────────────────────────────┤
│ Main (Production/Stable)                                    │
│ └─ Commit: f497bda (Dec 8)                                  │
│    └─ Status: ✅ Proven stable, no timer issues             │
│    └─ Deployed as: Cloud Run revisions (00018-svv, 00026-txn)
│                                                               │
│ Develop (Features + Fixes)                                  │
│ └─ Commit: d7eb379 (Latest with timer fix)                  │
│    └─ Status: ✅ All 3 features + timer fix verified        │
│    └─ Deployed as: Cloud Run revisions (00019-wgj, 00027-bm4)
└─────────────────────────────────────────────────────────────┘
```

## Deployment Workflow

### Option 1: Deploy Stable Main Branch
**Use when**: Testing stable code, rolling back from issues, or validating baseline

```bash
# 1. Ensure you're on Main branch
git checkout Main
git pull origin Main

# 2. Deploy to Cloud Run
./deploy-gcp-fast.sh --dev

# 3. Switch traffic to new revision (once deployed successfully)
# Frontend:
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-latest

# Backend:
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-latest
```

### Option 2: Deploy Develop Branch (With All Features)
**Use when**: Testing PDF, saliency maps, HCP UI fixes, and timer fix

```bash
# 1. Ensure you're on develop branch
git checkout develop
git pull origin develop

# 2. Deploy to Cloud Run
./deploy-gcp-fast.sh --dev

# 3. Switch traffic to new revision
# Frontend:
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-latest

# Backend:
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-latest
```

## A/B Testing Strategy

### Setup A/B Split (e.g., 90% Main, 10% Develop)
This allows testing new features with a small percentage of traffic.

```bash
# Get latest revision names
MAIN_REV=$(gcloud run services describe skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --format='value(status.traffic[0].revisionName)')
DEV_REV=$(gcloud run services describe skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --format='value(status.traffic[1].revisionName)')

# Split traffic: 90% Main, 10% Develop
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions ${MAIN_REV}=90,${DEV_REV}=10

gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions ${MAIN_REV}=90,${DEV_REV}=10
```

### Monitor Traffic Distribution
```bash
# Frontend
gcloud run services describe skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --format="table(status.traffic[*].revisionName,status.traffic[*].percent)"

# Backend
gcloud run services describe skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --format="table(status.traffic[*].revisionName,status.traffic[*].percent)"
```

### Instant Rollback
```bash
# Revert to Main (all traffic)
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00018-svv=100

gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00026-txn=100
```

## Current Status

### Main Branch (Stable)
- **Deployed as**: Frontend rev 00018-svv (Dec 8), Backend rev 00026-txn (Dec 9)
- **Features**: Core AD analysis (no timer issues)
- **Status**: Currently serving 100% traffic
- **Last commit**: f497bda

### Develop Branch (Features)
- **Deployed as**: Frontend rev 00019-wgj (Dec 11), Backend rev 00027-bm4 (Dec 11)
- **Features**: PDF, saliency maps, HCP UI fix, timer fix
- **Status**: Ready to deploy or A/B test
- **Last commit**: d7eb379 (timer fix applied)

## Deployment Checklist

When deploying from any branch:

- [ ] Checkout correct branch (`git checkout Main` or `git checkout develop`)
- [ ] Pull latest changes (`git pull origin [branch]`)
- [ ] Run fast deploy (`./deploy-gcp-fast.sh --dev`)
- [ ] Wait for Cloud Build to complete (~2-3 minutes)
- [ ] Verify deployment in Cloud Console
- [ ] Run health check: `curl https://[API_URL]/health`
- [ ] Switch traffic to new revision(s)
- [ ] Test in browser (submit image, verify features)
- [ ] Monitor Cloud Logs for errors

## Emergency Procedures

### If Deploy Fails
```bash
# Check Cloud Build logs
gcloud builds log --limit=50

# Check Cloud Run service status
gcloud run services describe [service] --region=us-central1

# If critical: Switch back to known-good revision
gcloud run services update-traffic [service] \
  --region=us-central1 --to-revisions [stable-revision]=100
```

### If Issues Found Post-Deploy
```bash
# Option 1: Immediate rollback (1 second)
gcloud run services update-traffic [service] \
  --region=us-central1 --to-revisions [previous-good-revision]=100

# Option 2: A/B split for diagnosis (keep both running)
gcloud run services update-traffic [service] \
  --region=us-central1 --to-revisions [new-rev]=50,[old-rev]=50
```

## Git Workflow for Merging Branches

When develop branch is verified stable and ready for production:

```bash
# 1. Merge develop into Main
git checkout Main
git pull origin Main
git merge develop
git push origin Main

# 2. Deploy from Main
git checkout Main
./deploy-gcp-fast.sh --dev

# 3. Switch traffic to new Main revision
gcloud run services update-traffic [service] \
  --region=us-central1 --to-latest
```

## Notes

- Cloud Run keeps all revisions indefinitely, allowing instant traffic switching
- No need to rebuild to switch traffic between revisions
- Each deployment creates a new revision; old revisions remain available for rollback
- Use `--dev` flag for fast code-only deploys (2-3 min vs 5-7 min full rebuild)
- Use full deploy when changing dependencies in requirements.txt or pubspec.yaml

