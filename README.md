# Voice-Based Banking Authentication System

A complete production-ready voice biometrics authentication system with anti-spoofing protection and OTP fallback authentication.

## 🎯 Features

- **Voice Biometrics Authentication**: Login using speaker recognition instead of passwords
- **Anti-Spoofing Protection**: Detects replay attacks and synthetic voice attacks
- **Speaker Embedding**: Uses pretrained WavLM model for robust speaker embeddings
- **Cosine Similarity**: Manual implementation of cosine similarity for voice comparison
- **OTP Fallback**: One-Time Password verification when voice similarity is medium
- **Email Integration**: OTP sent via email (SMTP)
- **JWT Authentication**: Secure token-based session management
- **SQLite Database**: Persistent storage of users and embeddings
- **RESTful API**: FastAPI backend with complete REST endpoints
- **Web Frontend**: HTML/CSS/JavaScript interface with Web Audio API

## 📋 System Architecture

```
Browser Frontend (HTML/CSS/JS)
    ↓
FastAPI Backend (main.py)
    ↓
Voice Processing Pipeline
    ├─ Audio Loading & Preprocessing
    ├─ MFCC Feature Extraction
    └─ WavLM Speaker Embedding
    ↓
Speaker Verification (Cosine Similarity)
    ├─ Anti-Spoofing Detection
    ├─ Similarity Scoring
    └─ Decision Making
    ↓
Database (SQLite)
    ├─ User Management
    ├─ Voice Embeddings
    ├─ OTP Storage
    └─ Login Attempts
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- pip package manager
- Git
- Text editor/IDE

### Installation Steps

#### 1. Clone/Download Project

```bash
cd voice-auth-system
```

#### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings:
# - Set SECRET_KEY to a random string
# - Configure SMTP settings for OTP emails (optional)
```

**For Gmail OTP (Optional):**
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Add to .env:
```
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

#### 5. Initialize Database

The database will be created automatically on first run.

#### 6. Run the Application

```bash
# Navigate to backend directory
cd backend

# Start the FastAPI server
uvicorn main:app --reload

# Server will be available at: http://localhost:8000
```

#### 7. Access Frontend

Open your browser and navigate to:
```
http://localhost:8000/static/index.html
```

## 📁 Project Structure

```
voice-auth-system/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── database.py             # SQLite database handler
│   ├── model_loader.py         # WavLM and anti-spoof models
│   ├── enroll.py               # Voice enrollment module
│   ├── verify.py               # Voice verification module
│   ├── antispoof.py            # Anti-spoofing detection
│   ├── otp_service.py          # OTP generation and verification
│   │
│   ├── utils/
│   │   ├── audio_processing.py # Audio loading and MFCC extraction
│   │   └── similarity.py        # Cosine similarity computation
│   │
│   └── stored_audio/           # Voice samples storage
│
├── frontend/
│   ├── index.html              # Home page
│   ├── register.html           # Registration page
│   ├── login.html              # Login page
│   │
│   ├── css/
│   │   └── style.css           # Stylesheets
│   │
│   └── js/
│       └── script.js           # Frontend utilities
│
├── database/
│   └── database.db             # SQLite database (auto-created)
│
├── requirements.txt            # Python dependencies
├── .env.example                # Environment configuration template
└── README.md                   # This file
```

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Description | Body |
|--------|----------|-------------|------|
| POST | `/register` | Register new user | name, email, password |
| POST | `/login` | Authenticate with email/password | email, password |
| POST | `/enroll_voice` | Enroll voice sample | user_id, audio file |
| POST | `/verify_voice` | Verify voice during login | user_id, audio file |
| POST | `/send_otp` | Generate and send OTP | user_id |
| POST | `/verify_otp` | Verify OTP code | user_id, otp_code |

### Protected Routes

| Method | Endpoint | Description | Headers |
|--------|----------|-------------|---------|
| GET | `/dashboard` | User dashboard | token |
| POST | `/update_voice` | Update voice embedding | token, user_id, audio |

### Testing

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API info |
| POST | `/test_spoof_detection` | Test anti-spoofing |

## 🎤 How It Works

### Registration Flow

1. **User Registration**
   - Enter name, email, password
   - Password is hashed using bcrypt
   - User account created in database

2. **Voice Enrollment**
   - Record voice sample (3-5 seconds)
   - Audio preprocessed and normalized
   - WavLM extracts 512-dimensional speaker embedding
   - Embedding stored in database

### Login Flow

1. **Password Verification**
   - User enters email and password
   - System verifies password hash

2. **Voice Verification**
   - User records voice sample
   - System extracts embedding using WavLM
   - Computes cosine similarity between login and stored embedding

3. **Anti-Spoofing Check**
   - MFCC features extracted from audio
   - Simple neural network detects spoof probability
   - If spoof detected: authentication denied
   - If clean: proceed with comparison

4. **Decision Making**
   - **similarity >= 0.80**: Direct login success
   - **0.60 <= similarity < 0.80**: OTP verification required
   - **similarity < 0.60**: Authentication failed

5. **OTP Verification** (if needed)
   - 6-digit OTP generated and sent to email
   - User enters OTP (valid for 5 minutes)
   - If correct: authentication successful

## 🔐 Security Features

### Password Security
- Bcrypt hashing with salt
- Minimum 6 characters required
- Never stored in plain text

### Voice Authentication
- Speaker embeddings extracted using WavLM
- Cosine similarity threshold-based comparison
- Anti-spoofing detection prevents replay attacks
- MFCC feature analysis detects synthetic voices

### OTP Security
- 6-digit random codes
- 5-minute expiration
- Email delivery via SMTP
- One-time use enforcement

### API Security
- JWT token-based authentication
- CORS enabled for development
- Input validation on all endpoints
- Error handling prevents information leakage

## 🧪 Testing the System

### Test User Registration

```bash
curl -X POST "http://localhost:8000/register" \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "password=password123"
```

### Test Health Check

```bash
curl http://localhost:8000/health
```

### Test Spoof Detection

```bash
curl -X POST "http://localhost:8000/test_spoof_detection" \
  -F "audio=@voice_sample.wav"
