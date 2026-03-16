# ⚡ QUICK START - 3 COMMANDS TO RUN

## ✅ SYSTEM STATUS: FULLY WORKING

All tests passed! Voice authentication is ready to use.

---

## 🚀 START SERVER (Open Command Prompt)

### Command 1:
```cmd
cd "d:\Yash\New folder\voice-auth-system"
.\venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Wait for:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

(Models will load in ~30-60 seconds first time)

---

## 💻 OPEN BROWSER

### Link:
```
http://localhost:8000/static/login.html
```

---

## 🎯 USE THE SYSTEM

### 1. Register
- Click: "Register here"
- Fill: Name, Email, Password
- Click: Register
- **Save your User ID!**

### 2. Enroll Voice
- Click: "🎤 Start Recording"
- Speak for 2-3 seconds
- Click: Stop Recording
- Click: "Enroll Voice"
- ✅ See: "Voice enrolled successfully!"

### 3. Login
- Go back to login page
- Enter: Email + Password
- Click: Sign In
- ✅ See: "Password verified..."

### 4. Verify Voice
- Click: "🎤 Start Recording"
- Speak SAME phrase as enrollment
- Click: Stop Recording
- Click: "✓ Verify Voice"
- ✅ See: Similarity score graph + "Authentication successful!"

---

## 🧪 TEST THE SYSTEM

### Run Complete Test:
```cmd
cd "d:\Yash\New folder\voice-auth-system"
python test_workflow.py
```

**Should show:**
```
✅ User registered
✅ Audio file created
✅ Voice enrolled successfully!
✅ Password verified
✅ Verification successful!
✅ TEST COMPLETE
```

---

## 🆘 IF SOMETHING GOES WRONG

### "Port 8000 already in use"
```cmd
netstat -ano | findstr :8000
taskkill /PID <NUMBER> /F
```

### "No voice enrollment found"
```cmd
REM Check if enrollment was saved:
curl "http://localhost:8000/user_status/10"
REM If "has_voice_enrollment": false, try enrolling again
```

### Server won't start
- Wait 60 seconds (models loading)
- Check cmd window for error messages
- Try killing Python: `taskkill /F /IM python.exe`

### Models downloading
- First run: Downloads WavLM model (~300MB)
- Internet connexion required
- Be patient! Normal behavior

---

## 📊 WHAT YOU'LL SEE IN THE UI

After voice verification, you'll see:

### Green Doughnut Chart
- Shows similarity score (0-100%)
- Color indicates authentication status:
  - 🟢 Green = Direct authentication
  - 🟡 Yellow = OTP required
  - 🔴 Red = Try again

### Embedding Bar Chart
- Shows voice characteristics
- First 50 dimensions of 512-dim embedding
- Helps understand voice representation

### Threshold Information
```
✅ Direct Auth: Score ≥ 0.65
⚠️ OTP Required: Score 0.45-0.65
❌ Try Again: Score < 0.45
```

---

## 💡 TIPS FOR BEST RESULTS

1. **Enrollment Quality**
   - Speak clearly for 2-3 seconds
   - Use natural voice (not whisper/shout)
   - Minimize background noise
   - Pick a phrase you can easily repeat

2. **Verification Quality**
   - Speak EXACTLY like enrollment
   - Same voice tone and speed
   - Similar room/environment
   - Good microphone pickup

3. **First Time**
   - Let system load completely (watch spinner)
   - Grant microphone permission
   - Speak one phrase per recording
   - Be patient with model inference

---

## 🔗 USEFUL ENDPOINTS

Check without UI:

```cmd
REM Health check
curl http://localhost:8000/health

REM Check user enrollment status (replace 10 with user_id)
curl http://localhost:8000/user_status/10
```

---

## 📝 TEST USERS ALREADY IN DATABASE

If you want to test with existing users, they're stored here:
```
d:\Yash\New folder\voice-auth-system\database\database.db
```

Or create fresh tests every time (above test_workflow.py does this)

---

## ✨ THAT'S IT!

You're ready to go! Start the server and test your voice authentication system.

**Enjoy! 🎤**

