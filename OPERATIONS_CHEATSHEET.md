# Operations Cheatsheet - For Engineers

Quick reference for daily operations on Skinopathy Atopic Dermatitis Demo v2.

---

## 🚀 Most Common Commands

### Check Current Status
```bash
# What's running right now?
gcloud run services describe skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --format="value(status.traffic[0].revisionName,status.traffic[0].percent)"

gcloud run services describe skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --format="value(status.traffic[0].revisionName,status.traffic[0].percent)"
```

### Switch to Stable (Main - no new features)
```bash
# Emergency rollback or switch to stable version
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00018-svv=100

gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00026-txn=100
```

### Switch to Features (Develop - all features + timer fix)
```bash
# Switch to latest with PDF, saliency maps, UI improvements
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00019-wgj=100

gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00027-bm4=100
```

### A/B Test (50/50 split)
```bash
# Test both versions with equal traffic
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00018-svv=50,00019-wgj=50

gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00026-txn=50,00027-bm4=50
```

### Gradual Rollout (90% new, 10% old for safety)
```bash
# Confidence test: run features for most users, fallback to stable for 10%
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00019-wgj=90,00018-svv=10

gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00027-bm4=90,00026-txn=10
```

---

## 📊 Understanding the Versions

| Property | Main (Stable) | Develop (Features) |
|----------|---------------|-------------------|
| **Frontend Revision** | 00018-svv | 00019-wgj |
| **Backend Revision** | 00026-txn | 00027-bm4 |
| **Features** | Core analysis only | PDF, saliency maps, HCP UI improvements |
| **Timer Fix** | ❌ Has bug when switching tabs | ✅ Fixed |
| **Best For** | Proven reliability | Testing new features |

---

## 🔧 Deployment (Code Updates)

Only needed when code changes. Traffic switching is instant.

### Deploy Main Branch
```bash
git checkout Main
git pull origin Main
./deploy-gcp-fast.sh --dev
```

### Deploy Develop Branch
```bash
git checkout develop
git pull origin develop
./deploy-gcp-fast.sh --dev
```

**Note**: After deploy, traffic stays on old revision until you manually switch.

---

## 🐛 Troubleshooting

### Service Is Down
1. Check if revision exists: `gcloud run revisions list --service=skinopathy-atopic-dermatitis-demo2-web --region=us-central1`
2. Switch to known-good revision:
   ```bash
   gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
     --region=us-central1 --to-revisions 00018-svv=100
   ```
3. Check logs: `gcloud run services logs read skinopathy-atopic-dermatitis-demo2-web --region=us-central1 --limit=50`

### API Errors
```bash
# Check backend health
curl https://skinopathy-atopic-dermatitis-demo2-api-oxp54sxycq-uc.a.run.app/health

# Check logs
gcloud run services logs read skinopathy-atopic-dermatitis-demo2-api --region=us-central1 --limit=50
```

### PDF Download Not Working
- Check if running develop (00019-wgj / 00027-bm4) - Main doesn't have PDF feature
- Try main branch version if feature is broken

### Timer Hangs When Switching Tabs
- This is a known issue in Main branch
- Switch to develop branch (00019-wgj / 00027-bm4) which has the fix

---

## 📋 Common Scenarios

### Test New PDF Feature
```bash
# Switch to develop which has PDF
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00019-wgj=100
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00027-bm4=100

# Upload image to https://skinopathy-atopic-dermatitis-demo2-web-890999745336.us-central1.run.app
# Verify PDF download buttons appear
```

### Test Stability (No New Features)
```bash
# Switch to Main which is proven stable
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-web \
  --region=us-central1 --to-revisions 00018-svv=100
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00026-txn=100
```

### Monitor API Performance Difference
```bash
# Run develop for 1 hour and capture metrics
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00027-bm4=100

# Check Cloud Monitoring for metrics
# After 1 hour, compare with Main baseline

# Switch back if needed
gcloud run services update-traffic skinopathy-atopic-dermatitis-demo2-api \
  --region=us-central1 --to-revisions 00026-txn=100
```

---

## 🔑 Key Facts

- **Same URLs**: Both versions use the same URLs (`https://skinopathy-atopic-dermatitis-demo2-web-...run.app`)
- **No Downtime**: Traffic switching takes ~1 second, services stay online
- **No Rebuild**: Old revisions are always available - just switch traffic
- **Revision Lifespan**: Revisions are kept forever in Cloud Run
- **Instant Rollback**: Can rollback to any old revision in seconds
- **A/B Testing**: Native support for traffic splitting without load balancer

---

## 📞 Help

- **Docs**: See README.md and DEPLOYMENT_SYNC_STRATEGY.md for full details
- **Git**: Use `git log --oneline -20` to see recent changes
- **Logs**: Always check `gcloud run services logs read` first before assuming failure
- **Status Dashboard**: https://console.cloud.google.com/run?project=total-furnace-288818

---

## ⚠️ Do NOT Do

- ❌ Don't manually edit production configs - use git + deploy script
- ❌ Don't assume revision will auto-scale - set min/max instances if needed
- ❌ Don't delete old revisions - they enable instant rollback
- ❌ Don't mix frontend and backend versions - always update both together
- ❌ Don't commit directly - use branches and PR process

---

**Last Updated**: Dec 11, 2025
**For Questions**: Check git history with `git log --oneline` or ask team