```

## 📊 Decision Rules

### Voice Similarity Threshold
- **90%+ confidence**: Immediate authentication
- **70-90% confidence**: Suspicious - requires OTP
- **Below 70%**: Likely fake/imposter - denied

### Anti-Spoofing Rules
- **Spoof probability > 0.5**: Detected attack - denied
- **Spoof probability <= 0.5**: Clean voice - proceed

## 🎓 Cosine Similarity Implementation

The system implements cosine similarity manually:

```python
similarity = (A · B) / (||A|| × ||B||)
```

Where:
- A, B are speaker embedding vectors
- · is dot product
- || || is L2 norm

This measures the angle between embeddings, giving scores 0-1.

## 📝 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE,
    password_hash TEXT,
    voice_embedding TEXT (JSON),
    voice_sample_path TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### OTP Table
```sql
CREATE TABLE otp (
    otp_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    otp_code TEXT,
    expiry_time INTEGER,
    verified INTEGER,
    created_at TIMESTAMP
)
```

### Login Attempts Table
```sql
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    similarity_score REAL,
    spoof_probability REAL,
    status TEXT,
    created_at TIMESTAMP
)
```

## 🔧 Configuration

### Environment Variables (.env)

```ini
# Security
SECRET_KEY=your-secret-key-here

# Email (OTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# Database
DATABASE_PATH=database/database.db

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### Tuning Parameters

Edit backend files for fine-tuning:

**Main Thresholds** (verify.py):
```python
0.80  # High confidence threshold
0.60  # Medium confidence threshold
```

**Anti-Spoofing** (antispoof.py):
```python
0.5   # Spoof detection probability threshold
```

**OTP** (otp_service.py):
```python
300   # OTP expiry in seconds
```

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Change port in main.py startup or use:
uvicorn main:app --reload --port 8001
```

### Microphone Not Working
- Check browser permissions
- Use HTTPS in production (getUserMedia requires secure context)
- Test with `navigator.mediaDevices.enumerateDevices()`

### Models Not Loading
- First run downloads models (~500MB+)
- Requires internet connection
- Check disk space

### Email Not Sending
- Use `.env.example` credentials
- Gmail requires App Password, not regular password
- Check SMTP credentials and ports
- System falls back to console logging on error

### Database Issues
- Delete `database/database.db` to reset
- Check file permissions on database folder
- Ensure SQLite is available

## 📚 Technology Stack

### Backend
- **FastAPI 0.104.1**: Modern web framework
- **PyTorch 2.1.1**: Deep learning
- **Transformers 4.35.2**: HuggingFace models
- **Librosa 0.10.0**: Audio processing
- **Torchaudio 2.1.1**: Audio handling
- **NumPy 1.26.2**: Numerical computing
- **scikit-learn 1.3.2**: ML utilities
- **bcrypt 4.1.1**: Password hashing
- **python-jose 3.3.0**: JWT handling
- **SQLAlchemy 2.0.23**: ORM (optional)

### Frontend
- **HTML5**: Markup
- **CSS3**: Styling (responsive design)
- **JavaScript (ES6+)**: Interactivity
- **Web Audio API**: Voice recording

### Database
- **SQLite 3**: Lightweight SQL database
- **Optional**: PostgreSQL (with SQLAlchemy)

## 🤖 AI Models Used

### WavLM Speaker Embedding Model
- **Model**: `microsoft/wavlm-base-plus-sv`
- **Type**: Transformer-based speaker verification model
- **Output**: 512-dimensional speaker embeddings
- **Usage**: Extract unique voice signature

### Anti-Spoofing Model
- **Architecture**: Simple MLP classifier
- **Input**: MFCC features
- **Output**: Spoof probability (0-1)
- **Purpose**: Detect replay and synthetic voices

## 📖 References

- WavLM Paper: https://arxiv.org/abs/2110.13900
- MFCC Features: https://en.wikipedia.org/wiki/Mel-frequency_cepstrum
- Cosine Similarity: https://en.wikipedia.org/wiki/Cosine_similarity
- Speaker Recognition: https://en.wikipedia.org/wiki/Speaker_recognition

## ⚠️ Important Notes

### Development vs Production
- This is a research/educational project
- **NOT recommended for production use without:**
  - Security audit
  - Rate limiting
  - Logging and monitoring
  - Input validation improvements
  - HTTPS/TLS enforcement
  - Database encryption
  - Backup systems

### Privacy & Data Protection
- Voice samples stored locally
- No external third-party services
- User data never shared
- GDPR compliant (local processing)

### Accuracy
- Depends on audio quality
- Voice changes over time (fatigue, illness)
- Accents and background noise affect accuracy
- Test with multiple voice samples

## 🤝 Contributing

Found a bug? Have suggestions? Feel free to:
1. Report issues
2. Suggest improvements
3. Submit enhancements

## 📄 License

This project is provided as-is for educational purposes.

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Review API documentation at `/docs`
3. Check console for detailed error messages
4. Ensure all dependencies are installed

## 🎉 Summary

You now have a complete, working voice authentication system with:
- ✅ User registration and voice enrollment
- ✅ Voice-based login with similarity matching
- ✅ Anti-spoofing protection
- ✅ OTP fallback authentication
- ✅ Email integration
- ✅ Complete REST API
- ✅ Web frontend
- ✅ Database persistence

Enjoy using the Voice Banking Authentication System! 🎤🔐

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Development/Research
