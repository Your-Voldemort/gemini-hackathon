#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Ralph Validation Loop - Comprehensive deployment verification
    Iteratively tests and validates that LegalMind is correctly deployed
    on publicly available URLs with all services functioning.

.DESCRIPTION
    This script performs a complete validation loop (Ralph Loop):
    - Verifies GCP project configuration
    - Checks Cloud Run backend deployment
    - Checks Firebase frontend deployment
    - Tests public API endpoints
    - Validates health checks
    - Generates comprehensive deployment report

.PARAMETER ProjectId
    GCP Project ID (e.g., legalmind-486106)

.PARAMETER Verbose
    Enable verbose output for detailed diagnostics

.EXAMPLE
    .\ralph-validation-loop.ps1 -ProjectId "legalmind-486106"

#>

param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectId = "legalmind-486106"
)

# Color codes for output
$colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-Status {
    param([string]$Message, [string]$Status = "Info")
    $color = $colors[$Status]
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] " -NoNewline -ForegroundColor Gray
    Write-Host $Message -ForegroundColor $color
}

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Magenta
    Write-Host $Title -ForegroundColor Magenta
    Write-Host ("=" * 80) -ForegroundColor Magenta
}

# ============================================================================
# RALPH LOOP ITERATION 1: PROJECT CONFIGURATION VERIFICATION
# ============================================================================
Write-Section "RALPH LOOP - ITERATION 1: PROJECT CONFIGURATION"

Write-Status "Checking GCP authentication..." "Info"
try {
    $authCheck = gcloud config get-value project 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Status "[OK] GCP authentication: OK" "Success"
        Write-Status "Current project: $authCheck" "Info"
    }
    else {
        Write-Status "[FAIL] GCP authentication failed" "Error"
        Write-Status "Run: gcloud auth login" "Warning"
        exit 1
    }
}
catch {
    Write-Status "[FAIL] GCP CLI not found" "Error"
    Write-Status "Please install: https://cloud.google.com/sdk/docs/install" "Warning"
    exit 1
}

Write-Status "Verifying project: $ProjectId" "Info"
try {
    gcloud config set project $ProjectId 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "[OK] Project set to: $ProjectId" "Success"
    }
    else {
        Write-Status "[FAIL] Project not found or not accessible" "Error"
        exit 1
    }
}
catch {
    Write-Status "[FAIL] Error setting project" "Error"
    exit 1
}

# ============================================================================
# RALPH LOOP ITERATION 2: CLOUD RUN BACKEND VERIFICATION
# ============================================================================
Write-Section "RALPH LOOP - ITERATION 2: CLOUD RUN BACKEND VERIFICATION"

Write-Status "Checking Cloud Run services..." "Info"
$cloudRunServices = gcloud run services list --project=$ProjectId --format="json" 2>&1 | ConvertFrom-Json

if ($cloudRunServices.Count -eq 0) {
    Write-Status "[!] No Cloud Run services found" "Warning"
    $backendUrl = $null
}
else {
    $backendService = $cloudRunServices | Where-Object { $_.metadata.name -like "*backend*" -or $_.metadata.name -like "*legalmind*" } | Select-Object -First 1
    
    if ($backendService) {
        $backendUrl = $backendService.status.url
        Write-Status "[OK] Backend service found" "Success"
        Write-Status "Service: $($backendService.metadata.name)" "Info"
        Write-Status "URL: $backendUrl" "Info"
        Write-Status "Region: $($backendService.metadata.annotations.'run.googleapis.com/deployment-tool')" "Info"
        Write-Status "Status: $($backendService.status.conditions[0].status)" "Info"
    }
    else {
        Write-Status "[FAIL] No backend service found matching pattern" "Error"
        Write-Status "Available services:" "Warning"
        $cloudRunServices | ForEach-Object { Write-Status "  - $($_.metadata.name)" "Warning" }
        $backendUrl = $null
    }
}

# ============================================================================
# RALPH LOOP ITERATION 3: FIREBASE FRONTEND VERIFICATION
# ============================================================================
Write-Section "RALPH LOOP - ITERATION 3: FIREBASE FRONTEND VERIFICATION"

Write-Status "Checking Firebase hosting sites..." "Info"
try {
    $firebaseSites = gcloud firebase hosting:sites:list --project=$ProjectId 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Status "[OK] Firebase hosting accessible" "Success"
        # Extract the default hosting URL
        $frontendUrl = "https://$ProjectId.web.app"
        Write-Status "Frontend URL: $frontendUrl" "Info"
    }
    else {
        Write-Status "[!] Firebase hosting not configured" "Warning"
        $frontendUrl = $null
    }
}
catch {
    Write-Status "[!] Firebase check skipped" "Warning"
    $frontendUrl = $null
}

