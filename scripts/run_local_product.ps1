$ErrorActionPreference = "Stop"

# 1. Resolve repository root safely
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

# 2. Verify Docker is available
$OldErr = $ErrorActionPreference
$ErrorActionPreference = "Continue"
docker info 2>&1 | Out-Null
$ErrorActionPreference = $OldErr
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker is not running or not available in PATH. Please start Docker and try again."
    exit 1
}

# 3. Verify external Fan artifact root
$ArtifactRoot = $env:AMHI_EXTERNAL_ARTIFACT_ROOT
if ([string]::IsNullOrWhiteSpace($ArtifactRoot)) {
    $ArtifactRoot = "D:\PDM_Data\MIMII"
}
if (-not (Test-Path -Path $ArtifactRoot)) {
    Write-Error "External artifact root not found at '$ArtifactRoot'. Override using `$env:AMHI_EXTERNAL_ARTIFACT_ROOT."
    exit 1
}

# 4. Verify GEMINI_API_KEY
if ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
    Write-Error "GEMINI_API_KEY missing. Please configure your API key."
    exit 1
} else {
    Write-Host "GEMINI_API_KEY configured."
}

# 5. Use local technician username
$Username = $env:AMHI_LOCAL_USERNAME
if ([string]::IsNullOrWhiteSpace($Username)) {
    $Username = "amhi-admin"
}

# 6. Prompt for local demo password without echoing it, generate bcrypt hash
$PlainPassword = Read-Host "Enter local demo password for $Username" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($PlainPassword)
$Plaintext = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)

# Generate bcrypt hash (safely calling python)
$PasswordHash = $Plaintext | python -c "import bcrypt, sys; print(bcrypt.hashpw(sys.stdin.read().strip().encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate password hash. Please ensure the 'bcrypt' Python package is installed."
    exit 1
}

# 7. Generate random AMHI_SESSION_SECRET
$SessionSecret = python -c "import secrets; print(secrets.token_urlsafe(32))"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate session secret."
    exit 1
}

# 8. Set environment for Docker Compose
$env:AMHI_ADMIN_USERNAME = $Username
$env:AMHI_ADMIN_PASSWORD_HASH = $PasswordHash
$env:AMHI_SESSION_SECRET = $SessionSecret
$env:PDM_DATA_ROOT = "/data/artifacts"
$env:AMHI_EXTERNAL_ARTIFACT_ROOT = $ArtifactRoot

# Clear sensitive variable from PowerShell memory
$Plaintext = $null

Write-Host "Starting AMHI Fan Local Product..."
# 9 & 10. Start the complete runtime automatically
docker compose -f docker-compose.prod.yml -f docker-compose.local.yml up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start Docker Compose services."
    exit 1
}

# 11. Wait for startup
Write-Host "Waiting for services to become ready..."
$MaxAttempts = 30
$Attempt = 0
$IsReady = $false
$WorkerFailed = $false

while ($Attempt -lt $MaxAttempts) {
    $Attempt++
    Start-Sleep -Seconds 2
    
    # Check if worker is running
    $RunningServices = docker compose -f docker-compose.prod.yml -f docker-compose.local.yml ps --services --filter "status=running" 2>&1
    if ($LASTEXITCODE -eq 0 -and $RunningServices -notcontains "worker") {
        $WorkerFailed = $true
        break
    }
    
    try {
        $Response = Invoke-WebRequest -Uri "http://127.0.0.1:8001/api/v1/ready" -Method Get -ErrorAction Stop
        if ($Response.StatusCode -eq 200) {
            $IsReady = $true
            break
        }
    } catch {
        # Ignore errors during startup
    }
    Write-Host -NoNewline "."
}
Write-Host ""

if ($WorkerFailed) {
    Write-Error "The AMHI worker container failed to start or exited unexpectedly."
    Write-Host "Diagnostic command to inspect worker logs:"
    Write-Host "docker compose -f docker-compose.prod.yml -f docker-compose.local.yml logs worker"
    exit 1
}

if (-not $IsReady) {
    Write-Error "Services failed to become ready within the timeout period. Check docker logs."
    exit 1
}

# 12. Print compact final result
Write-Host "========================================"
Write-Host "AMHI FAN LOCAL PRODUCT READY"
Write-Host "========================================"
Write-Host ""
Write-Host "URL:"
Write-Host "http://127.0.0.1:8001/dashboard"
Write-Host ""
Write-Host "USERNAME:"
Write-Host $Username
Write-Host ""
Write-Host "PIPELINE:"
Write-Host "REAL"
Write-Host ""
Write-Host "WORKER:"
Write-Host "RUNNING"
Write-Host ""
Write-Host "ARTIFACTS:"
Write-Host "READY"
Write-Host ""
Write-Host "GEMINI:"
Write-Host "CONFIGURED"
Write-Host ""
Write-Host "To stop:"
Write-Host ".\scripts\stop_local_product.ps1"
Write-Host "========================================"

# 13. Optionally open the browser automatically
Start-Process "http://127.0.0.1:8001/dashboard"
