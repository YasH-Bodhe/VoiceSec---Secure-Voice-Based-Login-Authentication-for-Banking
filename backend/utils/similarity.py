"""
Similarity computation utilities.
Implements cosine similarity manually for speaker verification.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)


def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Compute cosine similarity between two embeddings (computed manually).
    
    Cosine Similarity = (A · B) / (||A|| * ||B||)
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Cosine similarity score between 0 and 1
    """
    # Convert to numpy arrays if needed
    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)
    
    # Compute dot product
    dot_product = np.sum(embedding1 * embedding2)
    
    # Compute norms
    norm1 = np.sqrt(np.sum(embedding1 ** 2))
    norm2 = np.sqrt(np.sum(embedding2 ** 2))
    
    # Avoid division by zero
    if norm1 == 0 or norm2 == 0:
        logger.warning("Zero norm detected in cosine similarity computation")
        return 0.0
    
    # Compute cosine similarity
    similarity = dot_product / (norm1 * norm2)
    
    # Ensure similarity is between 0 and 1
    similarity = max(0.0, min(1.0, similarity))
    
    logger.info(f"Computed cosine similarity: {similarity:.4f}")
    return similarity


def make_decision(similarity_score: float) -> dict:
    """
    Make authentication decision based on similarity score.
    
    Decision rules:
    - similarity >= 0.80 → login success
    - 0.60 <= similarity < 0.80 → OTP verification required
    - similarity < 0.60 → login failed
    
    Args:
        similarity_score: Cosine similarity score
        
    Returns:
        Dictionary with decision and message
    """
    if similarity_score >= 0.80:
        return {
            'decision': 'success',
            'message': 'Voice authenticated successfully',
            'requires_otp': False,
            'similarity_score': similarity_score
        }
    elif 0.60 <= similarity_score < 0.80:
        return {
            'decision': 'medium',
            'message': 'Voice similarity medium. OTP verification required.',
            'requires_otp': True,
            'similarity_score': similarity_score
        }
    else:
        return {
            'decision': 'failed',
            'message': 'Voice authentication failed. Similarity too low.',
            'requires_otp': False,
            'similarity_score': similarity_score
        }


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    """
    Normalize embedding to unit vector.
    
    Args:
        embedding: Embedding vector
        
    Returns:
        Normalized embedding
    """
    embedding = np.array(embedding)
    norm = np.sqrt(np.sum(embedding ** 2))
    
    if norm == 0:
        return embedding
    
    return embedding / norm


def compute_verification_confidence(similarity_score: float, spoof_probability: float) -> dict:
    """
    Compute overall verification confidence.
    
    Args:
        similarity_score: Speaker similarity score (0-1)
        spoof_probability: Spoof detection probability (0-1)
        
    Returns:
        Confidence metrics
    """
    # If spoof detected, confidence is very low
    if spoof_probability > 0.5:
        return {
            'confidence': 0.0,
            'is_spoofed': True,
            'reason': 'Anti-spoofing detection triggered'
        }
    
    # Otherwise, confidence is based on similarity
    return {
        'confidence': similarity_score,
        'is_spoofed': False,
        'reason': 'Clean voice detected'
    }