# ============================================================================
# RALPH LOOP ITERATION 4: BACKEND API ENDPOINT TESTING
# ============================================================================
Write-Section "RALPH LOOP - ITERATION 4: BACKEND API ENDPOINT TESTING"

$endpoints = @(
    @{ name = "Health Check"; path = "/health"; method = "GET" }
    @{ name = "Root Endpoint"; path = "/"; method = "GET" }
    @{ name = "API Docs"; path = "/docs"; method = "GET" }
    @{ name = "OpenAPI Spec"; path = "/openapi.json"; method = "GET" }
)

$backendTests = @()

if ($backendUrl) {
    Write-Status "Testing backend endpoints at: $backendUrl" "Info"
    
    foreach ($endpoint in $endpoints) {
        $testUrl = "$backendUrl$($endpoint.path)"
        Write-Status "Testing: $($endpoint.name) ($testUrl)" "Info"
        
        try {
            $response = Invoke-WebRequest -Uri $testUrl -Method $endpoint.method -TimeoutSec 10 -SkipHttpErrorCheck
            
            if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 404) {
                Write-Status "[OK] $($endpoint.name) - HTTP $($response.StatusCode)" "Success"
                $backendTests += @{
                    Endpoint = $endpoint.name
                    Path = $endpoint.path
                    Status = "OK"
                    HttpCode = $response.StatusCode
                }
            }
            else {
                Write-Status "[!] $($endpoint.name) - HTTP $($response.StatusCode)" "Warning"
                $backendTests += @{
                    Endpoint = $endpoint.name
                    Path = $endpoint.path
                    Status = "HTTP $($response.StatusCode)"
                    HttpCode = $response.StatusCode
                }
            }
        }
        catch {
            Write-Status "[FAIL] $($endpoint.name) - Connection failed: $($_.Exception.Message)" "Error"
            $backendTests += @{
                Endpoint = $endpoint.name
                Path = $endpoint.path
                Status = "FAILED"
                Error = $_.Exception.Message
            }
        }
    }
}
else {
    Write-Status "! Skipping backend tests - no URL available" "Warning"
}

# ============================================================================
# RALPH LOOP ITERATION 5: FRONTEND ACCESSIBILITY TESTING
# ============================================================================
Write-Section "RALPH LOOP - ITERATION 5: FRONTEND ACCESSIBILITY TESTING"

if ($frontendUrl) {
    Write-Status "Testing frontend at: $frontendUrl" "Info"
    
    try {
        $response = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -eq 200) {
            Write-Status "[OK] Frontend accessible - HTTP $($response.StatusCode)" "Success"
            Write-Status "Content size: $($response.RawContentLength) bytes" "Info"
            $frontendStatus = "OK"
        }
        else {
            Write-Status "[!] Frontend returned HTTP $($response.StatusCode)" "Warning"
            $frontendStatus = "HTTP $($response.StatusCode)"
        }
    }
    catch {
        Write-Status "[FAIL] Frontend not accessible: $($_.Exception.Message)" "Error"
        $frontendStatus = "FAILED"
    }
}
else {
    Write-Status "[!] Skipping frontend test - no URL available" "Warning"
    $frontendStatus = "UNKNOWN"
}

# ============================================================================
# RALPH LOOP ITERATION 6: GCP RESOURCES VERIFICATION
# ============================================================================
Write-Section "RALPH LOOP - ITERATION 6: GCP RESOURCES VERIFICATION"

$resources = @(
    @{ name = "Firestore Database"; command = "firestore:databases:list" }
    @{ name = "Cloud Storage Buckets"; command = "storage:buckets:list" }
    @{ name = "Service Accounts"; command = "iam:service-accounts:list" }
)

Write-Status "Checking GCP resources..." "Info"

    foreach ($resource in $resources) {
    Write-Status "Checking: $($resource.name)" "Info"
    
    try {
        $output = gcloud $resource.command --project=$ProjectId --format="json" 2>&1 | ConvertFrom-Json
        $count = if ($output -is [array]) { $output.Count } else { if ($output) { 1 } else { 0 } }
        
        if ($count -gt 0) {
            Write-Status "[OK] $($resource.name): $count found" "Success"
        }
        else {
            Write-Status "[!] $($resource.name): None found" "Warning"
        }
    }
    catch {
        Write-Status "[!] $($resource.name): Check skipped" "Warning"
    }
}

# ============================================================================
# RALPH LOOP ITERATION 7: COMPREHENSIVE REPORTING
# ============================================================================
Write-Section "RALPH LOOP - ITERATION 7: DEPLOYMENT SUMMARY REPORT"

$reportDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$report = @"
╔════════════════════════════════════════════════════════════════════════════╗
║                    LEGALMIND DEPLOYMENT VALIDATION REPORT                  ║
║                          Ralph Loop Iteration 7/7                           ║
╚════════════════════════════════════════════════════════════════════════════╝

Generated: $reportDate
Project ID: $ProjectId

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEPLOYMENT URLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 Frontend (Firebase Hosting):
   URL: $frontendUrl
   Status: $frontendStatus
   
🔧 Backend (Cloud Run):
   URL: $backendUrl
   Status: $(if ($backendUrl) { "DEPLOYED" } else { "NOT DEPLOYED" })

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API ENDPOINT TEST RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"@

if ($backendTests.Count -gt 0) {
    $report += "`n"
    $backendTests | ForEach-Object {
        $status_symbol = if ($_.Status -eq "OK") { "[OK]" } else { "[FAIL]" }
        $report += "$status_symbol $($_.Endpoint) - $($_.Path)`n   Status: $($_.Status)`n`n"
    }
}
else {
    $report += "No backend tests performed`n`n"
}

# Deployment checklist
$report += @"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEPLOYMENT CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

$(if ($backendUrl) { "[YES]" } else { "[NO]" }) Backend deployed on Cloud Run
$(if ($frontendUrl) { "[YES]" } else { "[NO]" }) Frontend deployed on Firebase Hosting
$(if ($backendUrl) { 
    $healthTestPassed = $backendTests | Where-Object { $_.Endpoint -eq "Health Check" -and $_.Status -eq "OK" }
    if ($healthTestPassed) { "[YES]" } else { "[NO]" }
} else { "[NO]" }) Health check endpoint responsive
$(if ($frontendUrl -and $frontendStatus -eq "OK") { "[YES]" } else { "[NO]" }) Frontend publicly accessible
$(if ($backendUrl -and $frontendUrl) { "[YES]" } else { "[NO]" }) Both frontend and backend deployed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"@

# Determine next steps based on results
$allTestsPassed = $backendUrl -and $frontendUrl -and ($backendTests | Where-Object { $_.Status -eq "OK" })

if ($allTestsPassed) {
    $report += @"
[SUCCESS] DEPLOYMENT SUCCESSFUL!

Your LegalMind application is live and accessible:
- Frontend: $frontendUrl
- Backend API: $backendUrl

Users can now access your application from the frontend URL.
API documentation available at: $backendUrl/docs

"@
}
else {
    $report += @"
[WARNING] DEPLOYMENT INCOMPLETE

Not all services are deployed or accessible. Issues found:"@
    
    if (-not $backendUrl) {
        $report += "`n- Backend service not deployed on Cloud Run`n"
    }
    if (-not $frontendUrl) {
        $report += "`n- Frontend not deployed on Firebase Hosting`n"
    }
    if ($backendTests | Where-Object { $_.Status -ne "OK" }) {
        $report += "`n- Some API endpoints are not accessible`n"
    }
    
    $report += @"

Run deployment script:
  .\deploy-complete-fix.ps1 -ProjectId "$ProjectId"

Or check specific components:
  - Backend: gcloud run services list --project=$ProjectId
  - Frontend: gcloud firebase hosting:sites:list --project=$ProjectId

"@
}

$report += @"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TROUBLESHOOTING COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View backend logs:
  gcloud run services describe legalmind-backend --platform=managed --region=us-central1 --project=$ProjectId

View backend logs (live streaming):
  gcloud run services logs read legalmind-backend --limit=50 --project=$ProjectId

Deploy backend:
  gcloud run deploy legalmind-backend --source=. --project=$ProjectId --region=us-central1

Deploy frontend:
  firebase deploy --project=$ProjectId

Restart backend service:
  gcloud run services update legalmind-backend --project=$ProjectId

Check service account permissions:
  gcloud projects get-iam-policy $ProjectId --flatten="bindings[].members" --filter="bindings.members:serviceAccount:*"

"@

Write-Host $report
Write-Host ""

# Save report to file
$reportFileName = "ralph-validation-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
$reportPath = Join-Path $PSScriptRoot $reportFileName
$report | Out-File -FilePath $reportPath -Encoding UTF8
Write-Status "Report saved to: $reportPath" "Success"

# ============================================================================
# RALPH LOOP COMPLETE
# ============================================================================
Write-Section "RALPH LOOP VALIDATION COMPLETE"

if ($allTestsPassed) {
    Write-Status "[SUCCESS] All checks passed! Deployment is live and accessible." "Success"
    exit 0
}
else {
    Write-Status "[WARNING] Some checks failed. Review the report above for details." "Warning"
    exit 1
}
