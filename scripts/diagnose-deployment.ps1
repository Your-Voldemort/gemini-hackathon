#!/usr/bin/env pwsh
# LegalMind Deployment Diagnostic Script
# This script verifies all aspects of the deployment and identifies any remaining issues

param(
    [string]$ProjectId = "legalmind-486106",
    [string]$ServiceName = "legalmind-backend",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Continue"

# Colors
$colors = @{
    "error"    = "Red"
    "success"  = "Green"
    "warning"  = "Yellow"
    "info"     = "White"
    "step"     = "Cyan"
}

function Print-Step {
    param([string]$msg)
    Write-Host ""
    Write-Host "█ $msg" -ForegroundColor Cyan -BackgroundColor Black
    Write-Host "─" * 80 -ForegroundColor Gray
}

function Check {
    param([string]$name, [scriptblock]$test)
    try {
        $result = & $test
        Write-Host "  ✓ $name" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ✗ $name" -ForegroundColor Red
        Write-Host "    Error: $_" -ForegroundColor Gray
        return $false
    }
}

Print-Step "LEGALMIND DEPLOYMENT DIAGNOSTIC"

$SA_EMAIL = "${ServiceName}@${ProjectId}.iam.gserviceaccount.com"
$all_checks_passed = $true

# ============================================================================
# CHECK 1: GCP PROJECT ACCESS
# ============================================================================

Print-Step "CHECK 1: GCP PROJECT ACCESS"

Check "Project exists and is accessible" {
    gcloud projects describe $ProjectId --format="value(projectId)" | Out-Null
}

Check "Current project is set correctly" {
    $current = gcloud config get-value project 2>$null
    if ($current -ne $ProjectId) {
        throw "Current project is $current, expected $ProjectId"
    }
}

# ============================================================================
# CHECK 2: SERVICE ACCOUNT
# ============================================================================

Print-Step "CHECK 2: SERVICE ACCOUNT"

Check "Service account exists: $SA_EMAIL" {
    gcloud iam service-accounts describe $SA_EMAIL --format="value(email)" | Out-Null
}

# ============================================================================
# CHECK 3: APIS ENABLED
# ============================================================================

Print-Step "CHECK 3: REQUIRED APIS"

$critical_apis = @(
    "aiplatform.googleapis.com",
    "generativeai.googleapis.com",
    "run.googleapis.com",
    "firestore.googleapis.com"
)

foreach ($api in $critical_apis) {
    Check "API enabled: $api" {
        $enabled = gcloud services list --enabled --filter="name:$api" --format="value(name)"
        if (-not $enabled) {
            throw "API not enabled"
        }
    }
}

# ============================================================================
# CHECK 4: IAM ROLES
# ============================================================================

Print-Step "CHECK 4: IAM ROLES"

$required_roles = @(
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter"
)

$assigned_roles = gcloud projects get-iam-policy $ProjectId `
    --flatten="bindings[].members" `
    --filter="bindings.members:serviceAccount:$SA_EMAIL" `
    --format="value(bindings.role)" 2>$null

foreach ($role in $required_roles) {
    $has_role = $assigned_roles | Where-Object { $_ -eq $role }
    if ($has_role) {
        Write-Host "  ✓ $role" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $role (MISSING)" -ForegroundColor Red
        $all_checks_passed = $false
    }
}

# ============================================================================
# CHECK 5: CLOUD RUN SERVICE
# ============================================================================

Print-Step "CHECK 5: CLOUD RUN SERVICE"

Check "Cloud Run service exists" {
    gcloud run services describe $ServiceName --region=$Region --format="value(metadata.name)" | Out-Null
}

if ($?) {
    Check "Service is in ACTIVE state" {
        $status = gcloud run services describe $ServiceName --region=$Region --format="value(status.conditions[0].status)"
        if ($status -ne "True") {
            throw "Service status is $status"
        }
    }
    
    Check "Service is configured with correct service account" {
        $sa = gcloud run services describe $ServiceName --region=$Region --format="value(spec.template.spec.serviceAccountName)"
        if ($sa -ne $SA_EMAIL) {
            throw "Service account is $sa, expected $SA_EMAIL"
        }
    }
    
    Check "Service has environment variables set" {
        $env_vars = gcloud run services describe $ServiceName --region=$Region --format="value(spec.template.spec.containers[0].env)"
        if (-not $env_vars -or $env_vars.Count -eq 0) {
            throw "No environment variables found"
        }
    }
}

# ============================================================================
# CHECK 6: DOCKERFILE CONFIGURATION
# ============================================================================

Print-Step "CHECK 6: DOCKERFILE CONFIGURATION"

Check "Dockerfile exists" {
    Test-Path "Dockerfile" | Out-Null
}

if ((Test-Path "Dockerfile")) {
    Check "Dockerfile uses Python 3.11-slim base image" {
        $content = Get-Content Dockerfile -Raw
        if ($content -notmatch "python:3\.11-slim") {
            throw "Dockerfile does not use python:3.11-slim base image"
        }
    }
    
    Check "Dockerfile exposes port 8000" {
        $content = Get-Content Dockerfile -Raw
        if ($content -notmatch "EXPOSE 8000") {
            throw "Dockerfile does not expose port 8000"
        }
    }
    
    Check "Dockerfile sets PYTHONUNBUFFERED" {
        $content = Get-Content Dockerfile -Raw
        if ($content -notmatch "PYTHONUNBUFFERED=1") {
            throw "PYTHONUNBUFFERED not set in Dockerfile"
        }
    }
}

# ============================================================================
# CHECK 7: REQUIREMENTS.TXT
# ============================================================================

Print-Step "CHECK 7: PYTHON DEPENDENCIES"

Check "requirements.txt exists" {
    Test-Path "backend/requirements.txt" | Out-Null
}

if ((Test-Path "backend/requirements.txt")) {
    Check "google-cloud-aiplatform is in requirements" {
        $content = Get-Content backend/requirements.txt -Raw
        if ($content -notmatch "google-cloud-aiplatform") {
            throw "google-cloud-aiplatform not found in requirements.txt"
        }
    }
    
    Check "google-generativeai is in requirements" {
        $content = Get-Content backend/requirements.txt -Raw
        if ($content -notmatch "google-generativeai") {
            throw "google-generativeai not found in requirements.txt"
        }
    }
    
    Check "FastAPI is in requirements" {
        $content = Get-Content backend/requirements.txt -Raw
        if ($content -notmatch "fastapi") {
            throw "fastapi not found in requirements.txt"
        }
    }
}

# ============================================================================
# CHECK 8: SOURCE CODE CONFIGURATION
# ============================================================================

Print-Step "CHECK 8: SOURCE CODE CONFIGURATION"

Check "settings.py handles Vertex AI correctly" {
    $content = Get-Content backend/config/settings.py -Raw
    if ($content -notmatch "use_vertex_ai") {
        throw "use_vertex_ai not found in settings.py"
    }
}

Check "gemini_service.py uses Vertex AI SDK correctly" {
    $content = Get-Content backend/services/gemini_service.py -Raw
    if ($content -notmatch "vertexai.init") {
        throw "vertexai.init not found in gemini_service.py"
    }
    if ($content -notmatch "GenerativeModel") {
        throw "GenerativeModel not found in gemini_service.py"
    }
}

Check "app_new.py has proper lifespan management" {
    $content = Get-Content backend/api/app_new.py -Raw
    if ($content -notmatch "@asynccontextmanager") {
        throw "Lifespan context manager not found in app_new.py"
    }
}

# ============================================================================
# CHECK 9: CLOUD RUN LOGS
# ============================================================================

Print-Step "CHECK 9: RECENT CLOUD RUN LOGS"

Write-Host ""
Write-Host "Recent logs (last 10 lines):" -ForegroundColor Cyan
try {
    gcloud run services logs read $ServiceName `
        --region $Region `
        --limit 10 `
        --format "table(timestamp,text)" 2>$null | Write-Host -ForegroundColor Gray
} catch {
    Write-Host "  Could not retrieve logs" -ForegroundColor Yellow
}

