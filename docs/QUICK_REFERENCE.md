# LegalMind - Quick Reference Guide

## 🎯 Deployed URLs

| Component | URL | Status |
|-----------|-----|--------|
| **Live Application** | https://legalmind-frontend-677928716377.us-central1.run.app | ✅ LIVE |
| **API Backend** | https://legalmind-backend-677928716377.us-central1.run.app | ✅ LIVE |
| **API Docs** | https://legalmind-backend-677928716377.us-central1.run.app/docs | ✅ LIVE |
| **Health Check** | https://legalmind-backend-677928716377.us-central1.run.app/health | ✅ LIVE |

## 🚀 Quick Start for Users

1. **Open the application:**
   ```
   https://legalmind-frontend-677928716377.us-central1.run.app
   ```

2. **Upload a contract** (PDF, DOCX, or TXT)

3. **Get instant analysis:**
   - Clause extraction
   - Risk scoring
   - Compliance checks
   - Obligation mapping

4. **Export results** in multiple formats

## 👨‍💻 For Developers

### Test the API
```bash
# Health check
curl https://legalmind-backend-677928716377.us-central1.run.app/health

# API documentation
curl https://legalmind-backend-677928716377.us-central1.run.app/docs
```

### API Key Endpoints (requires auth for production)
- `POST /v1/analyze/contract` - Upload and analyze contract
- `GET /v1/documents/{id}` - Retrieve document
- `GET /v1/reports/{id}` - Get analysis report
- `WebSocket /ws/chat` - Real-time chat interface

## 📊 GCP Project Info

- **Project ID:** `legalmind-486106`
- **Region:** `us-central1`
- **Environment:** Production
- **Services:**
  - Cloud Run (Frontend + Backend)
  - Firestore Database
  - Cloud Storage
  - Vertex AI

## 🛠️ Common Commands

### Monitor Services
```bash
# List all services
gcloud run services list --project=legalmind-486106

# View frontend logs
gcloud run services logs read legalmind-frontend \
  --project=legalmind-486106 --limit=50

# View backend logs
gcloud run services logs read legalmind-backend \
  --project=legalmind-486106 --limit=50
```

### Get Service Details
```bash
# Frontend details
gcloud run services describe legalmind-frontend \
  --project=legalmind-486106 --region=us-central1

# Backend details
gcloud run services describe legalmind-backend \
  --project=legalmind-486106 --region=us-central1
```

### Update Environment Variables
```bash
# Update backend (if needed)
gcloud run deploy legalmind-backend \
  --update-env-vars KEY=VALUE \
  --project=legalmind-486106 --region=us-central1
```

### View Service Metrics
```bash
gcloud monitoring dashboards list --project=legalmind-486106
```

## 📈 Current Configuration

### Frontend (Cloud Run)
- **Image:** Latest Next.js build
- **Port:** 3000
- **Memory:** 512MB
- **CPU:** 1 vCPU
- **Max instances:** 20
- **Timeout:** 300s

### Backend (Cloud Run)
- **Image:** `gcr.io/legalmind-486106/legalmind-backend:latest`
- **Port:** 8080
- **Memory:** 512MB
- **CPU:** 1 vCPU
- **Max instances:** 20
- **Environment:**
  - `USE_VERTEX_AI=true`
  - `GOOGLE_CLOUD_PROJECT=legalmind-486106`
  - `DEBUG=false`

## 🔐 Security

- ✅ SSL/TLS enabled
- ✅ Cloud Run authentication enforced for internal services
- ✅ Service accounts with minimal permissions
- ✅ Firestore security rules configured
- ✅ Cloud Storage access controlled

## 📱 Features Available

### Contract Analysis
- ✅ Automatic clause extraction
- ✅ Risk assessment
- ✅ Obligation mapping
- ✅ Key term highlighting

### Compliance Checks
- ✅ GDPR compliance
- ✅ HIPAA requirements
- ✅ CCPA obligations
- ✅ SOX compliance

### Documentation
- ✅ Legal memos
- ✅ Compliance reports
- ✅ Executive summaries
- ✅ Multi-format export

### Intelligence
- ✅ AI-powered analysis
- ✅ Real-time reasoning logs
- ✅ Precedent research
- ✅ Custom analysis workflows

## ⚡ Performance Metrics

### Expected Performance
- **Frontend load:** < 3 seconds
- **API response:** < 2 seconds for small docs
- **Analysis startup:** 10-30 seconds (first request, cold start)
- **Document analysis:** 30-120 seconds (depending on size)

### Scaling Behavior
- Auto-scales from 0 to 20 instances
- First request may take 30-60 seconds (cold start)
- Subsequent requests: sub-second latency
- Scales down after 15 minutes of inactivity

## 🆘 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| **Slow first load** | Normal due to Cloud Run cold start. Wait 30-60s. |
| **API unreachable** | Check if service has scaled up. Try again. |
| **CORS errors** | Frontend-to-backend connection issue. Check logs. |
| **High latency** | May need more instances. Check metrics. |
| **Deployment failed** | Verify GCP permissions and quotas. |

## 📞 Contact & Support

For deployment issues:
1. Check Cloud Run logs
2. Verify GCP project permissions
3. Review firestore/storage quotas
4. Check Vertex AI API is enabled

## ✅ Deployment Checklist

- [x] Frontend deployed and accessible
- [x] Backend deployed and responding
- [x] Health check endpoint working
- [x] API documentation accessible
- [x] SSL/TLS enabled
- [x] Auto-scaling configured
- [x] Logging enabled
- [x] Firestore connected
- [x] Cloud Storage configured
- [x] Vertex AI integrated

---

**Deployment Status:** ✅ COMPLETE AND LIVE  
**Last Verified:** 2026-02-08  
**Next Check:** Continuous monitoring
