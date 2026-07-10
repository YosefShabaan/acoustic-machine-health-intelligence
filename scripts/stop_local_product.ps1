param(
    [switch]$ClearData
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

if ($ClearData) {
    Write-Host "WARNING: -ClearData flag provided. This will destroy all local runtime persistent data!" -ForegroundColor Red
    $Confirmation = Read-Host "Are you sure you want to delete all local events and results? (y/N)"
    if ($Confirmation -notmatch "^y(es)?`$") {
        Write-Host "Aborting stop operation."
        exit 1
    }
    Write-Host "Stopping and removing local product containers and volumes..."
    docker compose -f docker-compose.prod.yml -f docker-compose.local.yml down -v
} else {
    Write-Host "Stopping local product containers cleanly (data preserved)..."
    docker compose -f docker-compose.prod.yml -f docker-compose.local.yml down
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to stop Docker Compose services."
    exit 1
}

Write-Host "========================================"
Write-Host "AMHI FAN LOCAL PRODUCT STOPPED"
Write-Host "========================================"
