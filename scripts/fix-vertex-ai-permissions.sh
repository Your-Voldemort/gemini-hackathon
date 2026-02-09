#!/bin/bash

# Fix Vertex AI Permissions for LegalMind Backend
# This script adds the missing Vertex AI permissions to the service account
# Run this if you're getting 403 "ACCESS_TOKEN_SCOPE_INSUFFICIENT" errors

set -e

PROJECT_ID="${1:-legalmind-486106}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}===============================================${NC}"
echo -e "${CYAN}LegalMind Vertex AI Permissions Fix${NC}"
echo -e "${CYAN}===============================================${NC}"
echo ""

# Verify gcloud is available
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}[ERROR] gcloud CLI is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}[INFO] Project ID: $PROJECT_ID${NC}"

# Set project
gcloud config set project $PROJECT_ID --quiet

SERVICE_ACCOUNT="legalmind-backend@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${GREEN}[INFO] Service Account: $SERVICE_ACCOUNT${NC}"
echo ""

# Step 1: Enable required APIs
echo -e "${GREEN}[INFO] Enabling required Google Cloud APIs...${NC}"

apis=(
    "aiplatform.googleapis.com"
    "generativeai.googleapis.com"
)

for api in "${apis[@]}"; do
    echo -e "${YELLOW}  - Enabling $api...${NC}"
    gcloud services enable $api --quiet 2>/dev/null || true
done

echo -e "${GREEN}[OK] APIs enabled${NC}"
echo ""

# Step 2: Grant Vertex AI User role
echo -e "${GREEN}[INFO] Granting Vertex AI User role...${NC}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user" \
    --quiet

echo -e "${GREEN}[OK] Vertex AI User role granted${NC}"
echo ""

# Step 3: Verify roles
echo -e "${GREEN}[INFO] Verifying service account roles...${NC}"
echo ""

echo -e "${CYAN}Service Account Roles:${NC}"
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT" \
    --format="table(bindings.role)" | tail -n +2 | while read role; do
    echo -e "${GREEN}  ✓ $role${NC}"
done

echo ""
echo -e "${CYAN}===============================================${NC}"
echo -e "${GREEN}[SUCCESS] Vertex AI permissions configured!${NC}"
echo -e "${CYAN}===============================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Restart your Cloud Run service:"
echo -e "     ${NC}gcloud run services update legalmind-backend --region us-central1"
echo ""
echo "  2. OR redeploy your backend:"
echo -e "     ${NC}docker build -t gcr.io/$PROJECT_ID/legalmind-backend:latest ."
echo -e "     ${NC}docker push gcr.io/$PROJECT_ID/legalmind-backend:latest"
echo ""
echo "  3. Check logs:"
echo -e "     ${NC}gcloud run services logs read legalmind-backend --region us-central1 --limit=50"
echo ""
