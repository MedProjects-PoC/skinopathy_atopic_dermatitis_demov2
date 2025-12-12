# GCP to Azure Migration Guide

Complete migration strategy for moving Skinopathy Atopic Dermatitis from GCP to Azure.

---

## Executive Summary

**Current GCP Setup:**
- Frontend: Cloud Run (Flutter web)
- Backend: Cloud Run (FastAPI)
- Database: Cloud SQL (PostgreSQL)
- Storage: Cloud Storage (GCS)
- AI/ML: Vertex AI (Gemini, Text Embeddings)
- RAG: Vertex AI Vector Search
- Model: EfficientNet-B7 (TensorFlow, stored in GCS)

**Easiest Azure Equivalent:**
- Frontend: Azure Container Instances or App Service
- Backend: Azure Container Instances or App Service
- Database: Azure Database for PostgreSQL
- Storage: Azure Blob Storage
- AI/ML: Azure OpenAI, Azure AI Services
- RAG: Azure Cognitive Search (Vector Search)
- Model: Azure Container Registry (same TensorFlow model)

**Estimated Effort:** 2-4 weeks
**Recommended Approach:** Lift-and-shift with minimal code changes

---

## RAG System Details

Yes, there IS a RAG system on GCP that will need migration:

### Current RAG Setup
```
Location: backend/app/rag/
Files:
  - rag_config.py (12KB) - Configuration for Vertex AI Vector Search
  - rag_service.py (6.9KB) - RAG service implementation

What it does:
  • Uses Vertex AI Text Embeddings (text-embedding-005 model)
  • Vector Search with Vertex AI Vector Search index
  • Stores embeddings in GCP Vertex AI
  • Includes AD clinical knowledge base (Hanifin & Rajka criteria, EASI scoring, etc.)
  • Provides context to Gemini 2.5 Flash for better diagnoses

Current Features:
  ✓ Retrieval of top-5 similar clinical documents
  ✓ Augmentation of Vision AI prompts with RAG context
  ✓ Medical guideline retrieval for accuracy
```

### Files Using RAG
```
backend/app/agents/vision_agent.py
  - Line ~145: Calls RAG service for clinical knowledge
  - Used to augment Gemini prompts with retrieved documents
```

---

## Step-by-Step Migration Plan

### Phase 1: Infrastructure Setup (Days 1-3)

#### 1.1 Azure Container Registry Setup
```bash
# Create container registry
az acr create --resource-group <your-rg> --name <registry-name> --sku Basic

# Tag and push images
docker tag skinopathy-atopic-dermatitis-demo2-web <registry>/skinopathy-web:latest
docker tag skinopathy-atopic-dermatitis-demo2-api <registry>/skinopathy-api:latest
az acr push --name <registry> --image skinopathy-web:latest
az acr push --name <registry> --image skinopathy-api:latest
```

#### 1.2 Database Migration
```bash
# Create Azure Database for PostgreSQL
az postgres server create \
  --resource-group <your-rg> \
  --name skinopathy-db \
  --location eastus \
  --admin-user dbadmin \
  --admin-password <strong-password> \
  --sku-name B_Gen5_2

# Migrate data from GCP Cloud SQL
# Option A: pg_dump from GCP → psql to Azure
pg_dump -h <gcp-cloud-sql-ip> -U postgres <database> | psql -h <azure-host> -U <user>

# Option B: Use Azure Database Migration Service (DMS)
# Recommended for large databases
```

#### 1.3 Storage Migration
```bash
# Create Azure Blob Storage
az storage account create \
  --resource-group <your-rg> \
  --name skinopathystorage \
  --location eastus

# Copy GCS bucket to Azure Blob
# Use Azure Storage Explorer or azcopy
azcopy copy "gs://total-furnace-288818-models/*" \
  "https://<storage-account>.blob.core.windows.net/models/" \
  --recursive
```

### Phase 2: Deploy Applications (Days 4-5)

#### 2.1 Deploy Backend API
```bash
# Create App Service (recommended over Container Instances for production)
az appservice plan create \
  --name skinopathy-plan \
  --resource-group <your-rg> \
  --is-linux --sku B2

az webapp create \
  --resource-group <your-rg> \
  --plan skinopathy-plan \
  --name skinopathy-api \
  --deployment-container-image-name <registry>/skinopathy-api:latest

# Configure environment variables
az webapp config appsettings set \
  --resource-group <your-rg> \
  --name skinopathy-api \
  --settings \
    DATABASE_URL="postgresql://<user>:<pass>@<azure-host>:5432/<db>" \
    STORAGE_ACCOUNT="<azure-storage-account>" \
    STORAGE_KEY="<azure-storage-key>" \
    AZURE_OPENAI_KEY="<your-azure-openai-key>" \
    AZURE_OPENAI_ENDPOINT="<your-endpoint>" \
    AZURE_SEARCH_ENDPOINT="<your-search-endpoint>"
```

