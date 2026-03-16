"""
Voice enrollment module.
Handles user voice recording, processing, and embedding extraction.
"""

import os
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from utils.audio_processing import (
    preprocess_audio, 
    extract_mfcc,
    save_audio,
    load_audio,
    SAMPLE_RATE
)
from model_loader import get_speaker_encoder
from database import db

logger = logging.getLogger(__name__)

STORED_AUDIO_DIR = Path(__file__).parent / "stored_audio"
STORED_AUDIO_DIR.mkdir(exist_ok=True)


def enroll_user_voice(user_id: int, audio_file_path: str) -> dict:
    """
    Enroll user voice by extracting embeddings using ECAPA-TDNN.
    
    Args:
        user_id: User ID
        audio_file_path: Path to audio file
        
    Returns:
        Dictionary with enrollment status and embedding info
    """
    try:
        logger.info(f"[ENROLL] Starting voice enrollment for user {user_id}")
        logger.info(f"[ENROLL] Audio file: {audio_file_path}")
        
        # Load and preprocess audio
        logger.info("[ENROLL] Loading and preprocessing audio...")
        audio = preprocess_audio(audio_file_path)
        logger.info(f"[ENROLL] Audio preprocessed. Shape: {audio.shape}, dtype: {audio.dtype}, duration: {len(audio)/SAMPLE_RATE:.2f}s")
        logger.info(f"[ENROLL] Audio stats - min: {audio.min():.6f}, max: {audio.max():.6f}, mean: {audio.mean():.6f}, rms: {np.sqrt(np.mean(audio**2)):.6f}")
        
        # Check if audio is essentially empty
        if np.max(np.abs(audio)) < 1e-6:
            logger.warning("[ENROLL] ⚠ Audio signal has very small amplitude!")
            logger.warning("[ENROLL] Make sure the audio file contains actual voice recording")
        
        
        # Save preprocessed audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_audio_name = f"user_{user_id}_{timestamp}.wav"
        saved_audio_path = STORED_AUDIO_DIR / saved_audio_name
        
        save_audio(audio, str(saved_audio_path))
        logger.info(f"[ENROLL] Audio saved to {saved_audio_path}")
        
        # Extract embedding using ECAPA-TDNN
        logger.info("[ENROLL] Extracting embedding using ECAPA-TDNN model...")
        speaker_encoder = get_speaker_encoder()
        embedding = speaker_encoder.extract_embedding(audio, sample_rate=SAMPLE_RATE)
        logger.info(f"[ENROLL] Embedding extracted. Shape: {embedding.shape}, dtype: {embedding.dtype}")
        
        if embedding is None or len(embedding) == 0:
            logger.error(f"[ENROLL] Embedding extraction failed for user {user_id}")
            return {
                'success': False,
                'message': 'Failed to extract embedding from audio',
                'user_id': user_id
            }
        
        # Convert embedding to list for JSON serialization
        embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        logger.info(f"[ENROLL] Embedding converted to list. Dimension: {len(embedding_list)}")
        
        # Save embedding to database
        logger.info(f"[ENROLL] Saving embedding to database for user {user_id}...")
        db.save_voice_embedding(user_id, embedding_list, str(saved_audio_path))
        
        # Verify embedding was saved
        retrieved = db.get_voice_embedding(user_id)
        if retrieved and len(retrieved) > 0:
            logger.info(f"[ENROLL] ✓ Embedding verified in database. Dimension: {len(retrieved)}")
        else:
            logger.error(f"[ENROLL] ✗ Embedding verification failed!")
            return {
                'success': False,
                'message': 'Embedding saved but could not be verified in database',
                'user_id': user_id
            }
        
        logger.info(f"[ENROLL] ✓ Voice enrollment completed successfully for user {user_id}")
        
        return {
            'success': True,
            'message': 'Voice enrolled successfully',
            'user_id': user_id,
            'audio_path': str(saved_audio_path),
            'embedding_dim': len(embedding_list)
        }
        
    except Exception as e:
        logger.exception(f"[ENROLL] ✗ Voice enrollment failed for user {user_id}: {e}")
        return {
            'success': False,
            'message': f'Voice enrollment failed: {str(e)}',
            'user_id': user_id
        }


def update_user_voice(user_id: int, audio_file_path: str) -> dict:
    """
    Update user's voice embedding.
    
    Args:
        user_id: User ID
        audio_file_path: Path to new audio file
        
    Returns:
        Dictionary with update status
    """
    try:
        logger.info(f"[UPDATE] Updating voice for user {user_id}")
        
        # Load and preprocess audio
        audio = preprocess_audio(audio_file_path)
        
        # Save preprocessed audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_audio_name = f"user_{user_id}_updated_{timestamp}.wav"
        saved_audio_path = STORED_AUDIO_DIR / saved_audio_name
        
        save_audio(audio, str(saved_audio_path))
        
        # Extract embedding using ECAPA-TDNN
        speaker_encoder = get_speaker_encoder()
        embedding = speaker_encoder.extract_embedding(audio, sample_rate=SAMPLE_RATE)
        embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        
        # Update database
        db.save_voice_embedding(user_id, embedding_list, str(saved_audio_path))
        
        logger.info(f"[UPDATE] ✓ Voice updated for user {user_id}")
        
        return {
            'success': True,
            'message': 'Voice updated successfully',
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"[UPDATE] ✗ Voice update failed: {e}")
        return {
            'success': False,
            'message': f'Voice update failed: {str(e)}',
            'user_id': user_id
        }


def get_embeddings_for_user(user_id: int) -> np.ndarray or None:
    """Get stored embedding for user."""
    return db.get_voice_embedding(user_id)
