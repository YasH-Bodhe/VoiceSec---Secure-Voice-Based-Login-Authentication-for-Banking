"""
Voice verification module.
Handles speaker verification by comparing voice embeddings with cosine similarity.
"""

import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
from utils.audio_processing import preprocess_audio, SAMPLE_RATE
from model_loader import get_speaker_encoder
from database import db

logger = logging.getLogger(__name__)

# Verification thresholds (optimized for ECAPA-TDNN)
SIMILARITY_THRESHOLD_HIGH = 0.85   # >= this → authenticated directly
SIMILARITY_THRESHOLD_LOW  = 0.70   # >= this and < HIGH → OTP fallback
# < LOW → rejected outright


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two embedding vectors.
    
    Uses the mathematically correct formula:
    cosine_similarity = dot(A,B) / (||A|| * ||B||)
    
    Args:
        a: First embedding vector (np.ndarray)
        b: Second embedding vector (np.ndarray)

    Returns:
        Cosine similarity score in [0, 1]; higher means more similar
    """
    try:
        # Ensure inputs are numpy arrays with correct dtype
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)

        # Use sklearn's implementation which is numerically stable
        # Reshape for sklearn (expects 2D arrays)
        a_reshaped = a.reshape(1, -1)
        b_reshaped = b.reshape(1, -1)
        
        similarity = sklearn_cosine_similarity(a_reshaped, b_reshaped)[0, 0]
        
        # Ensure result is in [0, 1] range (normalized embeddings)
        similarity = float(np.clip(similarity, 0.0, 1.0))
        
        logger.debug(f"Cosine similarity: {similarity:.6f}")
        return similarity
        
    except Exception as e:
        logger.error(f"Error computing cosine similarity: {e}")
        # Return 0 on error (safest option)
        return 0.0


def verify_speaker(user_id: int, audio_file_path: str) -> dict:
    """
    Verify whether the provided audio matches the enrolled voice of the user.

    Decision logic:
        similarity >= SIMILARITY_THRESHOLD_HIGH  → authenticated (direct login)
        similarity >= SIMILARITY_THRESHOLD_LOW   → OTP fallback required
        similarity <  SIMILARITY_THRESHOLD_LOW   → rejected (do not proceed)

    Args:
        user_id:          ID of the user to verify
        audio_file_path:  Path to the audio file to verify against

    Returns:
        Dictionary with keys:
            success          (bool)   – processing succeeded without errors
            authenticated    (bool)   – whether the speaker is accepted
            requires_otp     (bool)   – whether an OTP fallback should be triggered
            similarity_score (float)  – cosine similarity between embeddings
            message          (str)    – human-readable result description
            reason           (str)    – machine-readable rejection / fallback reason
    """
    logger.info(f"[VERIFY] Starting voice verification for user {user_id}")
    logger.info(f"[VERIFY] Audio file: {audio_file_path}")

    # ================================================================== #
    # 1. Fetch stored embedding from database
    # ================================================================== #
    logger.info(f"[VERIFY] Fetching stored embedding for user {user_id}...")
    stored_embedding = db.get_voice_embedding(user_id)
    
    if stored_embedding is None or len(stored_embedding) == 0:
        logger.warning(f"[VERIFY] No voice embedding found for user {user_id}")
        return {
            "success": False,
            "authenticated": False,
            "requires_otp": False,
            "similarity_score": None,
            "message": "No voice enrollment found for this user. Please enroll your voice first.",
            "reason": "no_enrollment",
        }
    
    logger.info(f"[VERIFY] ✓ Stored embedding retrieved. Dimension: {len(stored_embedding)}")

    # ================================================================== #
    # 2. Preprocess incoming audio
    # ================================================================== #
    logger.info(f"[VERIFY] Preprocessing incoming audio...")
    try:
        audio = preprocess_audio(audio_file_path)
        logger.info(f"[VERIFY] ✓ Audio preprocessed. Shape: {audio.shape}, dtype: {audio.dtype}, duration: {len(audio)/SAMPLE_RATE:.2f}s")
    except Exception as e:
        logger.error(f"[VERIFY] ✗ Audio preprocessing failed: {e}")
        return {
            "success": False,
            "authenticated": False,
            "requires_otp": False,
            "similarity_score": None,
            "message": "Failed to process the audio file. Please try again.",
            "reason": "preprocessing_error",
        }

    # ================================================================== #
    # 3. Extract embedding from incoming audio using ECAPA-TDNN
    # ================================================================== #
    logger.info(f"[VERIFY] Extracting live embedding using ECAPA-TDNN...")
    try:
        speaker_encoder = get_speaker_encoder()
        live_embedding = speaker_encoder.extract_embedding(audio, sample_rate=SAMPLE_RATE)
        logger.info(f"[VERIFY] ✓ Live embedding extracted. Shape: {live_embedding.shape}")
    except Exception as e:
        logger.error(f"[VERIFY] ✗ Embedding extraction failed: {e}")
        return {
            "success": False,
            "authenticated": False,
            "requires_otp": False,
            "similarity_score": None,
            "message": "Failed to extract voice features. Please try again.",
            "reason": "embedding_error",
        }

    # ================================================================== #
    # 4. Compute cosine similarity between stored and live embeddings
    # ================================================================== #
    logger.info(f"[VERIFY] Computing cosine similarity...")
    similarity = cosine_similarity(
        np.array(stored_embedding, dtype=np.float32),
        live_embedding
    )
    logger.info(f"[VERIFY] Similarity score: {similarity:.6f}")
    logger.info(f"[VERIFY] Thresholds: HIGH={SIMILARITY_THRESHOLD_HIGH}, LOW={SIMILARITY_THRESHOLD_LOW}")

    # ================================================================== #
    # 5. Make authentication decision
    # ================================================================== #
    if similarity >= SIMILARITY_THRESHOLD_HIGH:
        logger.info(f"[VERIFY] ✓ AUTHENTICATED: similarity ({similarity:.4f}) >= HIGH threshold ({SIMILARITY_THRESHOLD_HIGH})")
        status = "authenticated"
        authenticated = True
        requires_otp = False
        message = f"Voice authentication successful! (Similarity: {similarity:.4f})"
        reason = "high_confidence"
        
    elif similarity >= SIMILARITY_THRESHOLD_LOW:
        logger.info(f"[VERIFY] ⚠ OTP REQUIRED: LOW threshold <= similarity ({similarity:.4f}) < HIGH threshold")
        status = "otp_required"
        authenticated = False
        requires_otp = True
        message = f"Voice partially matched. OTP verification required. (Similarity: {similarity:.4f})"
        reason = "medium_confidence"
        
    else:
        logger.warning(f"[VERIFY] ✗ REJECTED: similarity ({similarity:.4f}) < LOW threshold ({SIMILARITY_THRESHOLD_LOW})")
        status = "rejected"
        authenticated = False
        requires_otp = False
        message = f"Voice does not match. Authentication failed. (Similarity: {similarity:.4f})"
        reason = "low_confidence"

    # ================================================================== #
    # 6. Record login attempt for auditing
    # ================================================================== #
    try:
        db.record_login_attempt(
            user_id=user_id,
            similarity_score=similarity,
            spoof_probability=0.0,  # Can be set later by anti-spoofing module
            status=status,
        )
        logger.info(f"[VERIFY] ✓ Login attempt recorded")
    except Exception as e:
        logger.warning(f"[VERIFY] ⚠ Could not record login attempt: {e}")

    # ================================================================== #
    # 7. Return verification result
    # ================================================================== #
    return {
        "success": True,
        "authenticated": authenticated,
        "requires_otp": requires_otp,
        "similarity_score": float(similarity),
        "message": message,
        "reason": reason,
    }
