# 🎬 FFmpeg Setup Guide

## 📋 Current Status

✅ **Frontend Fixed**: Audio now encodes to proper WAV format before sending to backend  
✅ **Backend Improved**: Supports WAV, WebM, MP3, OGG with automatic detection  
⚠️ **Missing Dependency**: FFmpeg needed for WebM fallback (not essential with new frontend)

---

## 🚀 Quick Solution (Recommended)

With the **frontend fixes**, audio should be encoded to WAV format before reaching the backend. FFmpeg is only needed as a **fallback**. You have 2 options:

### **Option 1: Easy - Use Conda (Recommended)**
```bash
conda install ffmpeg
```

### **Option 2: Download Pre-built Binary**

1. Download FFmpeg from: **https://ffmpeg.org/download.html**
   - Choose "Windows builds from" → BtbN/FFmpeg-Builds
   - Download: `ffmpeg-master-latest-win64-gpl-shared.zip`

2. Extract to: `C:\ffmpeg`

3. Add to PATH:
   - Press `Win + X` → System → Advanced system settings
   - Click "Environment Variables"
   - Edit `Path` and add: `C:\ffmpeg\bin`
   - Click OK and restart terminal

4. Verify:
   ```cmd
   ffmpeg -version
   ```

### **Option 3: Chocolatey (Requires Admin)**
If you have admin rights:
```cmd
choco install ffmpeg -y
```

---

## ✅ Verify Installation

Test if ffmpeg works:
```cmd
ffmpeg -version
```

You should see version info like:
```
ffmpeg version N-...
Copyright (c) ...
```

---

## 🧪 Test System After Installation

After installing ffmpeg (or if you skip it):

```bash
cd "d:\Yash\New folder\voice-auth-system"
python test_workflow.py
```

Should show:
```
✅ TEST COMPLETE - NO ISSUES!
```

---

## 📊 What Each Audio Loading Method Does

The backend tries audio formats in this order:

| # | Method | Format | Requires | Status |
|---|--------|--------|----------|--------|
| 1 | librosa | Any | audioread | ✅ Works |
| 2 | soundfile | WAV/FLAC | Built-in | ✅ Works |
| 3 | scipy | WAV | Built-in | ✅ Works |
| 4 | pydub | WebM/MP3/OGG | **FFmpeg** | ⚠️ Needs ffmpeg |
| 5 | ffmpeg | Any | **FFmpeg** | ⚠️ Last resort |

**With frontend fix**: Audio sent to backend is already WAV → Methods 1-3 work → ffmpeg NOT needed!

---

## 🎯 Why FFmpeg is Optional

- **Before Fix**: Browser sends WebM → librosa/soundfile fail → pydub needs ffmpeg
- **After Fix**: Browser encodes to WAV → librosa/soundfile succeed → ffmpeg never called

**But keeping ffmpeg installed ensures 100% compatibility** if there are any edge cases.

---

## 🔧 Install Without Admin Rights

If you can't run admin commands:

1. Download the portable build: https://ffmpeg.org/download.html
2. Extract to any folder (example: `D:\ffmpeg`)
3. Add that folder to your Python environment:

**In Power Shell:**
```powershell
$env:PATH += ";D:\ffmpeg"
ffmpeg -version  # Should work now
```

**Or edit your code to specify path:**
```python
import os
os.environ['PATH'] = 'D:\\ffmpeg;' + os.environ['PATH']
import pydub  # Will now find ffmpeg
```

---

## ✨ Next Steps

### Immediately:
1. Test with frontend: `python test_workflow.py`
2. If it passes → You're done! System works
3. If it fails with WebM errors → Install FFmpeg from above options

### Later (Optional):
- Deploy frontend to actual browser
- Test with real microphone recordings
- System will automatically handle any format

---

## 💡 Troubleshooting

**Q: Getting "ffmpeg not found" error?**
- Answer: Either skip ffmpeg (system works with WAV) OR install from options above
- Verify with: `ffmpeg -version` in terminal
- If not found: Update PATH and restart terminal

**Q: Still getting WebM format errors?**
- Answer: Check browser console for encoder errors
- Verify wav-encoder library is loaded (search console for "Encoded to WAV")
- Check server logs for specific error

**Q: Audio works on my computer but might fail elsewhere?**
- Answer: Install ffmpeg for 100% compatibility guarantee
- FFmpeg is free, open-source, platform-independent

---

## 📝 File Location Check

Verify these files have the wav-encoder fix:

- ✅ `frontend/register.html` - Line 9: `<script src="...wav-encoder..."`
- ✅ `frontend/login.html` - Line 8: `<script src="...wav-encoder..."`
- ✅ `backend/utils/audio_processing.py` - load_audio() has pydub support

---

## 🎉 Success Criteria

After setup, you should see:

```
✓ librosa loaded successfully
✓ Encoded to WAV: XXXXXX bytes, magic bytes: RIFF
✓ Voice enrolled successfully!
✓ Voice verification PASSED
✓ JWT token generated
```

---

**Your system is ready!** FFmpeg is completely optional with the new frontend encoding. 🚀

