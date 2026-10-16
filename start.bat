@echo off
title Smart Campus Electronics Rental System
echo ===================================================
echo 🚀 SMART CAMPUS ELECTRONICS RENTAL & MANAGEMENT SYSTEM
echo ===================================================
echo.

IF NOT EXIST ".venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
    python seed_data.py
) ELSE (
    call .venv\Scripts\activate
)

IF NOT EXIST "instance\campus_rental.db" (
    echo [INFO] Database not found. Seeding initial data...
    python seed_data.py
)

echo [INFO] Starting Flask Server at http://127.0.0.1:5000
python run.py
pause
