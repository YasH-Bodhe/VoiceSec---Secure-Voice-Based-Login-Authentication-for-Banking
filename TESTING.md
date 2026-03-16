# Testing Guide - Voice Banking Authentication System

## Unit Testing

### Test Database Operations

```python
# test_database.py
from backend.database import Database

def test_user_creation():
    db = Database(':memory:')  # Use in-memory DB for testing
    user_id = db.create_user('Test User', 'test@example.com', 'hashed_pwd')
    assert user_id is not None
    
    user = db.get_user_by_id(user_id)
    assert user['email'] == 'test@example.com'

def test_voice_embedding():
    db = Database(':memory:')
    user_id = db.create_user('Test User', 'test@example.com', 'hashed_pwd')
    embedding = [0.1] * 512
    db.save_voice_embedding(user_id, embedding, '/path/to/audio.wav')
    
    retrieved = db.get_voice_embedding(user_id)
    assert retrieved == embedding
```

### Test Audio Processing

```python
# test_audio.py
from backend.utils.audio_processing import normalize_audio, extract_mfcc
import numpy as np

def test_normalize_audio():
    audio = np.array([0.5, 1.0, 0.5, -0.5])
    normalized = normalize_audio(audio)
    assert np.max(np.abs(normalized)) <= 1.0

def test_mfcc_extraction():
    audio = np.random.randn(16000)  # 1 second at 16kHz
    mfcc = extract_mfcc(audio)
    assert mfcc.shape[0] == 13  # 13 MFCC coefficients
```

### Test Similarity Computation

```python
# test_similarity.py
from backend.utils.similarity import cosine_similarity, make_decision

def test_cosine_similarity():
    embedding1 = [1, 0, 0, 0]
    embedding2 = [1, 0, 0, 0]
    
    similarity = cosine_similarity(embedding1, embedding2)
    assert abs(similarity - 1.0) < 0.001  # Should be 1.0

def test_decision_making():
    # Test high confidence
    decision = make_decision(0.85)
    assert decision['decision'] == 'success'
    assert not decision['requires_otp']
    
    # Test medium confidence
    decision = make_decision(0.70)
    assert decision['decision'] == 'medium'
    assert decision['requires_otp']
    
    # Test low confidence
    decision = make_decision(0.50)
    assert decision['decision'] == 'failed'
```

## Integration Testing

### Test Registration Flow

```bash
# 1. Register a user
curl -X POST "http://localhost:8000/register" \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "password=password123"

# Response should contain user_id
# Expected: {"success": true, "user_id": 1, ...}
```

### Test Voice Enrollment

```bash
# 1. Record a voice sample (save as voice.wav)
# 2. Enroll the voice

curl -X POST "http://localhost:8000/enroll_voice" \
  -F "user_id=1" \
  -F "audio=@voice.wav"

# Response: {"success": true, "embedding_dim": 512}
```

### Test Login Flow

```bash
# 1. Password verification
curl -X POST "http://localhost:8000/login" \
  -F "email=john@example.com" \
  -F "password=password123"

# Response: {"success": true, "user_id": 1, "next_step": "voice_verification"}

# 2. Voice verification
curl -X POST "http://localhost:8000/verify_voice" \
  -F "user_id=1" \
  -F "audio=@voice.wav"

# Response (if successful):
# {"success": true, "authenticated": true, "similarity_score": 0.92, "token": "..."}
```

### Test OTP Flow

```bash
# 1. Send OTP
curl -X POST "http://localhost:8000/send_otp" \
  -F "user_id=1"

# Response: {"success": true, "expiry_seconds": 300}

# 2. Verify OTP (check email for the code)
curl -X POST "http://localhost:8000/verify_otp" \
  -F "user_id=1" \
  -F "otp_code=123456"

# Response: {"success": true, "authenticated": true, "token": "..."}
```

## Frontend Testing

### Test Browser Console

```javascript
// Check if voice recording works
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => console.log('Microphone access granted'))
  .catch(err => console.error('Microphone error:', err));

// Test localStorage
localStorage.setItem('test', 'value');
console.log(localStorage.getItem('test'));

// Test API calls
fetch('/health')
  .then(r => r.json())
  .then(d => console.log('API Response:', d));
```

### Test All Pages Load

- [ ] http://localhost:8000/static/index.html - Home loads
- [ ] http://localhost:8000/static/register.html - Registration loads
- [ ] http://localhost:8000/static/login.html - Login loads
- [ ] Check console for JavaScript errors

## Microphone Testing

### Test Microphone Access

```javascript
// In browser console
navigator.mediaDevices.enumerateDevices()
  .then(devices => {
    const audioInput = devices.filter(d => d.kind === 'audioinput');
    console.log('Available microphones:', audioInput);
  });
```

### Test Audio Recording

1. Go to `/static/register.html`
2. Create a test account
3. Click "Start Recording"
4. Speak for 3-5 seconds
5. Click "Stop Recording"
6. Check if audio plays back correctly
7. Submit voice enrollment

## API Testing with cURL

### Health Check

