@echo off
setlocal enabledelayedexpansion
title BhashaShield Backend API Service

echo =====================================================================
echo                BHASHASHIELD AI SECURITY INTELLIGENCE
echo                Backend API Startup ^& Health Verification
echo =====================================================================
echo.

:: 1. Navigate to repository root
cd /d "%~dp0"
echo [*] Working Directory: %CD%

:: 2. Set PYTHONPATH to backend directory
set "PYTHONPATH=%~dp0backend"
echo [*] PYTHONPATH set to: %PYTHONPATH%

:: 3. Verify Python availability
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.10+ or ensure it is added to your PATH environment variable.
    goto :FAIL
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo [*] Using: !PY_VER!

:: 4. Port Conflict Detection & Prevention (Port 8000)
echo [*] Checking port 8000 availability...
set "CONFLICT_PID="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    set "CONFLICT_PID=%%a"
)

if defined CONFLICT_PID (
    echo [!] WARNING: Port 8000 is already in use by process PID !CONFLICT_PID!.
    echo [*] Checking if stale BhashaShield python process is holding the port...
    tasklist /fi "PID eq !CONFLICT_PID!" | findstr /i "python" >nul
    if %ERRORLEVEL% EQU 0 (
        echo [*] Automatically terminating orphaned Python process !CONFLICT_PID! on port 8000...
        taskkill /f /pid !CONFLICT_PID! >nul 2>&1
        timeout /t 1 /nobreak >nul
        echo [+] Port 8000 successfully freed.
    ) else (
        echo [ERROR] Port 8000 is occupied by an external application (PID !CONFLICT_PID!).
        echo Please free port 8000 before running BhashaShield.
        goto :FAIL
    )
) else (
    echo [+] Port 8000 is free and available.
)

:: 5. Initialize Database and Demo Data Check
echo [*] Checking backend initialization...
python -c "import sys; sys.path.insert(0, 'backend'); from app.database import init_db; init_db()" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Database initialization check returned non-zero code. Continuing startup...
)

:: 6. Launch Uvicorn Server with Safe Reload Directory
echo.
echo =====================================================================
echo [+] Launching FastAPI server on http://127.0.0.1:8000
echo [+] Swagger Documentation: http://127.0.0.1:8000/docs
echo [+] OpenAPI Schema: http://127.0.0.1:8000/openapi.json
echo [+] Active Mode: Multilingual Rule Engine (Rules-Only Mode)
echo [+] Press Ctrl+C in this terminal to shut down gracefully.
echo =====================================================================
echo.

python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload --reload-dir backend\app

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Uvicorn process terminated with exit code %ERRORLEVEL%.
    goto :FAIL
)

goto :END

:FAIL
echo.
echo [!] Server failed to start or encountered a critical error.
echo [!] Review the diagnostic output above.
pause
exit /b 1

:END
pause
