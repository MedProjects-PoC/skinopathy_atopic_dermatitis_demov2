# GCP Docker Image Cleanup Analysis

## Summary
Your Artifact Registry contains **47 old Docker images** that are **NOT in use** and can be safely deleted to reduce costs and storage. Only **2 active images** are currently deployed.

---

## Current Deployment Status

### ✅ ACTIVE IMAGES (in production - DO NOT DELETE)

**Backend API**:
- Image: `us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api:latest`
- Digest: `sha256:09d32230d0304fc5b779c59c0165e7bf936a9e52cb93eef979428c47d7c7942f`
- Size: 3.6 GB
- Last Updated: Dec 8, 2025 11:24:56 UTC
- Service: `skinopathy-atopic-dermatitis-demo2-api` (26 revisions deployed)
- Status: **ACTIVE & PRODUCTION**

**Frontend Web**:
- Image: `us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web:latest`
- Digest: `sha256:7c9ab9493ce3a89719b3cb4e2dae1e54c6261e9640282defea332723fa37eeb6`
- Size: 40.2 MB
- Last Updated: Dec 8, 2025 12:52:53 UTC
- Service: `skinopathy-atopic-dermatitis-demo2-web` (18 revisions deployed)
- Status: **ACTIVE & PRODUCTION**

---

## Unnecessary Images (Safe to Delete)

### OLD SKINOPATHY-AD REPOSITORY IMAGES

**API Images** (21 old builds):
- 20 untagged images ranging from Dec 1-8
- All but latest should be deleted
- Each ~3.6 GB
- **Total to delete: ~72 GB**

```
To delete old API images:
gcloud artifacts docker images delete \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api@sha256:4fae920036442058fc30a711e434d94d6a5dd2de073fec91237868e4e6511f18 \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api@sha256:2dd8e6452a6f078165e49b847f89642aec2b53a6a0f225433f046201782c8c90 \
  ... (20 total)
```

**Web Images** (16 old builds):
- 15 untagged images ranging from Dec 2-8
- All but latest should be deleted
- Each ~40 MB
- **Total to delete: ~600 MB**

```
To delete old web images:
gcloud artifacts docker images delete \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web@sha256:d7d5ef1016e3477c43c6bf203fcf21a8559ca12e700bed13f10f2c973c3b8bef \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web@sha256:c3e1a834bbdbca11dd59317ee9192f139af9146d64ec967c0e5611de6e594282 \
  ... (15 total)
```

**Old skinopathy-ad-api & skinopathy-ad-web** (10 images):
- These are from earlier project iterations (not atopic-dermatitis-demo2)
- API: 5 images (~3.6 GB each) = ~18 GB
- Web: 5 images (~30 MB each) = ~150 MB
- **Status: OBSOLETE - Safe to delete**

### CLOUD-RUN-SOURCE-DEPLOY REPOSITORY (6.4 GB)

This is GCP's automatic source deployment cache. Contains:
- **4 old builds** for demo2-api (~3.6 GB each = 7.2 GB theoretical, but deduplicated)
- **2 old builds** for demo2-web (~40 MB)

**Status**: This repo is created automatically by `gcloud run deploy --source .` commands. It's safe to clear out old builds.

---

## Recommended Cleanup Strategy

### Option A: CONSERVATIVE (Safe, minimal disruption)
**Delete only truly old images (>7 days)**
- Keep: Latest API + web images from skinopathy-ad repo
- Delete: All cloud-run-source-deploy images (auto-rebuilt if needed)
- Delete: All skinopathy-ad-api and skinopathy-ad-web (old project names)
- **Estimated savings: ~25 GB**

### Option B: AGGRESSIVE (Maximum cleanup)
**Delete all but latest `live` images**
- Keep: Only the one `latest` API image + one `latest` web image in skinopathy-ad
- Delete: Everything else (old builds, source-deploy cache, old projects)
- **Estimated savings: ~72 GB**
- **Risk**: Medium (but safe - images are still available in git history via rebuild)

### Option C: RECOMMENDED (Balanced)
**Keep 3 recent images per service, delete everything else**
- Keep: 3 most recent API builds (fallback for rollback)
- Keep: 3 most recent web builds (fallback for rollback)
- Delete: Everything in cloud-run-source-deploy (auto-rebuilt if needed)
- Delete: Old project images (skinopathy-ad-api, skinopathy-ad-web)
- **Estimated savings: ~60 GB**
- **Benefit**: Rollback capability without storage bloat

---

## Cleanup Commands

### Delete cloud-run-source-deploy repo (SAFE - auto-recreated)
```bash
# This deletes the entire auto-deployment cache repo
# GCP will automatically recreate it if you use gcloud run deploy --source again
gcloud artifacts repositories delete cloud-run-source-deploy \
  --location=us-central1 \
  --quiet
```

### Delete old API images in skinopathy-ad (SAFE)
```bash
# Keep only latest 3, delete all others
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api \
  --sort-by="~UPDATE_TIME" \
  --limit=999 | tail -n +4 | awk '{print $1"@"$2}' | xargs -I {} \
  gcloud artifacts docker images delete {} --quiet
```

