#!/usr/bin/env python
"""Quick test to verify imports and database"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

print("=" * 50)
print("TESTING IMPORTS AND DATABASE")
print("=" * 50)

try:
    from database import db
    print("✓ Database imported successfully")
    
    # Test database connection
    user = db.get_user_by_id(1)
    print(f"✓ Database query test: {('user found' if user else 'no users yet')}")
    
    from main import app
    print("✓ FastAPI app imported successfully")
    
    print("\n✓ ALL IMPORTS SUCCESSFUL")
    print("=" * 50)
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
