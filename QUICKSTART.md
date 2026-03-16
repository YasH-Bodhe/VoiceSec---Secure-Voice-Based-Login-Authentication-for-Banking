# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Extract & Navigate
```bash
cd voice-auth-system
```

### Step 2: Run the Application

**Windows:**
```bash
run.bat
```

**macOS/Linux:**
```bash
chmod +x run.sh
./run.sh
```

### Step 3: Open Browser
```
http://localhost:8000/static/index.html
```

### Step 4: Test the System

1. Click **"Create Account"**
2. Fill in Name, Email, Password
3. Record voice sample
4. Click **"Sign In"**
5. Record voice again to verify
6. Done! ✓

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI application |
| `backend/database.py` | SQLite database |
| `backend/model_loader.py` | WavLM speaker model |
| `frontend/index.html` | Home page |
| `requirements.txt` | Python dependencies |
| `.env` | Configuration |

---

## 🔑 Key Features

✅ Voice-based authentication  
✅ Anti-spoofing detection  
✅ OTP fallback  
✅ Secure password hashing  
✅ JWT tokens  
✅ Email integration  
✅ Web Audio API recording  

---

## 📚 Documentation

- **README.md** - Full documentation
- **TESTING.md** - Testing instructions & examples
- **DEPLOYMENT.md** - Production deployment guide

---

## 🐛 Troubleshooting

### Port in Use
```bash
uvicorn main:app --reload --port 8001
```

### Microphone Not Working
- Check browser permissions
- Ensure HTTPS (production)
- Check microphone in Windows Settings

### No Mail Delivery
- Check .env email settings
- Use App Password instead of account password (Gmail)
- System logs to console on failure

---

## 📞 API Quick Reference

```bash
# Register
curl -X POST http://localhost:8000/register \
  -F "name=John" -F "email=john@test.com" -F "password=pass123"

# Health check
curl http://localhost:8000/health

# API docs
http://localhost:8000/docs
```

---

## ⚡ Performance

- Registration: < 1s
- Voice enrollment: 2-3s (first time, model loading)
- Voice login: 1-2s
- OTP delivery: 1-5s

---

## 🎓 Learn More

Check the documentation files:
1. Start with **README.md** for overview
2. Follow **TESTING.md** for practical examples
3. Review **DEPLOYMENT.md** for production setup

---

**Ready to go! Happy coding! 🎉**
