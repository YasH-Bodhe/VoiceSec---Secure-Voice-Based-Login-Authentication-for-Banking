"""
Anti-spoofing detection module.
Detects replay attacks and synthetic voice attacks using CNN features.
"""

import logging
import numpy as np
from utils.audio_processing import extract_spectral_features, SAMPLE_RATE
from model_loader import get_antispoof_model

logger = logging.getLogger(__name__)

# Spoof detection threshold
SPOOF_THRESHOLD = 0.5


def detect_spoof(audio: np.ndarray) -> dict:
    """
    Detect if audio is a spoof (replay attack or synthetic voice).
    
    Args:
        audio: Audio signal as numpy array
        
    Returns:
        Dictionary with spoof detection results
    """
    try:
        logger.info("[SPOOF] Starting anti-spoofing detection")
        
        # Check audio quality first
        quality = analyze_audio_quality(audio)
        logger.info(f"[SPOOF] Audio quality: RMS={quality['rms_energy']:.4f}, Duration={quality['duration']:.2f}s")
        
        if quality['is_silent']:
            logger.warning("[SPOOF] Audio is silent or very low energy")
            return {
                'success': False,
                'is_spoofed': True,
                'spoof_probability': 0.9,
                'threshold': SPOOF_THRESHOLD,
                'message': 'Audio is too quiet. Could not detect spoofing.',
                'reason': 'insufficient_audio'
            }
        
        # Extract spectral features
        logger.info("[SPOOF] Extracting spectral features...")
        features = extract_spectral_features(audio)
        
        # Get MFCC features for the neural network
        mfcc = features['mfcc']
        
        # Flatten MFCC for the model (typically 13 x 188 = 2444)
        mfcc_flattened = mfcc.flatten()
        logger.info(f"[SPOOF] MFCC features shape: {mfcc.shape}, flattened: {mfcc_flattened.shape}")
        
        # Get anti-spoofing model and detect spoof
        logger.info("[SPOOF] Running anti-spoofing model...")
        antispoof_model = get_antispoof_model()
        spoof_probability = antispoof_model.detect_spoof(mfcc_flattened)
        logger.info(f"[SPOOF] Spoof probability: {spoof_probability:.4f}")
        
        # Decision threshold
        is_spoofed = spoof_probability > SPOOF_THRESHOLD
        
        if is_spoofed:
            logger.warning(f"[SPOOF] ✗ Spoof detected! Probability: {spoof_probability:.4f}")
            return {
                'success': True,
                'is_spoofed': True,
                'spoof_probability': float(spoof_probability),
                'threshold': SPOOF_THRESHOLD,
                'message': f'⚠️ Spoof detected! Probability: {spoof_probability:.4f}. Possible replay or synthetic attack.',
                'reason': 'replay_or_synthetic'
            }
        else:
            logger.info(f"[SPOOF] ✓ Clean audio detected. Probability: {spoof_probability:.4f}")
            return {
                'success': True,
                'is_spoofed': False,
                'spoof_probability': float(spoof_probability),
                'threshold': SPOOF_THRESHOLD,
                'message': f'✓ Audio appears genuine. Probability: {spoof_probability:.4f}',
                'reason': 'genuine_audio'
            }
        
    except Exception as e:
        logger.error(f"[SPOOF] ✗ Anti-spoofing detection failed: {e}")
        # On error, default to safe mode (allow but flag as uncertain)
        return {
            'success': False,
            'is_spoofed': False,
            'spoof_probability': 0.5,
            'threshold': SPOOF_THRESHOLD,
            'message': f'Anti-spoofing detection error: {str(e)}',
            'reason': 'detection_error'
        }


def analyze_audio_quality(audio: np.ndarray) -> dict:
    """
    Analyze audio quality for login verification.
    
    Args:
        audio: Audio signal (numpy array)
        
    Returns:
        Dictionary with audio quality metrics
    """
    try:
        logger.debug("[QUALITY] Analyzing audio quality...")
        
        # Check audio length
        duration = len(audio) / SAMPLE_RATE
        
        # Check RMS (Root Mean Square) energy
        rms = np.sqrt(np.mean(audio ** 2))
        
        # Check for silence (very low RMS)
        # Typically, RMS < 0.01 indicates very quiet audio
        is_silent = rms < 0.01
        
        # Check dynamic range
        max_val = np.max(np.abs(audio)) if len(audio) > 0 else 0
        min_val = np.min(np.abs(audio)) if len(audio) > 0 else 0
        dynamic_range = max_val - min_val if max_val > 0 else 0
        
        # Calculate quality score (0-1)
        # Based on RMS energy (should be between 0.01 and 1.0)
        if rms < 0.01:
            quality_score = 0.0  # Too quiet
        elif rms > 0.5:
            quality_score = 0.9  # Good level
        else:
            quality_score = min(1.0, (rms * 2))  # Linear scaling
        
        logger.debug(f"[QUALITY] Duration: {duration:.2f}s, RMS: {rms:.4f}, Dynamic: {dynamic_range:.4f}, Score: {quality_score:.4f}")
        
        return {
            'duration': float(duration),
            'rms_energy': float(rms),
            'is_silent': bool(is_silent),
            'dynamic_range': float(dynamic_range),
            'quality_score': float(quality_score),
            'max_amplitude': float(max_val),
            'min_amplitude': float(min_val)
        }
        
    except Exception as e:
        logger.error(f"[QUALITY] Audio quality analysis failed: {e}")
        return {
            'duration': 0.0,
            'rms_energy': 0.0,
            'is_silent': True,
            'dynamic_range': 0.0,
            'quality_score': 0.0,
            'max_amplitude': 0.0,
            'min_amplitude': 0.0,
            'error': str(e)
        }

