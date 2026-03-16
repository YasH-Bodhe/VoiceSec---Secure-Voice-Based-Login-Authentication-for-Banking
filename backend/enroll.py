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
from model_loader import get_wavlm_model
from database import db

logger = logging.getLogger(__name__)

STORED_AUDIO_DIR = Path(__file__).parent / "stored_audio"
STORED_AUDIO_DIR.mkdir(exist_ok=True)


def enroll_user_voice(user_id: int, audio_file_path: str) -> dict:
    """
    Enroll user voice by extracting embeddings.
    
    Args:
        user_id: User ID
        audio_file_path: Path to audio file
        
    Returns:
        Dictionary with enrollment status and embedding info
    """
    try:
        logger.info(f"Starting voice enrollment for user {user_id} from file: {audio_file_path}")
        
        # Load and preprocess audio
        audio = preprocess_audio(audio_file_path)
        logger.info(f"Audio preprocessed. Shape: {audio.shape}, dtype: {audio.dtype}")
        
        # Save preprocessed audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_audio_name = f"user_{user_id}_{timestamp}.wav"
        saved_audio_path = STORED_AUDIO_DIR / saved_audio_name
        
        save_audio(audio, str(saved_audio_path))
        logger.info(f"Audio saved to {saved_audio_path}")
        
        # Extract embedding using WavLM
        wavlm_model = get_wavlm_model()
        logger.info(f"Extracting embedding using WavLM model")
        embedding = wavlm_model.extract_embedding(audio, sample_rate=SAMPLE_RATE)
        logger.info(f"Embedding extracted. Shape: {embedding.shape if hasattr(embedding, 'shape') else len(embedding)}, Type: {type(embedding)}")
        
        if embedding is None:
            logger.error(f"Embedding is None for user {user_id}")
            return {
                'success': False,
                'message': 'Failed to extract embedding from audio',
                'user_id': user_id
            }
        
        # Convert embedding to list for JSON serialization
        embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
        logger.info(f"Embedding converted to list. Length: {len(embedding_list)}")
        
        # Save embedding to database
        db.save_voice_embedding(user_id, embedding_list, str(saved_audio_path))
        logger.info(f"Embedding saved to database for user {user_id}")
        
        # Verify it was saved
        retrieved = db.get_voice_embedding(user_id)
        if retrieved:
            logger.info(f"✓ Embedding verified in database. Length: {len(retrieved)}")
        else:
            logger.error(f"✗ Embedding could not be retrieved from database!")
            return {
                'success': False,
                'message': 'Embedding saved but could not be verified in database',
                'user_id': user_id
            }
        
        logger.info(f"Voice enrollment completed successfully for user {user_id}")
        
        return {
            'success': True,
            'message': 'Voice enrolled successfully',
            'user_id': user_id,
            'audio_path': str(saved_audio_path),
            'embedding_dim': len(embedding_list)
        }
        
    except Exception as e:
        logger.exception(f"Voice enrollment failed for user {user_id}: {e}")
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
        logger.info(f"Updating voice for user {user_id}")
        
        # Load and preprocess audio
        audio = preprocess_audio(audio_file_path)
        
        # Save preprocessed audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_audio_name = f"user_{user_id}_updated_{timestamp}.wav"
        saved_audio_path = STORED_AUDIO_DIR / saved_audio_name
        
        save_audio(audio, str(saved_audio_path))
        
        # Extract embedding
        wavlm_model = get_wavlm_model()
        embedding = wavlm_model.extract_embedding(audio, sample_rate=SAMPLE_RATE)
        embedding_list = embedding.tolist()
        
        # Update database
        db.save_voice_embedding(user_id, embedding_list, str(saved_audio_path))
        
        logger.info(f"Voice updated for user {user_id}")
        
        return {
            'success': True,
            'message': 'Voice updated successfully',
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"Voice update failed: {e}")
        return {
            'success': False,
            'message': f'Voice update failed: {str(e)}',
            'user_id': user_id
        }


def get_embeddings_for_user(user_id: int) -> np.ndarray or None:
    """Get stored embedding for user."""
    return db.get_voice_embedding(user_id)