# ============================================================================
# CHECK 10: SERVICE URL AND CONNECTIVITY
# ============================================================================

Print-Step "CHECK 10: SERVICE CONNECTIVITY"

try {
    $service_url = gcloud run services describe $ServiceName `
        --region=$Region `
        --format="value(status.url)" 2>$null
    
    if ($service_url) {
        Write-Host "Service URL: $service_url" -ForegroundColor Green
        
        Write-Host "Testing connectivity to health endpoint..." -ForegroundColor Cyan
        try {
            $response = Invoke-WebRequest -Uri "$service_url/api/health" -UseBasicParsing
            Write-Host "  ✓ Health endpoint is responding" -ForegroundColor Green
            Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Gray
        } catch {
            Write-Host "  ⚠ Health endpoint not responding (service might be warming up)" -ForegroundColor Yellow
            Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "Could not retrieve service URL" -ForegroundColor Yellow
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

Print-Step "DIAGNOSTIC SUMMARY"

Write-Host ""
if ($all_checks_passed) {
    Write-Host "✅ All critical checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your LegalMind backend deployment is properly configured." -ForegroundColor Green
    Write-Host ""
    Write-Host "If you're still experiencing issues:" -ForegroundColor Yellow
    Write-Host "  1. Check real-time logs: gcloud run services logs read $ServiceName --region=$Region --follow" -ForegroundColor Gray
    Write-Host "  2. Wait 5-10 minutes for the service to fully initialize" -ForegroundColor Gray
    Write-Host "  3. Try the health endpoint in a browser: $service_url/api/health" -ForegroundColor Gray
} else {
    Write-Host "⚠️ Some checks did not pass. Review the errors above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To fix issues:" -ForegroundColor Yellow
    Write-Host "  1. Run: .\deploy-complete-fix.ps1 -ProjectId '$ProjectId'" -ForegroundColor Gray
    Write-Host "  2. Wait 5-10 minutes for deployment to complete" -ForegroundColor Gray
    Write-Host "  3. Run this diagnostic script again" -ForegroundColor Gray
}

Write-Host ""
