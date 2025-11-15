#!/usr/bin/env pwsh
# Setup TMDB API Key and Run JellyRancher
# This script sets up the environment and launches the application

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setting up JellyRancher Environment" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Set TMDB API Key
$env:TMDB_API_KEY = "a71ed25dc11e509b52067f0c10df1af4"
Write-Host "[OK] TMDB API Key configured" -ForegroundColor Green
Write-Host "    Key: $env:TMDB_API_KEY" -ForegroundColor Gray
Write-Host ""

# Check if virtual environment exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[OK] Virtual environment found" -ForegroundColor Green
    
    # Activate virtual environment
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
    & .venv\Scripts\Activate.ps1
    
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "[WARN] Virtual environment not found at .venv\" -ForegroundColor Yellow
    Write-Host "       Using system Python installation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Test Media Folder Ready" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Location: $(Get-Location)\test_media" -ForegroundColor White
Write-Host ""
Write-Host "Contains:" -ForegroundColor White
Write-Host "  - 7 movies (various formats)" -ForegroundColor Gray
Write-Host "  - 6 TV shows (organized and messy)" -ForegroundColor Gray
Write-Host "  - 41 total video files" -ForegroundColor Gray
Write-Host "  - 6 subtitle files" -ForegroundColor Gray
Write-Host "  - 2 multi-part episodes (for NFO testing)" -ForegroundColor Gray
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Launching JellyRancher GUI..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Run the application
python jelly_rancher_clean.py

# Check if application exited with error
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Application exited with error code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}



