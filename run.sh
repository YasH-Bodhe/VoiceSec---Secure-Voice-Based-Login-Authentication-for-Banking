#!/bin/bash

# Voice Banking Authentication System - Startup Script for Unix/Linux/macOS

echo ""
echo "================================"
echo "Voice Banking Authentication"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.12+ from https://www.python.org/"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if ! pip show fastapi &> /dev/null; then
    echo "Installing required packages..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error installing requirements"
        exit 1
    fi
fi

# Navigate to backend and start server
echo ""
echo "Starting FastAPI server..."
echo "Access the application at: http://localhost:8000/static/index.html"
echo "API documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
uvicorn main:app --reload

