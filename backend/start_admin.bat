@echo off
:: Guardian Shield Backend - Must be Run as Administrator
:: Right-click -> Run as administrator
cd /d "%~dp0"

:: Verify admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click start_admin.bat and select "Run as administrator"
    pause
    exit /b 1
)

echo ========================================
echo  Guardian Shield Backend (Administrator)
echo ========================================
echo.
echo Admin privileges confirmed.
echo Starting uvicorn on port 8000...
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
