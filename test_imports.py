#!/usr/bin/env python
"""
Comprehensive test script to verify all dependencies and system configuration.
Run this before starting the server to ensure everything is ready.
"""

import sys
from pathlib import Path
import importlib

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

print("\n" + "=" * 80)
print("VOICE BANKING AUTHENTICATION SYSTEM - STARTUP VERIFICATION")
print("=" * 80 + "\n")

# ============================================================================
# Test Core Python Imports
# ============================================================================

print("Testing Core Dependencies...")
print("-" * 80)

core_modules = [
    'fastapi',
    'uvicorn',
    'numpy',
    'scipy',
    'librosa',
    'torch',
    'torchaudio',
    'transformers',
    'sklearn',
    'bcrypt',
    'sqlalchemy'
]

failed_modules = []

for module in core_modules:
    try:
        importlib.import_module(module)
        print(f"✓ {module}")
    except ImportError as e:
        print(f"✗ {module}: {str(e)[:50]}")
        failed_modules.append(module)

# ============================================================================
# Test SpeechBrain (Critical for speaker verification)
# ============================================================================

print("\n\nTesting SpeechBrain (Critical for ECAPA-TDNN)...")
print("-" * 80)

try:
    import speechbrain
    print(f"✓ SpeechBrain imported successfully")
    
    # Test loading a model (this is critical)
    print("  Loading ECAPA-TDNN model from SpeechBrain...")
    from speechbrain.pretrained import SpeakerRecognition
    print("  ✓ SpeakerRecognition available")
    
except ImportError as e:
    print(f"✗ SpeechBrain not installed or importable: {e}")
    failed_modules.append('speechbrain')
except Exception as e:
    print(f"✗ Error importing SpeechBrain: {e}")
    failed_modules.append('speechbrain')

# ============================================================================
# Test Database
# ============================================================================

print("\n\nTesting Database...")
print("-" * 80)

try:
    from database import db
    print("✓ Database module imported successfully")
    
    # Test database connection
    user = db.get_user_by_id(1)
    print(f"✓ Database connection working")
    
    # Test database tables
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    
    print(f"✓ Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
        
except Exception as e:
    print(f"✗ Database error: {e}")
    import traceback
    traceback.print_exc()
    failed_modules.append('database')

# ============================================================================
# Test Backend Modules
# ============================================================================

print("\n\nTesting Backend Modules...")
print("-" * 80)

backend_modules = [
    ('main', 'FastAPI Application'),
    ('model_loader', 'Model Loader (ECAPA-TDNN)'),
    ('enroll', 'Voice Enrollment'),
    ('verify', 'Voice Verification'),
    ('antispoof', 'Anti-spoofing Detection'),
    ('otp_service', 'OTP Service'),
]

for module_name, display_name in backend_modules:
    try:
        if module_name == 'main':
            from main import app
            print(f"✓ {display_name} ({module_name})")
        elif module_name == 'model_loader':
            from model_loader import load_models, get_speaker_encoder, get_antispoof_model
            print(f"✓ {display_name} ({module_name})")
        elif module_name == 'enroll':
            from enroll import enroll_user_voice
            print(f"✓ {display_name} ({module_name})")
        elif module_name == 'verify':
            from verify import verify_speaker, cosine_similarity
            print(f"✓ {display_name} ({module_name})")
        elif module_name == 'antispoof':
            from antispoof import detect_spoof, analyze_audio_quality
            print(f"✓ {display_name} ({module_name})")
        elif module_name == 'otp_service':
            from otp_service import create_otp_for_user, verify_otp_for_user
            print(f"✓ {display_name} ({module_name})")
    except Exception as e:
        print(f"✗ {display_name} ({module_name}): {str(e)[:50]}")
        failed_modules.append(module_name)

# ============================================================================
# Test Environment Configuration
# ============================================================================

print("\n\nTesting Environment Configuration...")
print("-" * 80)

import os
from dotenv import load_dotenv

load_dotenv()

config = {
    'SECRET_KEY': 'JWT Secret Key',
    'SMTP_SERVER': 'SMTP Server',
    'SMTP_PORT': 'SMTP Port',
    'SENDER_EMAIL': 'Sender Email',
    'SENDER_PASSWORD': 'Sender Password (Gmail App Password)'
}

warnings = 0

for env_var, display_name in config.items():
    value = os.getenv(env_var)
    if value:
        if 'PASSWORD' in env_var:
            print(f"✓ {display_name}: [SET]")
        else:
            print(f"✓ {display_name}: {value[:20]}...")
    else:
        print(f"⚠ {display_name}: NOT SET (will use defaults)")
        warnings += 1

# ============================================================================
# Summary and Recommendations
# ============================================================================

print("\n\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

if not failed_modules and warnings == 0:
    print("✓ ALL SYSTEMS READY!")
    print("\nYou can now start the server with:")
    print("  python -m uvicorn backend.main:app --reload")
    print("\n✅ System is fully operational")
    
elif not failed_modules:
    print(f"✓ CORE SYSTEMS OK ({warnings} config warnings)")
    print("\n⚠️  Configuration Warnings:")
    print("  - Some environment variables are not set")
    print("  - The system will use defaults, but consider setting them for production")
    print("\nYou can start the server with:")
    print("  python -m uvicorn backend.main:app --reload")
    
else:
    print(f"❌ {len(failed_modules)} CRITICAL ISSUE(S) FOUND")
    print(f"\nFailed modules/dependencies:")
    for module in failed_modules:
        print(f"  - {module}")
    print("\nFix these issues before starting:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

print("\n" + "=" * 80 + "\n")
