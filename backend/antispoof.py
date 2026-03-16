"""
Anti-spoofing detection module.
Detects replay attacks and synthetic voice attacks.
"""

import logging
import numpy as np
from utils.audio_processing import extract_spectral_features, SAMPLE_RATE
from model_loader import get_antispoof_model

logger = logging.getLogger(__name__)


def detect_spoof(audio: np.ndarray) -> dict:
    """
    Detect if audio is a spoof (replay attack or synthetic voice).
    
    Args:
        audio: Audio signal as numpy array
        
    Returns:
        Dictionary with spoof detection results
    """
    try:
        logger.info("Starting anti-spoofing detection")
        
        # Extract spectral features
        features = extract_spectral_features(audio)
        
        # Get MFCC features
        mfcc = features['mfcc']
        
        # Flatten MFCC for the neural network
        mfcc_flattened = mfcc.flatten()
        
        # Get anti-spoofing model
        antispoof_model = get_antispoof_model()
        
        # Detect spoof
        spoof_probability = antispoof_model.detect_spoof(mfcc_flattened)
        
        # Decision threshold
        SPOOF_THRESHOLD = 0.5
        is_spoofed = spoof_probability > SPOOF_THRESHOLD
        
        logger.info(f"Spoof detection result: probability={spoof_probability:.4f}, is_spoofed={is_spoofed}")
        
        return {
            'success': True,
            'is_spoofed': is_spoofed,
            'spoof_probability': spoof_probability,
            'threshold': SPOOF_THRESHOLD,
            'message': 'Spoof detected! Possible replay or synthetic attack.' if is_spoofed else 'Clean audio detected.'
        }
        
    except Exception as e:
        logger.error(f"Anti-spoofing detection failed: {e}")
        return {
            'success': False,
            'is_spoofed': False,
            'spoof_probability': 0.5,
            'message': f'Anti-spoofing detection error: {str(e)}'
        }


def analyze_audio_quality(audio: np.ndarray) -> dict:
    """
    Analyze audio quality for login.
    
    Args:
        audio: Audio signal
        
    Returns:
        Audio quality metrics
    """
    try:
        # Check audio length
        duration = len(audio) / SAMPLE_RATE
        
        # Check RMS energy
        rms = np.sqrt(np.mean(audio ** 2))
        
        # Check for silence (very low RMS)
        is_silent = rms < 0.01
        
        # Check dynamic range
        max_val = np.max(np.abs(audio))
        min_val = np.min(np.abs(audio))
        dynamic_range = max_val - min_val if max_val > 0 else 0
        
        quality_score = min(1.0, (rms * 100))  # Normalize to 0-1
        
        return {
            'duration': duration,
            'rms_energy': float(rms),
            'is_silent': is_silent,
            'dynamic_range': float(dynamic_range),
            'quality_score': float(quality_score)
        }
        
    except Exception as e:
        logger.error(f"Audio quality analysis failed: {e}")
        return {
            'duration': 0,
            'rms_energy': 0,
            'is_silent': True,
            'dynamic_range': 0,
            'quality_score': 0
        }
