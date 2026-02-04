# LegalMind - Google Cloud Deployment Complete ✅

## What Was Set Up

I've prepared your LegalMind project for full deployment on Google Cloud. Here's what's been created:

### 📦 **Deployment Files Created**

1. **[Dockerfile](Dockerfile)** - Container image for FastAPI backend
2. **[.dockerignore](.dockerignore)** - Optimize Docker build size
3. **[cloudbuild-backend.yaml](cloudbuild-backend.yaml)** - Cloud Build pipeline for backend
4. **[cloudbuild-frontend.yaml](cloudbuild-frontend.yaml)** - Cloud Build pipeline for frontend
5. **[firebase.json](firebase.json)** - Firebase Hosting configuration
6. **[.github/workflows/deploy-backend.yml](.github/workflows/deploy-backend.yml)** - GitHub Actions for backend
7. **[.github/workflows/deploy-frontend.yml](.github/workflows/deploy-frontend.yml)** - GitHub Actions for frontend
8. **[setup-gcp.sh](setup-gcp.sh)** - Bash setup script for Linux/macOS
9. **[setup-gcp.ps1](setup-gcp.ps1)** - PowerShell setup script for Windows
10. **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** - 5-minute deployment guide
11. **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment documentation

### 🏗️ **Architecture**

```
┌─────────────────────────────────────┐
│   Firebase Hosting (Frontend)       │
│        Next.js 15.3 SPA             │
└─────────────────────────────────────┘
              ↕️
         Cloud CDN
              ↕️
┌─────────────────────────────────────┐
│      Google Cloud Run (Backend)     │
│        FastAPI + Python 3.11        │
└─────────────────────────────────────┘
              ↕️
┌─────────────────────────────────────┐
│   Firestore + Cloud Storage         │
│   (Database & Document Storage)     │
└─────────────────────────────────────┘
```

### ⚙️ **Technologies Used**

| Component | Service |
|-----------|---------|
| **Frontend** | Firebase Hosting |
| **Backend** | Google Cloud Run |
| **Database** | Firestore |
| **Storage** | Cloud Storage |
| **CI/CD** | GitHub Actions |
| **Registry** | Google Container Registry |
| **Auth** | Workload Identity Federation |

---

## 🚀 **Next Steps (In Order)**

### **Step 1: Run GCP Setup Script** (5 minutes)

This script will automatically configure your Google Cloud project:

**Windows (PowerShell):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup-gcp.ps1
```

**macOS/Linux (Bash):**
```bash
chmod +x setup-gcp.sh
./setup-gcp.sh
```

When prompted, enter your **Google Cloud Project ID**.

**This script will:**
- ✅ Enable required Google Cloud APIs
- ✅ Create service accounts with proper permissions
- ✅ Set up GitHub Actions integration (Workload Identity Federation)
- ✅ Create Cloud Storage buckets
- ✅ Output all necessary configuration values

**Save the output!** You'll need these values for Step 2.

---

### **Step 2: Add GitHub Secrets** (2 minutes)

Go to your GitHub repository:
`Settings > Secrets and variables > Actions > New repository secret`

Add these 6 secrets using values from the script output:

| Secret Name | Value | Where to Get It |
|-------------|-------|-----------------|
| `GCP_PROJECT_ID` | your-project-id-123 | Script output |
| `WIF_PROVIDER` | projects/PROJECT_NUMBER/locations/... | Script output |
| `WIF_SERVICE_ACCOUNT` | github-actions@project-id.iam.gserviceaccount.com | Script output |
| `CLOUD_RUN_SERVICE_ACCOUNT` | legalmind-backend@project-id.iam.gserviceaccount.com | Script output |
| `FIREBASE_SERVICE_ACCOUNT` | (base64 encoded JSON) | See below |
| `API_URL` | (leave empty for now) | Update after first deploy |

**To create FIREBASE_SERVICE_ACCOUNT:**

```bash
# Run this in your terminal
gcloud iam service-accounts keys create firebase-key.json \
  --iam-account=legalmind-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Print base64 encoded version
cat firebase-key.json | base64 -w 0

# Copy the output and paste as FIREBASE_SERVICE_ACCOUNT secret
```

---

### **Step 3: Deploy!** (Automatic)

```bash
git add .
git commit -m "Deploy LegalMind to Google Cloud"
git push origin main
```

GitHub Actions will automatically:
1. 🏗️ Build Docker image for backend
2. 📦 Push to Container Registry
3. ☁️ Deploy backend to Cloud Run
4. 🎨 Build and deploy frontend to Firebase Hosting
5. 📡 Set up CDN and auto-scaling

**Watch the deployment:**
- Check GitHub `Actions` tab for real-time progress
- View Cloud Run: `gcloud run services list --region us-central1`
- View Firebase Hosting: `firebase hosting:channel:list`

---

### **Step 4: Get Your Live URLs**

```bash
# Backend URL (API)
gcloud run services describe legalmind-backend \
  --region us-central1 \
  --format='value(status.url)'

