"""
Audio processing utilities for voice authentication system.
Handles WAV conversion, normalization, and MFCC extraction.
"""

import numpy as np
import logging
import gc
from pathlib import Path
from scipy.io import wavfile

# Optional dependencies
try:
    import librosa
except Exception:
    librosa = None

try:
    import soundfile as sf
except Exception:
    sf = None

try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

logger = logging.getLogger(__name__)

# Audio configuration
SAMPLE_RATE = 16000  # 16 kHz sampling rate
DURATION = 5  # 5 seconds of audio
N_MFCC = 13  # Number of MFCC coefficients
N_FFT = 400
HOP_LENGTH = 160


def _resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int = SAMPLE_RATE) -> np.ndarray:
    """Resample to target sample rate."""
    if orig_sr == target_sr:
        return audio
    if librosa:
        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    raise RuntimeError("Resampling requires librosa; install setuptools and librosa properly.")


def _to_mono(audio: np.ndarray) -> np.ndarray:
    """Convert multichannel audio to mono."""
    if audio.ndim == 1:
        return audio
    return np.mean(audio, axis=1)


def load_audio(audio_path: str) -> np.ndarray:
    """Load audio from a file path and return mono float32 audio at SAMPLE_RATE.

    Supports: WAV, MP3, FLAC, OGG, WEBM, and other formats via fallback methods.
    """
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Detect file format by magic bytes
    try:
        with open(audio_path, 'rb') as f:
            magic = f.read(4)
            logger.info(f"File magic bytes: {magic}, path: {audio_path}")
    except Exception as e:
        logger.warning(f"Could not read file magic bytes: {e}")
        magic = b''

    exceptions = []

    # 1) Try librosa if available (most robust)
    if librosa:
        try:
            logger.info("Attempting librosa load...")
            audio, sr = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
            logger.info(f"✓ Loaded audio via librosa from {audio_path} (sr={sr})")
            return audio.astype(np.float32)
        except Exception as e:
            logger.warning(f"Librosa load failed: {e}")
            exceptions.append(("librosa", e))

    # 2) Try soundfile if available
    if sf:
        try:
            logger.info("Attempting soundfile load...")
            audio, sr = sf.read(str(audio_path), always_2d=False)
            audio = np.asarray(audio, dtype=np.float32)
            audio = _to_mono(audio)
            if sr != SAMPLE_RATE:
                audio = _resample_audio(audio, sr, SAMPLE_RATE)
            logger.info(f"✓ Loaded audio via soundfile from {audio_path} (sr={sr})")
            return audio
        except Exception as e:
            logger.warning(f"Soundfile load failed: {e}")
            exceptions.append(("soundfile", e))

    # 3) Try scipy wavfile for WAV files
    if magic.startswith(b'RIFF'):
        try:
            logger.info("Attempting scipy wavfile load (detected RIFF header)...")
            sr, audio = wavfile.read(str(audio_path))
            # Normalize int16/int32 PCM to float32 [-1, 1]; leave float as-is
            if np.issubdtype(audio.dtype, np.integer):
                max_val = np.iinfo(audio.dtype).max
                audio = audio.astype(np.float32) / max_val
            else:
                audio = audio.astype(np.float32)
            audio = _to_mono(audio)
            if sr != SAMPLE_RATE:
                audio = _resample_audio(audio, sr, SAMPLE_RATE)
            logger.info(f"✓ Loaded audio via scipy wavfile from {audio_path} (sr={sr})")
            return audio
        except Exception as e:
            logger.warning(f"scipy wavfile load failed: {e}")
            exceptions.append(("scipy", e))

    # 4) Try pydub for multiple formats (WebM, MP3, OGG, etc.)
    if AudioSegment:
        try:
            logger.info("Attempting pydub conversion...")
            seg = AudioSegment.from_file(str(audio_path))
            logger.info(
                f"Loaded segment: {len(seg)}ms, frame rate: {seg.frame_rate},"
                f" channels: {seg.channels}"
            )
            if seg.frame_rate != SAMPLE_RATE:
                seg = seg.set_frame_rate(SAMPLE_RATE)
            if seg.channels != 1:
                seg = seg.set_channels(1)
            samples = np.array(seg.get_array_of_samples(), dtype=np.int16)
            samples = samples.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
            logger.info(f"✓ Loaded audio via pydub from {audio_path}, shape: {samples.shape}")
            return samples
        except Exception as e:
            logger.warning(f"pydub load failed: {e}")
            exceptions.append(("pydub", e))

    # 5) Try ffmpeg conversion as last resort
    try:
        import subprocess
        import tempfile
        import os

        logger.info("Attempting ffmpeg conversion...")
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name

            result = subprocess.run(
                [
                    'ffmpeg', '-y', '-i', str(audio_path),
                    '-acodec', 'pcm_s16le', '-ar', str(SAMPLE_RATE), '-ac', '1',
                    tmp_path,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {result.stderr}")

            sr, audio = wavfile.read(tmp_path)
            audio = audio.astype(np.float32) / 32768.0
            audio = _to_mono(audio)
            logger.info(f"✓ Loaded audio via ffmpeg from {audio_path}")
            return audio
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except Exception as e:
        logger.warning(f"ffmpeg conversion failed: {e}")
        exceptions.append(("ffmpeg", e))

    # If all methods failed, provide detailed error
    error_msg = (
        f"Could not load audio file {audio_path}.\n"
        f"Magic bytes: {magic}\n"
        f"File size: {audio_path.stat().st_size if audio_path.exists() else 'N/A'} bytes\n"
        "Failed methods:\n"
    )
    for method, exc in exceptions:
        error_msg += f"  - {method}: {str(exc)[:100]}\n"

    logger.error(error_msg)
    raise RuntimeError(error_msg)


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    """Normalize audio to [-1, 1] range."""
    original_max = np.max(np.abs(audio)) if audio.size else 0
    original_mean = np.mean(np.abs(audio)) if audio.size else 0
    original_len = len(audio)
    
    logger.info(f"Normalize: before - shape={audio.shape}, max={original_max:.6f}, mean={original_mean:.6f}")
    
    if librosa:
        try:
            audio = librosa.effects.trim(audio, top_db=40)[0]
            logger.info(f"Normalize: trimmed with librosa - new shape={audio.shape}")
        except Exception as e:
            logger.warning(f"Librosa trim failed: {e}, using fallback")
            # Basic trim: remove leading/trailing low-energy frames
            threshold = 1e-4
            non_silent = np.where(np.abs(audio) > threshold)[0]
            if len(non_silent) > 0:
                audio = audio[non_silent[0]: non_silent[-1] + 1]
                logger.info(f"Normalize: fallback trim - new shape={audio.shape}")
    else:
        # Basic trim: remove leading/trailing low-energy frames
        threshold = 1e-4
        non_silent = np.where(np.abs(audio) > threshold)[0]
        if len(non_silent) > 0:
            audio = audio[non_silent[0]: non_silent[-1] + 1]
            logger.info(f"Normalize: basic trim - new shape={audio.shape}")

    max_val = np.max(np.abs(audio)) if audio.size else 1.0
    if max_val > 0:
        audio = audio / max_val
        logger.info(f"Normalize: after - shape={audio.shape}, max={np.max(np.abs(audio)):.6f}, scale_factor={max_val:.6f}")
    else:
        logger.warning("Normalize: audio max is 0! Returning as-is")
    
    return audio


def preprocess_audio(audio_path: str) -> np.ndarray:
    """
    Complete audio preprocessing pipeline.

    Args:
        audio_path: Path to audio file

    Returns:
        Preprocessed audio signal
    """
    try:
        audio = load_audio(audio_path)
        audio = normalize_audio(audio)
        return audio
    finally:
        # Encourage release of any lingering file handles
        gc.collect()


def extract_mfcc(audio: np.ndarray, n_mfcc: int = N_MFCC) -> np.ndarray:
    """Extract MFCC features from audio."""
    if not librosa:
        raise RuntimeError(
            "Librosa is required for MFCC extraction. Install librosa and setuptools."
        )
    try:
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=SAMPLE_RATE,
            n_mfcc=n_mfcc,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
        )
        logger.info(f"Extracted MFCC features with shape {mfcc.shape}")
        return mfcc
    except Exception as e:
        logger.error(f"Failed to extract MFCC: {e}")
        raise


def extract_spectral_features(audio: np.ndarray) -> dict:
    """Extract spectral features for anti-spoofing."""
    if not librosa:
        raise RuntimeError(
            "Librosa is required for spectral feature extraction. Install librosa and setuptools."
        )

    features = {
        'mfcc': librosa.feature.mfcc(
            y=audio, sr=SAMPLE_RATE, n_mfcc=N_MFCC, n_fft=N_FFT, hop_length=HOP_LENGTH
        ),
        'zcr': librosa.feature.zero_crossing_rate(audio, hop_length=HOP_LENGTH),
        'spectral_centroid': librosa.feature.spectral_centroid(
            y=audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH
        ),
        'spectral_rolloff': librosa.feature.spectral_rolloff(
            y=audio, sr=SAMPLE_RATE, hop_length=HOP_LENGTH
        ),
        'mel_spectrogram': librosa.feature.melspectrogram(
            y=audio, sr=SAMPLE_RATE, n_fft=N_FFT, hop_length=HOP_LENGTH
        ),
    }
    return features


def save_audio(audio: np.ndarray, output_path: str, sr: int = SAMPLE_RATE):
    """
    Save audio to WAV file.

    Args:
        audio: Audio signal (float32, expected in [-1, 1])
        output_path: Path to save audio
        sr: Sample rate
    """
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        audio_int16 = np.int16(np.clip(audio, -1.0, 1.0) * 32767)
        wavfile.write(output_path, sr, audio_int16)
        logger.info(f"Saved audio to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save audio: {e}")
        raise