#### 2.2 Deploy Frontend
```bash
az webapp create \
  --resource-group <your-rg> \
  --plan skinopathy-plan \
  --name skinopathy-web \
  --deployment-container-image-name <registry>/skinopathy-web:latest

# Configure API endpoint
az webapp config appsettings set \
  --resource-group <your-rg> \
  --name skinopathy-web \
  --settings API_URL="https://skinopathy-api.azurewebsites.net"
```

### Phase 3: RAG System Migration (Days 3-4, parallel with Phase 1)

#### 3.1 Replace Vertex AI with Azure Cognitive Search

**What to change:**

File: `backend/app/rag/rag_config.py`
```python
# BEFORE (GCP Vertex AI)
embedding_model: str = "text-embedding-005"  # Vertex AI
vector_search_index: str = "ad_knowledge_vertex"

# AFTER (Azure)
embedding_model: str = "text-embedding-3-small"  # Azure OpenAI
vector_search_endpoint: str = "https://<search-service>.search.windows.net"
vector_search_admin_key: str = os.getenv("AZURE_SEARCH_ADMIN_KEY")
```

File: `backend/app/rag/rag_service.py`
```python
# BEFORE: from google.cloud import aiplatform
# AFTER: from azure.search.documents import SearchClient
#        from openai import AzureOpenAI

# Replace Vertex AI Vector Search calls with Azure Cognitive Search
```

#### 3.2 Setup Azure Cognitive Search
```bash
# Create Azure Cognitive Search service
az search service create \
  --resource-group <your-rg> \
  --name skinopathy-search \
  --sku standard

# Create index for medical knowledge base
# Index must have:
#   - Vector field for embeddings (1536 dimensions for Azure OpenAI)
#   - Text field for source content
#   - Metadata fields (source_id, title, publication_year, etc.)

# Use Azure portal or REST API to create index
```

#### 3.3 Ingest Knowledge Base
```python
# Python script to populate Cognitive Search with AD knowledge base
from azure.search.documents import SearchClient
from openai import AzureOpenAI

# 1. Generate embeddings using Azure OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# 2. Create embeddings for each knowledge base item
# 3. Upload to Cognitive Search
```

### Phase 4: Model Deployment (Day 2, parallel)

#### 4.1 Store EfficientNet-B7 Model
```bash
# Already have model in Azure Blob Storage from Phase 1.3
# Update backend code to load from Azure Blob:

from azure.storage.blob import BlobClient

model_url = "https://<storage-account>.blob.core.windows.net/models/efficientnet_b7_ad.h5"
blob = BlobClient.from_blob_url(model_url, credential=account_key)
model_bytes = blob.download_blob().readall()
# Load model from bytes
```

---

## Code Changes Required

### Summary
- **rag_config.py**: Update 4 lines (Vertex AI → Azure Cognitive Search)
- **rag_service.py**: Update 3 methods (~30 lines total)
- **vision_agent.py**: No changes needed (same RAG interface)
- **main backend.py**: Update storage client initialization (~5 lines)
- **frontend config**: Update API endpoint URL (1 line)

**Total code changes**: ~50 lines across 5 files

### Specific Changes

#### 1. rag_config.py
```python
# Line 15-16: Change project config
-   project_id: str = os.getenv("GCP_PROJECT_ID", "total-furnace-288818")
+   azure_subscription: str = os.getenv("AZURE_SUBSCRIPTION_ID")
+   azure_resource_group: str = os.getenv("AZURE_RESOURCE_GROUP", "skinopathy-rg")

# Line 20: Change embedding model
-   embedding_model: str = "text-embedding-005"  # Vertex AI
+   embedding_model: str = "text-embedding-3-small"  # Azure OpenAI

# Add new fields
+   azure_search_endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT")
+   azure_search_admin_key: str = os.getenv("AZURE_SEARCH_ADMIN_KEY")
```

#### 2. rag_service.py
```python
# Replace Vertex AI imports with Azure
from azure.search.documents import SearchClient
from openai import AzureOpenAI

# Update _initialize_embeddings_client() method
# Update retrieve_documents() method
# Update ingest_knowledge_base() method
```

