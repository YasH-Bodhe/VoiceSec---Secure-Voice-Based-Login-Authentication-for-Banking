"""
Main FastAPI application for voice-based banking authentication.
Provides REST API endpoints for registration, enrollment, and login.
"""

import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
import tempfile
from jose import jwt
from jose.exceptions import JWTError
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import os
import time

# Import modules
from database import db
from enroll import enroll_user_voice
from verify import verify_speaker
from antispoof import detect_spoof, analyze_audio_quality
from otp_service import create_otp_for_user, verify_otp_for_user
from utils.audio_processing import load_audio, SAMPLE_RATE
from model_loader import load_models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Voice Banking Authentication System",
    description="Authentication system using voice biometrics with anti-spoofing",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add cache-busting middleware for HTML files
@app.middleware("http")
async def cache_busting_middleware(request, call_next):
    response = await call_next(request)
    
    # Disable caching for HTML files
    if request.url.path.endswith(('.html', '.htm')):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response

# JWT Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Mount frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ==================== Startup & Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup.
    Load all ML models into memory.
    """
    logger.info("=" * 80)
    logger.info("STARTING VOICE BANKING AUTHENTICATION SYSTEM")
    logger.info("=" * 80)
    
    try:
        logger.info("Loading machine learning models...")
        load_models()
        logger.info("✓ All models loaded successfully")
    except Exception as e:
        logger.error(f"✗ Failed to load models on startup: {e}")
        logger.error("The application may not function properly without models")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("=" * 80)
    logger.info("SHUTTING DOWN VOICE BANKING AUTHENTICATION SYSTEM")
    logger.info("=" * 80)


# ==================== Helper Functions ====================

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: int, email: str) -> str:
    """Create JWT access token."""
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict or None:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def cleanup_temp_file(file_path: str, max_retries: int = 3) -> bool:
    """Clean up temp file with retry logic for Windows file locking."""
    for attempt in range(max_retries):
        try:
            if os.path.exists(file_path):
                time.sleep(0.1)  # Small delay for file handle release
                os.remove(file_path)
            return True
        except (OSError, PermissionError) as e:
            if attempt < max_retries - 1:
                time.sleep(0.2)
            else:
                logger.warning(f"Could not delete temp file {file_path}: {e}")
                return False
    return False


# ==================== Health Check ====================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "online",
        "message": "Voice Banking Authentication System v2.0",
        "version": "2.0.0",
        "features": [
            "ECAPA-TDNN speaker verification",
            "Anti-spoofing detection",
            "OTP-based fallback authentication",
            "Cosine similarity matching"
        ],
        "endpoints": "/docs for API documentation"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


# ==================== Registration & Enrollment Endpoints ====================

@app.post("/register")
async def register(name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    """
    Register a new user with name, email, and password.
    
    - **name**: User's full name
    - **email**: User's email address
    - **password**: User's password (will be hashed)
    """
    try:
        # Check if user exists
        existing_user = db.get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate input
        if not name or not email or not password:
            raise HTTPException(status_code=400, detail="All fields are required")
        
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user_id = db.create_user(name, email, password_hash)
        
        logger.info(f"User registered: {email} (ID: {user_id})")
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user_id,
            "email": email,
            "next_step": "upload voice sample"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/enroll_voice")
async def enroll_voice(user_id: int = Form(...), audio: UploadFile = File(...)):
    """
    Enroll user's voice by uploading audio sample.
    
    - **user_id**: User ID (from registration)
    - **audio**: Audio file (WAV, MP3)
    """
    try:
        logger.info(f"Enrollment request for user_id={user_id}, filename={audio.filename}")
        
        # Verify user exists
        user = db.get_user_by_id(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User {user_id} found: {user['email']}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_file_path = tmp_file.name
            logger.info(f"Temp audio file: {tmp_file_path}, size: {len(content)} bytes")
            # Explicitly close before passing to processing
            tmp_file.close()
        
        try:
            # Enroll voice
            logger.info(f"Starting voice enrollment process for user {user_id}")
            result = enroll_user_voice(user_id, tmp_file_path)
            logger.info(f"Enrollment result: {result}")
            
            # Verify enrollment was actually saved
            if result.get('success'):
                # Double-check that embedding is in database
                saved_embedding = db.get_voice_embedding(user_id)
                if saved_embedding:
                    logger.info(f"✓ Confirmed: Embedding exists in database for user {user_id}")
                    return {
                        "success": True,
                        "message": "Voice enrolled successfully!",
                        "user_id": user_id,
                        "embedding_dim": len(saved_embedding)
                    }
                else:
                    logger.error(f"✗ CRITICAL: Embedding save failed for user {user_id}")
                    raise HTTPException(
                        status_code=500,
                        detail="Voice enrollment failed: Could not save to database"
                    )
            else:
                logger.error(f"Enrollment failed: {result.get('message')}")
                raise HTTPException(
                    status_code=400,
                    detail=result.get('message', 'Voice enrollment failed')
                )
            
        finally:
            # Clean up temp file with retry logic
            cleanup_temp_file(tmp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice enrollment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Enrollment error: {str(e)}")


# ==================== Login & Verification Endpoints ====================

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    """
    Authenticate user with email and password.
    
    - **email**: User's email
    - **password**: User's password
    """
    try:
        # Get user by email
        user = db.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        logger.info(f"User logged in with password: {email}")
        
        return {
            "success": True,
            "message": "Password verified. Please verify voice.",
            "user_id": user['id'],
            "email": email,
            "next_step": "voice_verification"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify_voice")
async def verify_voice(user_id: int = Form(...), audio: UploadFile = File(...)):
    """
    Verify user's voice during login.
    
    - **user_id**: User ID
    - **audio**: Audio sample for verification
    """
    try:
        # Verify user exists
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        stored_embedding = db.get_voice_embedding(user_id)
        if stored_embedding is None:
            raise HTTPException(
                status_code=400,
                detail="No voice enrolled. Please complete voice enrollment before logging in."
            )


        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_file_path = tmp_file.name
            # Explicitly close before passing to processing
            tmp_file.close()
        
        try:
            # Verify voice
            result = verify_speaker(user_id, tmp_file_path)
            
            if result['success']:
                if result['authenticated']:
                    # Create token for direct authentication
                    token = create_access_token(user_id, user['email'])
                    return {
                        "success": True,
                        "message": "Voice authentication successful!",
                        "user_id": user_id,
                        "authenticated": True,
                        "token": token,
                        "similarity_score": result.get('similarity_score'),
                        "requires_otp": False
                    }
                elif result.get('requires_otp'):
                    # OTP required
                    otp_result = create_otp_for_user(user_id)
                    return {
                        "success": True,
                        "message": result['message'],
                        "user_id": user_id,
                        "authenticated": False,
                        "requires_otp": True,
                        "similarity_score": result.get('similarity_score'),
                        "otp_sent": otp_result['success']
                    }
                else:
                    # Authentication failed
                    return {
                        "success": False,
                        "message": result['message'],
                        "user_id": user_id,
                        "authenticated": False,
                        "similarity_score": result.get('similarity_score'),
                        "reason": result.get('reason')
                    }
            else:
                    return JSONResponse(status_code=400, content={
                        "success": False,
                        "authenticated": False,
                        "message": result['message'],
                        "reason": result.get('reason')
                    })
            
        finally:
            cleanup_temp_file(tmp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== OTP Endpoints ====================

@app.post("/send_otp")
async def send_otp(user_id: int = Form(...)):
    """
    Send OTP to user's email.
    
    - **user_id**: User ID
    """
    try:
        result = create_otp_for_user(user_id)
        
        if result['success']:
            return {
                "success": True,
                "message": result['message'],
                "user_id": user_id,
                "expiry_seconds": result['expiry_seconds']
            }
        else:
            raise HTTPException(status_code=400, detail=result['message'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send OTP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify_otp")
async def verify_otp(user_id: int = Form(...), otp_code: str = Form(...)):
    """
    Verify OTP for user.
    
    - **user_id**: User ID
    - **otp_code**: OTP code to verify
    """
    try:
        result = verify_otp_for_user(user_id, otp_code)
        
        if result['authenticated']:
            user = db.get_user_by_id(user_id)
            token = create_access_token(user_id, user['email'])
            
            return {
                "success": True,
                "message": "OTP verified. Login successful!",
                "user_id": user_id,
                "authenticated": True,
                "token": token
            }
        else:
            raise HTTPException(status_code=400, detail=result['message'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify OTP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Dashboard & Protected Routes ====================

@app.get("/dashboard")
async def dashboard(token: str = None):
    """
    Get user dashboard (requires authentication).
    
    - **token**: JWT access token
    """
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get('user_id')
    user = db.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "user_id": user['id'],
        "name": user['name'],
        "email": user['email'],
        "created_at": user['created_at']
    }


@app.post("/update_voice")
async def update_voice(user_id: int = Form(...), audio: UploadFile = File(...), token: str = Form(...)):
    """Update user's voice embedding."""
    
    # Verify token
    payload = verify_token(token)
    if not payload or payload['user_id'] != user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from enroll import update_user_voice
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_file_path = tmp_file.name
            tmp_file.close()
        
        try:
            result = update_user_voice(user_id, tmp_file_path)
            return result
        finally:
            cleanup_temp_file(tmp_file_path)
        
    except Exception as e:
        logger.error(f"Voice update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Testing/Debug Endpoints ====================

@app.post("/test_spoof_detection")
async def test_spoof(audio: UploadFile = File(...)):
    """Test anti-spoofing detection (for debugging)."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_file_path = tmp_file.name
            tmp_file.close()
        
        try:
            audio_data = load_audio(tmp_file_path)
            result = detect_spoof(audio_data)
            quality = analyze_audio_quality(audio_data)
            
            return {
                "spoof_detection": result,
                "audio_quality": quality
            }
        finally:
            cleanup_temp_file(tmp_file_path)
        
    except Exception as e:
        logger.error(f"Spoof test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user_status/{user_id}")
async def user_status(user_id: int):
    """
    Get user status including enrollment status (for debugging).
    
    - **user_id**: User ID
    """
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        embedding = db.get_voice_embedding(user_id)
        has_enrollment = embedding is not None
        embedding_dim = len(embedding) if embedding else 0
        
        return {
            "success": True,
            "user_id": user_id,
            "email": user['email'],
            "name": user['name'],
            "has_voice_enrollment": has_enrollment,
            "embedding_dimension": embedding_dim,
            "created_at": user['created_at'],
            "updated_at": user['updated_at']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Verification Analysis & Visualization ====================

@app.post("/analyze_verification")
async def analyze_verification(user_id: int = Form(...), audio: UploadFile = File(...)):
    """
    Analyze voice verification with detailed metrics for visualization.
    Used for debugging and UI visualization of similarity scores.
    
    - **user_id**: User ID
    - **audio**: Audio sample for verification
    """
    try:
        logger.info(f"Analyze verification for user_id={user_id}")
        
        # Verify user exists
        user = db.get_user_by_id(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        stored_embedding = db.get_voice_embedding(user_id)
        if stored_embedding is None:
            logger.warning(f"No voice embedding found for user {user_id}")
            return {
                "success": False,
                "error": f"No voice enrollment found for user {user_id}. Please complete voice enrollment first.",
                "similarity_score": None,
                "threshold_high": 0.65,
                "threshold_low": 0.45,
                "embedding_dim": 512
            }

        logger.info(f"Found stored embedding with dim {len(stored_embedding)} for user {user_id}")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file.flush()
            tmp_file_path = tmp_file.name
            logger.info(f"Temp audio received: {len(content)} bytes")
            tmp_file.close()
        
        try:
            # Get verification result
            result = verify_speaker(user_id, tmp_file_path)
            logger.info(f"Verification result for user {user_id}: similarity={result.get('similarity_score')}, authenticated={result.get('authenticated')}")
            
            # Return full analysis data
            return {
                "success": result.get('success', True),
                "similarity_score": result.get('similarity_score'),
                "threshold_high": 0.65,
                "threshold_low": 0.45,
                "authenticated": result.get('authenticated', False),
                "requires_otp": result.get('requires_otp', False),
                "message": result.get('message'),
                "reason": result.get('reason'),
                "embedding_dim": len(stored_embedding) if stored_embedding else 512,
                "embedding_visualization": [
                    {"id": i, "value": stored_embedding[i] if i < len(stored_embedding) else 0}
                    for i in range(min(50, len(stored_embedding)))  # Show first 50 dims
                ]
            }
            
        finally:
            cleanup_temp_file(tmp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


# ==================== Startup & Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Load models on startup."""
    logger.info("Starting up...")
    try:
        load_models()
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        logger.warning("Continuing without models - some features may not work")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