```bash
curl http://localhost:8000/health
```

### Get API Docs

```
Open browser: http://localhost:8000/docs
```

### Test User Creation

```bash
curl -X POST "http://localhost:8000/register" \
  -F "name=Test User" \
  -F "email=test123@example.com" \
  -F "password=testpass123"
```

### Test with Multiple Users

```bash
# Create 3 test users
for i in {1..3}; do
  curl -X POST "http://localhost:8000/register" \
    -F "name=User $i" \
    -F "email=user$i@example.com" \
    -F "password=password123"
done
```

## Performance Testing

### Test High-Load Registration

```python
import concurrent.futures
import requests

def register_user(i):
    data = {
        'name': f'User {i}',
        'email': f'user{i}@test.com',
        'password': 'testpass123'
    }
    return requests.post('http://localhost:8000/register', data=data)

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(register_user, i) for i in range(100)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
    print(f'Registered {sum(1 for r in results if r.status_code == 200)} users')
```

### Test Audio Processing Speed

```python
import time
from backend.utils.audio_processing import preprocess_audio

audio_file = 'voice_sample.wav'
start = time.time()
for _ in range(100):
    audio = preprocess_audio(audio_file)
elapsed = time.time() - start
print(f'100 audio processings took {elapsed:.2f}s ({elapsed/100:.4f}s each)')
```

## Test Scenarios

### Scenario 1: Happy Path (Successful Authentication)

1. Register with good credentials
2. Record clear voice sample (low noise)
3. Enroll voice
4. Login with same voice
5. Should succeed without OTP

**Expected Result**: Direct login success ✓

### Scenario 2: Medium Confidence (OTP Required)

1. Register and enroll voice
2. Read same text but with slight variation
3. Login with slightly different voice
4. Should trigger OTP

**Expected Result**: OTP required ✓

### Scenario 3: Failed Authentication

1. Register user A
2. Record user A's voice and enroll
3. Try to login as user A with user B's voice
4. Should fail (similarity too low)

**Expected Result**: Authentication failed ✓

### Scenario 4: Spoof Detection

1. Register user
2. Enroll voice
3. Create replay attack (replay the recorded audio)
4. Try to login with replayed audio

**Expected Result**: Spoof detected, denied ✓

### Scenario 5: OTP Timeout

1. Trigger OTP
2. Wait 6 minutes
3. Try to verify OTP
4. Should fail (expired)

**Expected Result**: OTP expired ✓

## Debugging

### Enable Debug Logging

In `main.py`, change:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Check Database Contents

```python
from backend.database import db

# Get all users
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('SELECT * FROM users')
for user in cursor.fetchall():
    print(f"User: {user['email']}, Created: {user['created_at']}")
conn.close()
```

### Test Models

```python
from backend.model_loader import get_wavlm_model, get_antispoof_model
import numpy as np

# Test WavLM
wavlm = get_wavlm_model()
fake_audio = np.random.randn(16000)
embedding = wavlm.extract_embedding(fake_audio)
print(f"Embedding shape: {embedding.shape}")
print(f"Average value: {np.mean(embedding)}")

# Test Anti-spoof
antispoof = get_antispoof_model()
spoof_prob = antispoof.detect_spoof(np.random.randn(128))
print(f"Spoof probability: {spoof_prob}")
```

## Known Limitations

1. **Audio Quality**: Works best with clear audio at 16kHz
2. **Background Noise**: Can reduce accuracy
3. **Voice Variation**: Illness, stress, fatigue affect similarity
4. **Language**: Models trained mainly on English
5. **GPU Memory**: WavLM requires ~2GB GPU memory (or uses CPU)

## Checklist

- [ ] Database initializes on startup
- [ ] Users can register successfully
- [ ] Voice enrollment stores embedding
- [ ] Voice similarity computed correctly
- [ ] OTP generation works
- [ ] Email sending works (or falls back to console)
- [ ] JWT tokens generated correctly
- [ ] All API endpoints respond
- [ ] Frontend pages load without errors
- [ ] Microphone access requested and granted
- [ ] Audio recording works
- [ ] Authentication flow completes
- [ ] OTP verification flow works
- [ ] Anti-spoofing detection triggers
- [ ] Database persists data between runs

## Test Results Template

```
Date: __________
Tester: __________
Version: __________

## Results

| Test | Status | Notes |
|------|--------|-------|
| Database Init | PASS/FAIL | |
| User Registration | PASS/FAIL | |
| Voice Enrollment | PASS/FAIL | |
| Voice Verification | PASS/FAIL | |
| High Confidence Auth | PASS/FAIL | |
| Medium Confidence (OTP) | PASS/FAIL | |
| Low Confidence Denial | PASS/FAIL | |
| OTP Delivery | PASS/FAIL | |
| OTP Verification | PASS/FAIL | |
| Spoof Detection | PASS/FAIL | |
| API Documentation | PASS/FAIL | |
| Frontend Loading | PASS/FAIL | |

## Issues Found

1. ...
2. ...

## Recommendations

1. ...
2. ...
```

---

**Happy Testing! 🎉**
