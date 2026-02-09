# Fix Vertex AI Permissions for LegalMind Backend
# This script adds the missing Vertex AI permissions to the service account
# Run this if you're getting 403 "ACCESS_TOKEN_SCOPE_INSUFFICIENT" errors

param(
    [string]$ProjectId = "legalmind-486106"
)

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "LegalMind Vertex AI Permissions Fix" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Verify gcloud is available
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] gcloud CLI is not installed" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Project ID: $ProjectId" -ForegroundColor Green

# Set project
gcloud config set project $ProjectId --quiet

$SERVICE_ACCOUNT = "legalmind-backend@${ProjectId}.iam.gserviceaccount.com"

Write-Host "[INFO] Service Account: $SERVICE_ACCOUNT" -ForegroundColor Green
Write-Host ""

# Step 1: Enable required APIs
Write-Host "[INFO] Enabling required Google Cloud APIs..." -ForegroundColor Green
$apis = @(
    "aiplatform.googleapis.com",
    "generativeai.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "  - Enabling $api..." -ForegroundColor Yellow
    gcloud services enable $api --quiet 2>$null
}

Write-Host "[OK] APIs enabled" -ForegroundColor Green
Write-Host ""

# Step 2: Grant Vertex AI User role
Write-Host "[INFO] Granting Vertex AI User role..." -ForegroundColor Green
gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/aiplatform.user" `
    --quiet

Write-Host "[OK] Vertex AI User role granted" -ForegroundColor Green
Write-Host ""

# Step 3: Verify roles
Write-Host "[INFO] Verifying service account roles..." -ForegroundColor Green
Write-Host ""

$roles = gcloud projects get-iam-policy $ProjectId `
    --flatten="bindings[].members" `
    --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT" `
    --format="table(bindings.role)" | Select-Object -Skip 1

Write-Host "Service Account Roles:" -ForegroundColor Cyan
$roles | ForEach-Object { 
    Write-Host "  ✓ $_" -ForegroundColor Green
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Vertex AI permissions configured!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Restart your Cloud Run service:"
Write-Host "     gcloud run services update legalmind-backend --region us-central1" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. OR redeploy your backend:"
Write-Host "     docker build -t gcr.io/$ProjectId/legalmind-backend:latest ." -ForegroundColor Gray
Write-Host "     docker push gcr.io/$ProjectId/legalmind-backend:latest" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Check logs:"
Write-Host "     gcloud run services logs read legalmind-backend --region us-central1 --limit=50" -ForegroundColor Gray
Write-Host ""
