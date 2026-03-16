@echo off
REM Voice Banking Authentication System - Startup Script for Windows

echo.
echo ================================
echo Voice Banking Authentication
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.12+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error installing requirements
        pause
        exit /b 1
    )
)

REM Navigate to backend and start server
echo.
echo Starting FastAPI server...
echo Access the application at: http://localhost:8000/static/index.html
echo API documentation at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

cd backend
uvicorn main:app --reload

pause