#### 3. Backend initialization
```python
# In backend/app/main.py or storage_service.py
-   from google.cloud import storage as gcs
+   from azure.storage.blob import BlobServiceClient

-   gcs_client = gcs.Client()
+   blob_client = BlobServiceClient.from_connection_string(
+       os.getenv("AZURE_STORAGE_CONNECTION_STRING")
+   )
```

---

## Service Comparison

| Feature | GCP | Azure | Migration Effort |
|---------|-----|-------|------------------|
| Container Hosting | Cloud Run | App Service / Container Instances | Low - same Docker images |
| Database | Cloud SQL (PostgreSQL) | Azure Database for PostgreSQL | Low - pg_dump compatible |
| Object Storage | Cloud Storage (GCS) | Blob Storage | Low - both object storage |
| Vector Search | Vertex AI Vector Search | Cognitive Search | Medium - API differences |
| Text Embeddings | Vertex AI (text-embedding-005) | Azure OpenAI (text-embedding-3-small) | Low - drop-in replacement |
| LLM | Gemini 2.5 Flash | GPT-4 Turbo / GPT-3.5 Turbo | Low - same prompts work |
| Model Storage | GCS | Blob Storage | Low - same format |
| **Total Effort** | - | - | **2-4 weeks** |

---

## Cost Comparison

### GCP Current
- Cloud Run: ~$20-50/month
- Cloud SQL: ~$30-50/month
- Vertex AI embeddings: ~$0.50/month
- Cloud Storage: ~$5-10/month
- **Total: ~$55-110/month**

### Azure Equivalent
- App Service (B2 tier): ~$50-70/month
- Azure Database for PostgreSQL: ~$40-60/month
- Azure OpenAI embeddings: ~$1-2/month
- Blob Storage: ~$5-10/month
- Cognitive Search (Standard): ~$250/month
- **Total: ~$346-392/month** (higher due to Cognitive Search)

**Note**: Cognitive Search cost can be reduced with:
- Smaller replica count (currently 1)
- Premium tier only if needed
- Scheduled indexing vs real-time

---

## Timeline

```
Week 1 (Days 1-5):
  - Days 1-2: Infrastructure setup (database, storage, registry)
  - Days 3-4: RAG system setup (Cognitive Search, embeddings)
  - Day 5: Deploy applications

Week 2 (Days 6-10):
  - Days 6-7: Testing and validation
  - Days 8-9: Load testing and optimization
  - Day 10: Go-live preparation

Week 3 (Days 11-15):
  - Day 11: Cutover day
  - Days 12-15: Monitoring and issue resolution
```

---

## Rollback Plan

Keep GCP running in parallel for 2 weeks:
1. Route 90% traffic to Azure, 10% to GCP (using Traffic Manager)
2. Monitor error rates, latency, logs
3. If critical issue on Azure → switch 100% back to GCP
4. After 2 weeks with <0.01% error rate → decommission GCP

---

## Post-Migration Cleanup

```bash
# Delete GCP resources (optional, for cost savings)
gcloud run services delete skinopathy-atopic-dermatitis-demo2-web
gcloud run services delete skinopathy-atopic-dermatitis-demo2-api
gsutil -m rm -r gs://total-furnace-288818-models/
gcloud sql instances delete skinopathy-db
```

---

## Questions & Answers

**Q: Will the RAG system work exactly the same?**
A: 95% same functionality. Azure Cognitive Search is more robust but slightly different API. Vision AI prompts will work unchanged with Azure OpenAI.

**Q: Do I need to retrain the EfficientNet model?**
A: No, TensorFlow models are platform-agnostic. Same model file works on Azure.

**Q: Can I do gradual migration?**
A: Yes - run both in parallel with Traffic Manager for gradual switchover.

**Q: What about CI/CD?**
A: Update GitHub Actions to push to Azure Container Registry instead of GCP Artifact Registry.

---

## Resources

- [Azure App Service Documentation](https://learn.microsoft.com/en-us/azure/app-service/)
- [Azure Database for PostgreSQL](https://learn.microsoft.com/en-us/azure/postgresql/)
- [Azure Cognitive Search](https://learn.microsoft.com/en-us/azure/search/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure Storage](https://learn.microsoft.com/en-us/azure/storage/)
- [Azure DMS (Database Migration Service)](https://learn.microsoft.com/en-us/azure/dms/)

---

**Summary**: This is a straightforward migration. The RAG system exists and will work great on Azure with Cognitive Search. Estimate 2-4 weeks for complete migration with parallel running for safety.
