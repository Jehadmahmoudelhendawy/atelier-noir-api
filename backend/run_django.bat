@echo off
echo ==========================================
echo Starting Assistify Django Backend (Proxy)...
echo ==========================================

cd /d "%~dp0"

IF EXIST "..\venv" (
    echo [INFO] Activating virtual environment...
    call ..\venv\Scripts\activate.bat
) ELSE IF EXIST "venv" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo [INFO] Starting Django on port 8000...
python manage.py runserver 0.0.0.0:8000

pause
