@echo off
setlocal enabledelayedexpansion
title BhashaShield Orchestrator

echo =====================================================================
echo                BHASHASHIELD AI SECURITY INTELLIGENCE
echo                Full Project Orchestrator (Backend + Frontend)
echo =====================================================================
echo.

cd /d "%~dp0"

echo [*] Starting BhashaShield Backend API Service in a dedicated terminal...
start "BhashaShield Backend API (Port 8000)" cmd /k call "%~dp0start_backend.bat"

echo [*] Waiting 3 seconds for backend initialization...
timeout /t 3 /nobreak >nul

echo [*] Starting BhashaShield 3D Cybersecurity Frontend in a dedicated terminal...
start "BhashaShield 3D Frontend (Port 5173)" cmd /k "cd /d \"%~dp0frontend\" && echo [*] Starting Vite Dev Server... && npm run dev"

echo.
echo =====================================================================
echo [+] Both services launched:
echo     - Backend API:       http://127.0.0.1:8000
echo     - API Docs:          http://127.0.0.1:8000/docs
echo     - Frontend Web App:  http://localhost:5173
echo.
echo [*] Keep the opened terminal windows running while using BhashaShield.
echo =====================================================================
echo.
pause
