@echo off
echo ==========================================
echo Starting Assistify Chatbot Microservice...
echo ==========================================

cd /d "%~dp0"

IF NOT EXIST "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing requirements...
pip install -r requirements.txt

echo [INFO] Starting FastAPI on port 8001...
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

pause
