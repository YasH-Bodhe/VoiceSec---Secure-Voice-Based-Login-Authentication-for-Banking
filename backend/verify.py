"""
Voice verification module.
Handles speaker verification by comparing voice embeddings with cosine similarity.
"""

import logging
import numpy as np
from utils.audio_processing import preprocess_audio, SAMPLE_RATE
from model_loader import get_wavlm_model
from database import db

logger = logging.getLogger(__name__)

# Verification thresholds
SIMILARITY_THRESHOLD_HIGH = 0.65   # Above this → authenticated directly
SIMILARITY_THRESHOLD_LOW  = 0.45   # Below this → rejected outright
# Between LOW and HIGH → OTP fallback


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        a: First embedding vector
        b: Second embedding vector

    Returns:
        Cosine similarity score in [-1, 1]; higher means more similar
    """
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        logger.warning("Zero-norm embedding encountered during cosine similarity computation")
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def verify_speaker(user_id: int, audio_file_path: str) -> dict:
    """
    Verify whether the provided audio matches the enrolled voice of the user.

    Decision logic:
        similarity >= SIMILARITY_THRESHOLD_HIGH  → authenticated
        similarity >= SIMILARITY_THRESHOLD_LOW   → OTP fallback required
        similarity <  SIMILARITY_THRESHOLD_LOW   → rejected

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
    logger.info(f"Starting voice verification for user {user_id}")

    # ------------------------------------------------------------------ #
    # 1. Fetch stored embedding
    # ------------------------------------------------------------------ #
    stored_embedding = db.get_voice_embedding(user_id)
    if stored_embedding is None:
        logger.warning(f"No voice embedding found for user {user_id}")
        return {
            "success": False,
            "authenticated": False,
            "requires_otp": False,
            "similarity_score": None,
            "message": "No voice enrollment found for this user. Please enroll your voice first.",
            "reason": "no_enrollment",
        }

    # ------------------------------------------------------------------ #
    # 2. Preprocess incoming audio
    # ------------------------------------------------------------------ #
    try:
        audio = preprocess_audio(audio_file_path)
        logger.info(f"Audio preprocessed – shape: {audio.shape}, dtype: {audio.dtype}")
    except Exception as e:
        logger.error(f"Audio preprocessing failed for user {user_id}: {e}")
        return {
            "success": False,
            "authenticated": False,
            "requires_otp": False,
            "similarity_score": None,
            "message": "Failed to process the audio file. Please try again.",
            "reason": "preprocessing_error",
        }

    # ------------------------------------------------------------------ #
    # 3. Extract embedding from incoming audio
    # ------------------------------------------------------------------ #
    try:
        wavlm_model = get_wavlm_model()
        live_embedding = wavlm_model.extract_embedding(audio, sample_rate=SAMPLE_RATE)
        logger.info(
            f"Live embedding extracted – dim: "
            f"{live_embedding.shape if hasattr(live_embedding, 'shape') else len(live_embedding)}"
        )
    except Exception as e:
        logger.error(f"Embedding extraction failed for user {user_id}: {e}")
        return {
            "success": False,
            "authenticated": False,
            "requires_otp": False,
            "similarity_score": None,
            "message": "Failed to extract voice features. Please try again.",
            "reason": "embedding_error",
        }

    # ------------------------------------------------------------------ #
    # 4. Compute similarity
    # ------------------------------------------------------------------ #
    similarity = cosine_similarity(stored_embedding, live_embedding)
    logger.info(
        f"Similarity score for user {user_id}: {similarity:.4f} "
        f"(HIGH={SIMILARITY_THRESHOLD_HIGH}, LOW={SIMILARITY_THRESHOLD_LOW})"
    )

    # ------------------------------------------------------------------ #
    # 5. Record attempt
    # ------------------------------------------------------------------ #
    try:
        if similarity >= SIMILARITY_THRESHOLD_HIGH:
            status = "authenticated"
        elif similarity >= SIMILARITY_THRESHOLD_LOW:
            status = "otp_required"
        else:
            status = "rejected"

        db.record_login_attempt(
            user_id=user_id,
            similarity_score=similarity,
            spoof_probability=0.0,   # spoof check can be layered on top later
            status=status,
        )
    except Exception as e:
        # Non-fatal – just log it
        logger.warning(f"Could not record login attempt for user {user_id}: {e}")

    # ------------------------------------------------------------------ #
    # 6. Decision
    # ------------------------------------------------------------------ #
    if similarity >= SIMILARITY_THRESHOLD_HIGH:
        logger.info(f"Voice authentication PASSED for user {user_id} (score={similarity:.4f})")
        return {
            "success": True,
            "authenticated": True,
            "requires_otp": False,
            "similarity_score": similarity,
            "message": "Voice authentication successful!",
            "reason": "authenticated",
        }

    if similarity >= SIMILARITY_THRESHOLD_LOW:
        logger.info(
            f"Voice partially matched for user {user_id} (score={similarity:.4f}) – OTP required"
        )
        return {
            "success": True,
            "authenticated": False,
            "requires_otp": True,
            "similarity_score": similarity,
            "message": (
                "Voice similarity is moderate. "
                "An OTP has been sent to your registered email for additional verification."
            ),
            "reason": "low_confidence",
        }

    logger.info(f"Voice authentication FAILED for user {user_id} (score={similarity:.4f})")
    return {
        "success": True,
        "authenticated": False,
        "requires_otp": False,
        "similarity_score": similarity,
        "message": "Voice does not match the enrolled profile.",
        "reason": "similarity_too_low",
    }