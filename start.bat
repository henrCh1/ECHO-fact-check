@echo off
chcp 65001 >nul
REM ECHO Fact-Checking System - Windows Startup Script
REM This script starts both the backend API server and the frontend development server

echo ========================================
echo ECHO Fact-Checking System
echo ========================================
echo.

REM Set virtual environment path
set VENV_PATH="d:\CUHKSZ\RA\WU_RA\事实核查\code\project\fact_check_system_V2_benchmark\venv\Scripts\activate.bat"

echo [1/4] Checking environment...
if not exist ".env" (
    echo WARNING: .env file not found. Make sure GOOGLE_API_KEY is set.
)

echo [2/4] Starting Backend API Server (port 8000)...
cd /d %~dp0
start "ECHO Backend" cmd /k "chcp 65001 >nul && call %VENV_PATH% && python -m uvicorn api.main:app --port 8000 --reload || pause"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo [3/4] Installing frontend dependencies...
cd /d %~dp0app
call npm install

echo [4/4] Starting Frontend Dev Server (port 3000)...
start "ECHO Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo Both servers are starting!
echo.
echo Backend API: http://localhost:8000
echo Backend Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo ========================================
echo.
echo Press any key to exit this window...
pause >nul
