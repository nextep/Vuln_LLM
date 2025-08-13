# PowerShell script for Windows deployment of Vulnerable LLM Application
# Designed to work with existing Ollama and Docker installations

param(
    [string]$OpenWebUIUrl = "http://192.168.1.110:8888",
    [switch]$SkipTemplateImport = $false,
    [switch]$Force = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Vulnerable LLM App - Windows Setup" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/5] Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not running"
    }
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Error "Docker is not running. Please start Docker Desktop."
    exit 1
}

Write-Host "[2/5] Checking Ollama status..." -ForegroundColor Yellow
try {
    $ollamaResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Ollama is running on port 11434" -ForegroundColor Green
} catch {
    Write-Error "Ollama is not running on port 11434. Please start Ollama service."
    exit 1
}

Write-Host "[3/5] Checking OpenWebUI status..." -ForegroundColor Yellow
try {
    $openwebuiResponse = Invoke-RestMethod -Uri "$OpenWebUIUrl/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ OpenWebUI is accessible at $OpenWebUIUrl" -ForegroundColor Green
} catch {
    if (-not $Force) {
        Write-Warning "OpenWebUI at $OpenWebUIUrl is not accessible."
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne "y") { exit 1 }
    } else {
        Write-Warning "OpenWebUI check failed but continuing due to -Force flag"
    }
}

# Set environment variables
Write-Host "[4/5] Setting up environment..." -ForegroundColor Yellow
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"

# Import templates (optional)
if (-not $SkipTemplateImport) {
    Write-Host "[5/5] Importing vulnerability templates..." -ForegroundColor Yellow
    try {
        Set-Location "openwebui_templates"
        python import_templates.py --url $OpenWebUIUrl
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Template import failed. You can import them manually later."
        } else {
            Write-Host "✓ Templates imported successfully" -ForegroundColor Green
        }
    } catch {
        Write-Warning "Template import failed: $($_.Exception.Message)"
    } finally {
        Set-Location ".."
    }
} else {
    Write-Host "[5/5] Skipping template import (use -SkipTemplateImport flag)" -ForegroundColor Yellow
}

# Build and deploy
Write-Host ""
Write-Host "Building and starting the vulnerable LLM application..." -ForegroundColor Yellow
docker-compose down --remove-orphans
docker-compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start the application."
    exit 1
}

# Verify deployment
Write-Host ""
Write-Host "Verifying deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

try {
    $appResponse = Invoke-RestMethod -Uri "http://localhost:5001/" -Method GET -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✓ Application is responding" -ForegroundColor Green
} catch {
    Write-Warning "Application health check failed, but containers may still be starting"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Deployment Completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Application URLs:" -ForegroundColor White
Write-Host "  Main Interface: http://localhost:5001" -ForegroundColor Cyan
Write-Host "  Advanced Testing: http://localhost:5001/advanced-testing" -ForegroundColor Cyan
Write-Host "  OpenWebUI: $OpenWebUIUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop the application:" -ForegroundColor White
Write-Host "  docker-compose down" -ForegroundColor Yellow
Write-Host ""
Write-Host "To view logs:" -ForegroundColor White
Write-Host "  docker-compose logs -f" -ForegroundColor Yellow
Write-Host ""