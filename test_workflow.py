#!/usr/bin/env python
"""
Complete test workflow for voice authentication system
"""
import requests
import tempfile
import wave
import numpy as np
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000"

def test_complete_workflow():
    # 1. Register user
    print("=" * 50)
    print("STEP 1: REGISTER USER")
    print("=" * 50)

    timestamp = str(int(time.time()))
    email = f"testuser{timestamp}@example.com"

    register_data = {
        'name': 'Test User',
        'email': email,
        'password': 'test123456'
    }

    r = requests.post(f"{BASE_URL}/register", data=register_data)
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2)}")

    if r.status_code != 200:
        print("❌ Registration failed!")
        return False

    user_id = r.json()['user_id']
    print(f"✅ User registered with ID: {user_id}")

    # 2. Create test audio file
    print("\n" + "=" * 50)
    print("STEP 2: CREATE TEST AUDIO")
    print("=" * 50)

    wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    wav_path = wav_file.name
    wav_file.close()

    # Create 16kHz, 3-second audio with 220Hz sine wave
    sr = 16000
    duration = 3
    t = np.linspace(0, duration, int(sr * duration), False)
    sine_wave = np.sin(2 * np.pi * 220 * t)
    audio_data = (sine_wave * 32767).astype(np.int16)

    with wave.open(wav_path, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(audio_data.tobytes())

    print(f"✅ Audio file created: {wav_path}")

    # 3. Enroll voice
    print("\n" + "=" * 50)
    print("STEP 3: ENROLL VOICE")
    print("=" * 50)

    with open(wav_path, 'rb') as audio_file:
        files = {'audio': audio_file}
        enroll_data = {'user_id': user_id}
        r = requests.post(f"{BASE_URL}/enroll_voice", data=enroll_data, files=files)

    print(f"Status: {r.status_code}")
    response_json = r.json()
    print(f"Response: {json.dumps(response_json, indent=2)}")

    if r.status_code != 200 or not response_json.get('success'):
        print("❌ Enrollment failed!")
        print("Full response:", response_json)
        os.remove(wav_path)
        return False
    else:
        print(f"✅ Voice enrolled successfully!")
        print(f"   Embedding dimension: {response_json.get('embedding_dim')}")

    # 4. Verify voice
    print("\n" + "=" * 50)
    print("STEP 4: VERIFY VOICE")
    print("=" * 50)

    # First do password login
    print("\n4a. Password Login...")
    login_data = {
        'email': email,
        'password': 'test123456'
    }
    r = requests.post(f"{BASE_URL}/login", data=login_data)
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2)}")

    if r.status_code != 200:
        print("❌ Password login failed!")
        os.remove(wav_path)
        return False

    print(f"✅ Password verified")

    # Now verify voice
    print("\n4b. Voice Verification...")
    with open(wav_path, 'rb') as audio_file:
        files = {'audio': audio_file}
        verify_data = {'user_id': user_id}
        r = requests.post(f"{BASE_URL}/verify_voice", data=verify_data, files=files)

    print(f"Status: {r.status_code}")
    response_json = r.json()
    print(f"Response: {json.dumps(response_json, indent=2)}")

    if r.status_code == 200:
        print(f"✅ Verification successful!")
        print(f"   Similarity Score: {response_json.get('similarity_score')}")
        print(f"   Authenticated: {response_json.get('authenticated')}")
    else:
        print(f"❌ Verification failed!")
        print("   Full response:", response_json)

    # Cleanup
    os.remove(wav_path)
    print("\n" + "=" * 50)
    print("✅ TEST COMPLETE - NO ISSUES!")
    print("=" * 50)
    return True

if __name__ == '__main__':
    success = test_complete_workflow()
    exit(0 if success else 1)
