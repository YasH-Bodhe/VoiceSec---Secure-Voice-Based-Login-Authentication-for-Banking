# Installation Guide

Complete step-by-step installation instructions for the Voice Banking Authentication System.

## Prerequisites

Before installing, ensure you have:

- **Python 3.12+** - Download from https://www.python.org/downloads/
- **pip** - Usually comes with Python
- **Git** (optional) - For cloning if from GitHub
- **4GB RAM minimum** - For running models
- **1GB disk space** - For dependencies and database
- **Microphone** - Any working microphone/headset
- **Internet connection** - For downloading models on first run

### Check Prerequisites

```bash
# Check Python version
python --version
# Should show Python 3.12.x or higher

# Check pip
pip --version
# Should show pip 23.x or higher
```

---

## Installation Steps

### Step 1: Prepare Directory

```bash
# Navigate to where you want to install
cd "C:\Your\Projects\Path"  # Windows
cd ~/Projects/path          # macOS/Linux

# The project folder is already created as voice-auth-system
cd voice-auth-system
```

### Step 2: Setup Python Virtual Environment

A virtual environment keeps project dependencies isolated.

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install 19 packages:
- **FastAPI** - Web framework
- **PyTorch** - Deep learning
- **Transformers** - AI models
- **Librosa** - Audio processing
- **Torchaudio** - Audio utilities
- **Numpy** - Numerical computing
- **And 13 more...**

**Installation time:** 5-15 minutes depending on internet speed

Verify installation:
```bash
pip list
# Should show all packages in requirements.txt
```

### Step 5: Configure Environment

```bash
# Copy template (already exists, but here's how to recreate)
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux
```

Edit `.env` file to configure:

**Basic Setup (Development):**
- No changes needed - defaults are fine

**With Email OTP (Optional):**
```ini
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

To get Gmail App Password:
1. Enable 2-factor authentication on Gmail
2. Visit https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer" (or your device)
4. Copy the 16-character password
5. Paste in `.env` as SENDER_PASSWORD

### Step 6: Initialize Database

The database will be created automatically on first run, but you can manually initialize:

```bash
cd backend
python -c "from database import Database; Database()"
cd ..
```

This creates `database/database.db` with all tables.

### Step 7: Download AI Models

On first run, models will be downloaded (~500MB+):

```bash
# This happens automatically when you start the server
# But you can pre-download:

python -c "
from backend.model_loader import load_models
load_models()
"
```

Models downloaded:
- **WavLM** (337MB) - Speaker embedding model
- **Supporting files** (~200MB)

### Step 8: Start the Application

**Easy Method (Recommended):**

Windows:
```bash
run.bat
```

macOS/Linux:
```bash
chmod +x run.sh
./run.sh
```

**Manual Method:**

```bash
cd backend
uvicorn main:app --reload
cd ..
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 9: Access the Application

Open your web browser and go to:
```
http://localhost:8000/static/index.html
```

You should see the home page with:
- 🎤 Voice Banking Auth heading
- Features section
- How it works
- Create Account button

### Step 10: Test Registration

1. Click "Create Account"
2. Fill in details:
   - Name: `Test User`
   - Email: `test@example.com`
   - Password: `testpass123`
3. Click "Create Account"
4. Record voice for 3-5 seconds
5. Click "Enroll Voice"
6. You should see success message

---

## Verify Installation

### Check All Components

**1. Backend Running:**
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","timestamp":"..."}
```

**2. API Documentation:**
```
Open: http://localhost:8000/docs
# Interactive API explorer should load
```

**3. Database Created:**
```bash
# File should exist
ls database/database.db          # macOS/Linux
dir database\database.db         # Windows
```

**4. Microphone Access:**
- Open http://localhost:8000/static/register.html
- Click "Start Recording"
- Allow microphone access when prompted
- You should hear microphone feedback

---

## Troubleshooting Installation

### Python Not Found

```bash
# Error: 'python' is not recognized

# Solution 1: Use python3
python3 --version

# Solution 2: Add Python to PATH
# Windows: Reinstall Python, check "Add Python to PATH"
# macOS: brew install python3
# Linux: apt-get install python3
```

### pip installation fails

```bash
# Error: Failed to build wheel for [package]

# Solution 1: Update pip
pip install --upgrade pip

# Solution 2: Use binary wheels
pip install --only-binary :all: -r requirements.txt

# Solution 3: Install build tools
# Windows: Install Microsoft Visual C++ 14.0 or greater
# Linux: sudo apt-get install build-essential python3-dev
# macOS: xcode-select --install
```

### Out of Memory During Installation

```bash
# Error: MemoryError

# Solution 1: Close other applications
# Solution 2: Install one package at a time
pip install fastapi
pip install torch
# ... etc

