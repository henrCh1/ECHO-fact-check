# ECHO Fact-Checking System - PowerShell Startup Script
# This script starts both the backend API server and the frontend development server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ECHO Fact-Checking System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set virtual environment path
$VENV_PATH = "d:/CUHKSZ/RA/WU_RA/事实核查/code/project/fact_check_system_V2_benchmark/venv/Scripts/Activate.ps1"

Write-Host "[1/4] Checking environment..."
if (!(Test-Path ".env")) {
    Write-Host "WARNING: .env file not found. Make sure GOOGLE_API_KEY is set." -ForegroundColor Yellow
}

Write-Host "[2/4] Starting Backend API Server (port 8000)..."
$BackendCommand = "& '$VENV_PATH'; python -m uvicorn api.main:app --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$BackendCommand"

Write-Host "Waiting for backend to start..."
Start-Sleep -Seconds 5

Write-Host "[3/4] Installing frontend dependencies..."
Set-Location -Path "app"
npm install

Write-Host "[4/4] Starting Frontend Dev Server (port 3000)..."
$FrontendCommand = "npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location -Path 'app'; $FrontendCommand"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Both servers are starting in separate windows!" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API: http://localhost:8000"
Write-Host "Backend Docs: http://localhost:8000/docs"
Write-Host "Frontend: http://localhost:3000"
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit this script..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