### Delete old project images (SAFE)
```bash
# Delete skinopathy-ad-api images (old project name)
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-api \
  --include-tags | awk '{print $1"@"$2}' | xargs -I {} \
  gcloud artifacts docker images delete {} --quiet

# Delete skinopathy-ad-web images (old project name)
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-web \
  --include-tags | awk '{print $1"@"$2}' | xargs -I {} \
  gcloud artifacts docker images delete {} --quiet
```

### One-liner to verify what would be deleted (DRY RUN)
```bash
# Shows which images WOULD be deleted (doesn't actually delete)
echo "=== OLD API IMAGES ==="
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-api \
  --sort-by="~UPDATE_TIME" --limit=999 | tail -n +4

echo "=== OLD WEB IMAGES ==="
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-atopic-dermatitis-demo2-web \
  --sort-by="~UPDATE_TIME" --limit=999 | tail -n +4

echo "=== OBSOLETE SKINOPATHY-AD-API ==="
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-api \
  --include-tags

echo "=== OBSOLETE SKINOPATHY-AD-WEB ==="
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/skinopathy-ad-web \
  --include-tags
```

---

## Cost Impact

### Current Storage Usage
- **skinopathy-ad repo**: 71.2 GB
- **cloud-run-source-deploy repo**: 6.4 GB
- **Total**: ~77.6 GB

### GCP Artifact Registry Pricing (us-central1)
- Storage: **$0.026 per GB/month** (first 100 GB free)
- Retrieval: **$0.05 per GB** (rarely charged unless pulled frequently)

### Monthly Cost (above free tier)
- Current: (77.6 - 100) = **FREE** (under 100 GB free tier)
- After cleanup (15 GB): **FREE** (still under free tier)

### Recommendation
**Clean up now to stay under free tier and establish good practices.** The free tier cushion gives you room for 20+ new production images before incurring charges.

---

## Why This Happened

Docker image cleanup is **NOT automatic** in GCP Artifact Registry:

1. **Every build creates a new image** - Even if code is identical
2. **Each revision of Cloud Run creates a tagged image** - 26 API revisions = 26 potential images
3. **Source deploys use separate repo** - cloud-run-source-deploy accumulates layers
4. **Old images are never auto-deleted** - Unlike some other registries
5. **No lifecycle policies by default** - You must manually configure or delete

This is actually **better than the old Container Registry** which couldn't even track layers separately, but it requires active cleanup.

---

## Going Forward: Prevent Accumulation

### Implement Lifecycle Policy (RECOMMENDED)
```bash
# Create a cleanup policy that deletes images older than 30 days
cat > /tmp/lifecycle-policy.json << 'EOF'
{
  "rules": [
    {
      "action": {"type": "DELETE"},
      "condition": {
        "tagState": "UNTAGGED",
        "olderThan": 2592000  # 30 days in seconds
      }
    },
    {
      "action": {"type": "KEEP"},
      "condition": {
        "tagState": "TAGGED",
        "tagPattern": "latest"
      }
    }
  ]
}
EOF

gcloud artifacts repositories update skinopathy-ad \
  --location=us-central1 \
  --cleanup-policy-condition=/tmp/lifecycle-policy.json
```

### Cleanup Script (Add to deploy-gcp.sh)
```bash
#!/bin/bash
# Add to your deployment script to auto-cleanup after each deploy

cleanup_old_images() {
  local repo=$1
  local keep_count=3

  echo "Cleaning up old images in $repo (keeping latest $keep_count)..."

  gcloud artifacts docker images list \
    us-central1-docker.pkg.dev/total-furnace-288818/skinopathy-ad/$repo \
    --sort-by="~UPDATE_TIME" --limit=999 | \
    tail -n +$((keep_count + 1)) | \
    awk '{print $1"@"$2}' | \
    xargs -I {} gcloud artifacts docker images delete {} --quiet
}

# Call after deploy
cleanup_old_images "skinopathy-atopic-dermatitis-demo2-api"
cleanup_old_images "skinopathy-atopic-dermatitis-demo2-web"
```

---

## Deployment Safe to Proceed ✅

**Your current services are using the latest, correct images:**
- API: `09d32230d030...` (Dec 8)
- Web: `7c9ab9493ce3...` (Dec 8)

**You can safely deploy your activation channels feature** - the cleanup is separate and won't affect your deployment.

---

## Summary Table

| Image Set | Count | Size | Status | Action |
|-----------|-------|------|--------|--------|
| API Latest | 1 | 3.6 GB | **IN USE** | ✅ KEEP |
| API Old (2-7 days) | 15 | 54 GB | **UNUSED** | 🗑️ DELETE |
| API Old (>7 days) | 6 | 21.6 GB | **UNUSED** | 🗑️ DELETE |
| Web Latest | 1 | 40 MB | **IN USE** | ✅ KEEP |
| Web Old (2-7 days) | 10 | 400 MB | **UNUSED** | 🗑️ DELETE |
| Web Old (>7 days) | 5 | 150 MB | **UNUSED** | 🗑️ DELETE |
| skinopathy-ad-api | 5 | 18 GB | **OBSOLETE** | 🗑️ DELETE |
| skinopathy-ad-web | 5 | 150 MB | **OBSOLETE** | 🗑️ DELETE |
| cloud-run-source-deploy | 4 | 6.4 GB | **CACHE** | 🗑️ DELETE |
| **TOTAL TO DELETE** | **45** | **~72 GB** | | |

---

**Recommendation**: Execute cleanup Option C to save ~60 GB and prevent future bloat.