# Solution 3: Use lower-memory models
# Edit backend/model_loader.py
# Change: microsoft/wavlm-base-plus-sv
# To: openai/whisper-base
```

### Microphone Not Detected

```bash
# Browser console error: "No audio input devices found"

# Solution 1: Check system audio settings
# Windows: Settings > Sound > Input > Microphone enabled
# macOS: System Preferences > Security & Privacy > Microphone
# Linux: Check alsamixer or pavucontrol

# Solution 2: Use HTTPS
# Development: Works on localhost
# Production: Requires HTTPS (Let's Encrypt)

# Solution 3: Test with Web Audio API
# Browser console:
navigator.mediaDevices.enumerateDevices()
  .then(devices => console.log(devices));
```

### Port 8000 Already in Use

```bash
# Error: Address already in use

# Solution 1: Use different port
uvicorn main:app --port 8001

# Solution 2: Kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :8000
kill -9 <PID>

# Solution 3: Check what's using it
# Windows: netstat -ano
# macOS/Linux: lsof -i :8000
```

### Models Not Downloading

```bash
# Error: Failed to download model

# Solution 1: Check internet connection
ping huggingface.co

# Solution 2: Manual download
# Visit: https://huggingface.co/microsoft/wavlm-base-plus-sv
# Download and place in ~/.cache/huggingface/

# Solution 3: Use offline mode
# Set environment variable:
export HF_OFFLINE=1

# Solution 4: Retry with timeout
export HF_DATASETS_TIMEOUT=1000
pip install -r requirements.txt
```

### Database Connection Error

```bash
# Error: Unable to open database file

# Solution 1: Create database directory
mkdir database

# Solution 2: Fix permissions
chmod 755 database

# Solution 3: Reset database
rm database/database.db
# It will be recreated on next run

# Solution 4: Use absolute path in .env
DATABASE_PATH=/full/path/to/database.db
```

---

## Post-Installation

### 1. Configure Email (Optional)

For OTP delivery, configure SMTP in `.env`:

```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

Test email:
```python
# In Python console:
from backend.otp_service import send_otp_email

send_otp_email("test@example.com", "123456")
```

### 2. Test All Features

Follow [TESTING.md](TESTING.md) for comprehensive testing:
- User registration
- Voice enrollment
- Voice login
- OTP verification
- Anti-spoofing detection

### 3. Review Documentation

- **README.md** - Full system documentation
- **QUICKSTART.md** - Quick reference
- **TESTING.md** - Testing guide
- **DEPLOYMENT.md** - Production deployment
- **PROJECT_STRUCTURE.md** - File organization

### 4. Customize Settings

Edit configuration files:
- `.env` - Environment variables
- `backend/utils/similarity.py` - Voice thresholds
- `backend/antispoof.py` - Spoof detection
- `frontend/css/style.css` - Styling

---

## System Requirements Summary

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.12 | 3.12+ |
| RAM | 4GB | 8GB+ |
| Disk | 2GB | 5GB+ |
| CPU | Dual-core | Quad-core |
| GPU | None | CUDA 11+ |
| Bandwidth | 1Mbps | 10Mbps+ |
| Microphone | Any | Headset |

---

## Performance Checklist

After installation, verify performance:

- [ ] Application starts in < 5 seconds
- [ ] First model load takes < 30 seconds
- [ ] Audio recording works without lag
- [ ] Registration completes in < 1 second
- [ ] Voice enrollment takes 2-3 seconds
- [ ] Voice verification takes 1-2 seconds
- [ ] OTP delivered within 5 seconds
- [ ] No console errors or warnings

---

## Next Steps

1. ✅ Installation complete
2. → Read: [QUICKSTART.md](QUICKSTART.md) - 5-minute guide
3. → Follow: [TESTING.md](TESTING.md) - Test the system
4. → Review: [README.md](README.md) - Full documentation
5. → Plan: [DEPLOYMENT.md](DEPLOYMENT.md) - For production

---

## Getting Help

If you encounter issues:

1. **Check error message** - Most errors are self-explanatory
2. **Search this guide** - Use Ctrl+F to find error type
3. **Check logs** - Look in console output
4. **Test components** - Verify each piece works
5. **Review documentation** - Detailed explanations provided

---

## Clean Installation (Start Over)

If you need to start fresh:

```bash
# Remove virtual environment
rm -rf venv          # macOS/Linux
rmdir /s venv        # Windows

# Remove database
rm database/database.db

# Remove cache
pip cache purge

# Restart from Step 2
```

---

**Installation complete! 🎉 Your voice authentication system is ready to use.**

For quick start, see [QUICKSTART.md](QUICKSTART.md)