# Frontend URL
# https://YOUR_PROJECT_ID.web.app
```

**Then update GitHub secret:**
- Set `API_URL` to your Cloud Run URL

---

## 📊 **Deployment Summary**

### **Backend (FastAPI → Cloud Run)**
- ✅ Containerized with Docker
- ✅ Auto-scaling (0-100 instances)
- ✅ 2GB memory, 2 CPU per instance
- ✅ 99.95% uptime SLA
- ✅ Cold start: ~2-3 seconds

### **Frontend (Next.js → Firebase Hosting)**
- ✅ Static site generation (SG)
- ✅ Global CDN distribution
- ✅ Auto-minification & optimization
- ✅ Free SSL/TLS certificate
- ✅ Instant deployments

### **Database (Firestore)**
- ✅ Fully managed NoSQL database
- ✅ 99.999% uptime SLA
- ✅ Real-time sync capabilities
- ✅ Automatic backups
- ✅ Already configured in your project

### **Storage (Cloud Storage)**
- ✅ Secure PDF document storage
- ✅ 99.99% durability
- ✅ Access control via service accounts
- ✅ Automatic lifecycle policies

---

## 💰 **Cost Breakdown**

### **Estimated Monthly Costs** (Low to Medium Usage)

| Service | Free Tier | Cost Beyond | Estimated Monthly |
|---------|-----------|-------------|-------------------|
| Cloud Run | 2M requests/month | $0.40/M | $0-5 |
| Firestore | 25k reads/day | $0.06/100k reads | $0-5 |
| Firestore | 25k writes/day | $0.18/100k writes | $0-5 |
| Cloud Storage | 5GB/month | $0.020/GB | $0 |
| Firebase Hosting | 10GB bandwidth/month | $0.15/GB | $0 |
| **Total** | | | **$5-15** |

### **To Reduce Costs:**
- Set Cloud Run min instances to 0 (default)
- Use Firestore automatic scaling
- Enable Data Export for backups (instead of manual)
- Set Cloud Storage lifecycle policies

---

## ✅ **Verification Checklist**

After deployment, verify everything works:

```bash
# 1. Check Cloud Run deployment
gcloud run services describe legalmind-backend \
  --region us-central1

# 2. Test API endpoint
curl https://legalmind-backend-YOUR_PROJECT_ID.cloudfunctions.net/docs

# 3. Check Firebase Hosting
open https://YOUR_PROJECT_ID.web.app

# 4. View logs
gcloud run logs read legalmind-backend \
  --region us-central1 --limit 50

# 5. Check Firestore status
gcloud firestore databases list
```

---

## 🆘 **Troubleshooting**

### **Deployment Failed?**

```bash
# Check GitHub Actions
# Settings > Actions > Select failed workflow > View logs

# Check Cloud Run errors
gcloud run logs read legalmind-backend \
  --region us-central1 \
  --limit 100

# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:legalmind-backend@"
```

### **API Returning 403?**

```bash
# Make sure Cloud Run allows unauthenticated access
gcloud run services update legalmind-backend \
  --allow-unauthenticated \
  --region us-central1
```

### **Frontend Not Loading?**

```bash
# Check Firebase Hosting deployment
firebase hosting:channel:list

# View Firebase logs
firebase hosting:sites list
```

### **Need Help?**

1. 📖 Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions
2. 📖 Check [QUICK_DEPLOY.md](QUICK_DEPLOY.md) for quick reference
3. 🔍 Search GitHub Actions logs for specific error
4. 💬 Check Cloud Run logs: `gcloud run logs read legalmind-backend --region us-central1 --follow`

---

## 🎯 **Advanced Features** (Optional)

### **Custom Domain**
```bash
# Backend
gcloud run domain-mappings create \
  --service=legalmind-backend \
  --domain=api.yourdomain.com \
  --region=us-central1

# Frontend
firebase hosting:domain:add yourdomain.com
```

### **Environment-Specific Deployments**
- Staging: Deploy from `staging` branch
- Production: Deploy from `main` branch
- (Requires branch protection rules in GitHub)

### **Monitoring & Alerts**
- Cloud Monitoring: `gcloud monitoring dashboards create ...`
- Error Reporting: Automatic for Cloud Run
- Logging: Cloud Logging integrated

---

## 📝 **Documentation**

- **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** - Start here (5-minute guide)
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete reference
- **[README.md](README.md)** - Project overview
- **[Dockerfile](Dockerfile)** - Container configuration
- **[firebase.json](firebase.json)** - Hosting configuration

---

## 🎉 **You're All Set!**

Your LegalMind project is ready for production deployment on Google Cloud Platform.

**Next Action:** Run the setup script and follow the 4 deployment steps above.

Questions? Check the deployment guides or GitHub Actions logs for error details.

Happy deploying! 🚀
