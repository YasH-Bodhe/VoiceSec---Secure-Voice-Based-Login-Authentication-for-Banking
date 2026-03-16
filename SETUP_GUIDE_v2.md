# Voice Banking Authentication System - v2.0 Setup Guide

## Overview

This is a **production-ready voice-based banking authentication system** with:
- ✅ **ECAPA-TDNN** speaker verification (high-accuracy embeddings)
- ✅ **Cosine similarity** matching (mathematically correct)
- ✅ **Anti-spoofing detection** (replay & synthetic voice protection)
- ✅ **OTP email verification** (Gmail SMTP via App Passwords)
- ✅ **3-tier authentication**: Voice → OTP (fallback) → Dashboard

---

## Prerequisites

- **Python 3.8+** (tested on 3.10)
- **CUDA 11.8+** (optional, for GPU acceleration)
- **FFmpeg** (for audio format conversion)
- **Gmail Account** (for OTP emails)

---

## Installation Steps

### 1. Clone and Setup Virtual Environment

```bash
cd voice-auth-system
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- **FastAPI** & **Uvicorn** - Web framework
- **SpeechBrain** - ECAPA-TDNN speaker verification
- **PyTorch** - Deep learning backend
- **librosa** - Audio processing
- **scikit-learn** - Cosine similarity metrics
- And more...

**⏱️ Installation may take 5-10 minutes** (large ML models)

### 3. Configure Gmail OTP (Critical!)

The system sends OTPs via Gmail SMTP. **You must configure this:**

#### Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow the prompts to enable 2FA

#### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select **Mail** and **Windows Computer** (or your OS)
3. Google generates a **16-character password** (with spaces)
4. Copy it (removing spaces)

#### Step 3: Update .env File
```bash
cp .env.example .env
```

Edit `.env`:
```bash
SENDER_EMAIL=your-gmail@gmail.com
SENDER_PASSWORD=xxyyzz1122334455  # 16-char app password (no spaces)
```

**Example**: If Google shows `xx yy zz 11 22 33 44 55`, use `xxyyzz1122334455`

### 4. Start the Server

```bash
python -m uvicorn backend.main:app --reload
```

Or use the provided batch file:
```bash
.\run.bat
```

**Expected output:**
```
Uvicorn running on http://127.0.0.1:8000
Models loading...
✓ ECAPA-TDNN Speaker Encoder loaded
✓ Anti-spoofing Model loaded
```

---

## How It Works

### Registration Flow
1. **Create Account** → Name, Email, Password
2. **Record Voice** → 3-5 seconds of audio
3. **Extract Embedding** → ECAPA-TDNN model (192-dim vector)
4. **Store Embedding** → SQLite database

### Login Flow
1. **Enter Email & Password** → Verify authentication
2. **Record Voice** → As during registration
3. **Extract Embedding** → Using same ECAPA-TDNN model
4. **Compute Similarity** → Cosine similarity score (0.0-1.0)

### Decision Logic
| Similarity Score | Action | Threshold |
|---|---|---|
| ≥ 0.85 | **Direct Login** ✅ | High confidence |
| 0.70 - 0.85 | **Send OTP** ⚠️ | Medium confidence |
| < 0.70 | **Reject** ❌ | Low confidence |

**OTP emails expire in 5 minutes**

---

## API Endpoints

### Authentication
- `POST /register` - Create account
- `POST /login` - Password verification
- `POST /enroll_voice` - Record voice during signup
- `POST /verify_voice` - Verify voice during login

### OTP
- `POST /send_otp` - Send OTP to email
- `POST /verify_otp` - Verify OTP code

### Dashboard
- `GET /dashboard` - User dashboard (requires token)
- `POST /update_voice` - Update voice embedding

---

## Testing the System

### Method 1: Via Frontend
1. Open http://localhost:8000/static/register.html
2. Create account, record voice
3. Go to http://localhost:8000/static/login.html
4. Login with voice, verify OTP

### Method 2: Via Python Script
```python
# See test_workflow.py for end-to-end tests
python test_workflow.py
```

### Method 3: API Testing
Use Swagger UI: http://localhost:8000/docs

---

## Configuration

### Audio Processing
```python
# backend/utils/audio_processing.py
SAMPLE_RATE = 16000  # Hz (required for ECAPA-TDNN)
DURATION = 5         # seconds
```

### Thresholds
```python
# backend/verify.py
SIMILARITY_THRESHOLD_HIGH = 0.85  # Direct auth
SIMILARITY_THRESHOLD_LOW = 0.70   # OTP fallback

# backend/antispoof.py
SPOOF_THRESHOLD = 0.5
```

### Email
```bash
# .env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=16-char-app-password
```

---

## Troubleshooting

### Issue: "ECAPA-TDNN model not found"
**Solution:** Models download on first use (~200MB). Ensure internet connection.

### Issue: OTP not sending
**Solution:** Check `.env` credentials:
```bash
# ❌ Wrong
SENDER_PASSWORD=your-gmail-password

# ✅ Correct
SENDER_PASSWORD=xxxx xxxx xxxx xxxx  (Gmail App Password)
```

### Issue: "Zero-norm embedding"
**Solution:** Audio too quiet. Ensure microphone input is at normal speaking volume.

### Issue: Slow performance
**Solution:** Enable GPU in PyTorch:
```python
# backend/model_loader.py
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

---

## Architecture

```
Frontend (HTML/JS)
    ↓
FastAPI Backend
    ↓
┌─────────────────────┐
│ Voice Processing    │
├─────────────────────┤
│ • Load Audio        │
│ • Preprocess        │
│ • Extract Features  │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ ECAPA-TDNN Model    │
├─────────────────────┤
│ • 192-dim embedding │
│ • SpeechBrain       │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ Anti-Spoofing       │
├─────────────────────┤
│ • Detect replays    │
│ • Detect synthesis  │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ Verification        │
├─────────────────────┤
│ • Cosine similarity │
│ • Decision logic    │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ OTP Verification    │
├─────────────────────┤
│ • Gmail SMTP        │
│ • 5-min expiry      │
└─────────────────────┘
    ↓
User Dashboard
```

---

## Performance Notes

- **Model Loading:** ~10 seconds on first startup (cached in memory)
- **Audio Processing:** ~500ms per file
- **Embedding Extraction:** ~100ms per audio file
- **Similarity Computation:** <1ms
- **Total Login:** ~1-2 seconds (including I/O)

---

## Security Considerations

1. **Passwords:** Hashed with bcrypt
2. **Tokens:** JWT with expiry
3. **Embeddings:** Normalized for cosine similarity
4. **OTP:** 6-digit code, 5-minute expiry
5. **Anti-spoofing:** Detects replay attacks

---

## Production Deployment

For production:
1. Change `SECRET_KEY` in `.env` to strong random key
2. Set `DEBUG=False`
3. Use HTTPS (SSL certificate)
4. Deploy to cloud (AWS, GCP, Azure)
5. Use production-grade database (PostgreSQL)
6. Monitor logs and authentication attempts

---

## Support & Issues

For issues, check:
- `test_imports.py` - Verify all dependencies
- `backend/main.py` - Application logs
- `database.db` - SQLite browser to view data

---

## References

- **ECAPA-TDNN Paper:** https://arxiv.org/abs/2005.07143
- **SpeechBrain:** https://github.com/speechbrain/speechbrain
- **PyTorch Audio:** https://pytorch.org/audio/
- **Gmail App Passwords:** https://support.google.com/accounts/answer/185833

---

**Version:** 2.0.0  
**Updated:** March 2026  
**Status:** ✅ Production Ready
