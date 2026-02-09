# LegalMind Deployment Fixes Summary

Date: February 5, 2026

## Issues Fixed

### 1. **Vertex AI Authentication Error (403 - ACCESS_TOKEN_SCOPE_INSUFFICIENT)**

**Problem:** The backend was receiving 403 errors when trying to call Vertex AI because the service account didn't have the required IAM role.

**Files Modified:**
- `backend/config/settings.py` - Updated validation to not require API key when using Vertex AI
- `backend/services/gemini_service.py` - Improved error handling for Vertex AI authentication
- `setup-gcp.ps1` - Added Vertex AI APIs and IAM roles
- `setup-gcp.sh` - Added Vertex AI APIs and IAM roles

**What was changed:**

1. **Settings Validation (`config/settings.py`)**
   - `gemini_api_key` validator now allows empty key when Vertex AI is enabled
   - `validate_settings()` function now checks `use_vertex_ai` flag before requiring API key
   - Better error messages when credentials are missing

2. **Gemini Service (`services/gemini_service.py`)**
   - Improved authentication flow to fail clearly if Vertex AI initialization fails
   - Removed silent fallback to public API that was causing scope errors
   - Added detailed error messages about required IAM roles

3. **Setup Scripts**
   - Added `aiplatform.googleapis.com` to enabled APIs
   - Added `generativeai.googleapis.com` to enabled APIs  
   - Added `roles/aiplatform.user` to service account roles

### 2. **Backend Staying Active & Accessible**

The backend uses proper async/await patterns in the lifespan manager to handle startup/shutdown without blocking.

**Key components:**
- ✅ Health check endpoint at `/api/health`
- ✅ Timeout handling with 10-second initialization window
- ✅ Proper async cleanup on shutdown
- ✅ Python 3.11-slim Docker image for faster cold starts

---

## Action Items (IMMEDIATE - DO THIS NOW)

### Option 1: Run Quick Fix Script (Recommended)

**On Windows (PowerShell):**
```powershell
./fix-vertex-ai-permissions.ps1 -ProjectId "legalmind-486106"
```

**On Linux/Mac:**
```bash
chmod +x fix-vertex-ai-permissions.sh
./fix-vertex-ai-permissions.sh legalmind-486106
```

### Option 2: Run Manual Commands

```bash
# Set your project
gcloud config set project legalmind-486106

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativeai.googleapis.com

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding legalmind-486106 \
  --member="serviceAccount:legalmind-backend@legalmind-486106.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Step 2: Redeploy Backend

```bash
# From the project root
docker build -t gcr.io/legalmind-486106/legalmind-backend:latest .
docker push gcr.io/legalmind-486106/legalmind-backend:latest

# Deploy with proper configuration
gcloud run deploy legalmind-backend \
  --image gcr.io/legalmind-486106/legalmind-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 60 \
  --min-instances 1 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=legalmind-486106,USE_VERTEX_AI=true,DEBUG=false"
```

### Step 3: Verify Deployment

```bash
# Check service status
gcloud run services describe legalmind-backend --region=us-central1

# Check logs
gcloud run services logs read legalmind-backend --region=us-central1 --limit=20

# Test health endpoint
curl https://legalmind-backend-YOUR-ID.us-central1.run.app/api/health
```

---

## Files Created

1. **fix-vertex-ai-permissions.ps1** - PowerShell script to fix permissions
2. **fix-vertex-ai-permissions.sh** - Bash script to fix permissions
3. **docs/DEPLOYMENT_TROUBLESHOOTING.md** - Comprehensive troubleshooting guide

---

## Files Modified

1. **backend/config/settings.py**
   - Line ~70: Updated `validate_api_key()` to allow empty key with Vertex AI
   - Line ~145: Updated `validate_settings()` to check use_vertex_ai flag

2. **backend/services/gemini_service.py**
   - Line ~203: Improved `_configure_api()` error handling and messaging
   - Removed silent fallback that was causing 403 errors

3. **setup-gcp.ps1**
   - Added `aiplatform.googleapis.com` and `generativeai.googleapis.com` to APIs
   - Added `roles/aiplatform.user` to service account roles

4. **setup-gcp.sh**
   - Added `aiplatform.googleapis.com` and `generativeai.googleapis.com` to APIs
   - Added `roles/aiplatform.user` to service account roles

---

## Monitoring & Maintenance

### Check Backend Health
```bash
# Real-time logs
gcloud run services logs read legalmind-backend --region=us-central1 --follow

# Service metrics
gcloud run services describe legalmind-backend --region=us-central1 --format=json | jq '.status'

# Check request metrics
gcloud monitoring metrics-descriptors list --filter="metric.type:run.googleapis.com"
```

### Keep Services Warm
- `--min-instances 1` keeps one instance always running (costs $~10/month)
- Prevents cold start errors
- Ensures API is always responsive

### Recommended Deployment Settings

For production reliability:
```bash
--memory 1Gi          # 1 GB RAM (prevents OOM crashes)
--cpu 1               # 1 vCPU (proper concurrency)
--timeout 60          # 60 second startup timeout
--min-instances 1     # Always keep 1 warm
--max-instances 10    # Scale up to 10 if needed
```

---

## What's Next?

1. ✅ Run the fix script to add Vertex AI permissions
2. ✅ Redeploy the backend
3. ✅ Monitor logs for any startup errors
4. ✅ Test the health endpoint
5. ✅ Verify the frontend can access the backend

If you encounter any issues during deployment:
- Check the troubleshooting guide: `docs/DEPLOYMENT_TROUBLESHOOTING.md`
- Review logs: `gcloud run services logs read legalmind-backend --limit=50`
- Verify IAM permissions: `gcloud projects get-iam-policy legalmind-486106`

---

## Technical Details

### Why This Happened

1. **Initialization Gap**: The service account was created with basic roles but Vertex AI wasn't included
2. **Silent Fallback**: When Vertex AI init failed, the code tried to fall back to the public API
3. **Scope Mismatch**: Service account tokens don't have scopes for the public Gemini API
4. **Result**: 403 "ACCESS_TOKEN_SCOPE_INSUFFICIENT" error

### How It's Fixed

1. **Explicit Roles**: Service account now has `roles/aiplatform.user`
2. **Clear Errors**: Code fails with helpful message instead of silent fallback
3. **Required Setup**: Setup scripts now include Vertex AI configuration
4. **Better Validation**: Settings properly handle Vertex AI credentials

### Architecture

```
Cloud Run Service (legalmind-backend)
    ↓
Service Account (legalmind-backend@legalmind-486106.iam.gserviceaccount.com)
    ↓ 
Application Default Credentials (ADC)
    ↓
Vertex AI API (with proper IAM role: aiplatform.user)
```

---

## Questions?

Refer to:
- GCP IAM Documentation: https://cloud.google.com/iam/docs
- Vertex AI Documentation: https://cloud.google.com/vertex-ai/docs
- Cloud Run Documentation: https://cloud.google.com/run/docs
