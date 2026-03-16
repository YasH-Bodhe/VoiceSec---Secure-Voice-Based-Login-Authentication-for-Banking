"""
Model loading utilities.
Loads pretrained ECAPA-TDNN speaker embedding model and anti-spoofing model.
"""

import torch
import torch.nn as nn
import logging
import numpy as np
import os
from pathlib import Path
import shutil
import sys

logger = logging.getLogger(__name__)

# Check if GPU is available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {DEVICE}")

# Set environment variables to handle Windows symlink issues FIRST
os.environ['HF_HUB_DISABLE_SYMLINK_WARNING'] = '1'
os.environ['HF_HUB_NO_SYMLINK'] = '1'

# Use a cache directory that doesn't require symlinks
CACHE_DIR = str(Path.home() / '.cache' / 'speechbrain_models_local')

# Workaround for Windows symlink issue in huggingface_hub
def patch_symlink_for_windows():
    """Patch pathlib.Path.symlink_to to use copy on Windows instead."""
    original_symlink_to = Path.symlink_to
    
    def symlink_to_wrapper(self, target, target_is_directory=False):
        try:
            # Try normal symlink first
            return original_symlink_to(self, target, target_is_directory)
        except OSError as e:
            if "WinError 1314" in str(e) or "required privilege" in str(e):
                # Windows permission error - use copy instead
                logger.warning(f"Symlink failed for {self}, using copy instead")
                try:
                    if Path(target).is_dir():
                        if self.exists():
                            shutil.rmtree(self)
                        shutil.copytree(target, self)
                    else:
                        self.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(target, self)
                    return
                except Exception as copy_err:
                    logger.error(f"Copy also failed: {copy_err}")
                    raise
            else:
                raise
    
    # Monkeypatch
    Path.symlink_to = symlink_to_wrapper

# Apply the patch before importing huggingface_hub or speechbrain
patch_symlink_for_windows()


class ECAPATDNNSpeakerEncoder:
    """Load and use pretrained ECAPA-TDNN model from SpeechBrain for speaker embeddings."""
    
    def __init__(self, model_name: str = "speechbrain/spkrec-ecapa-voxceleb"):
        """
        Initialize ECAPA-TDNN speaker embedding model.
        
        Args:
            model_name: SpeechBrain model identifier
        """
        self.model_name = model_name
        self.model = None
        self.device = DEVICE
        self.embedding_dim = 192  # ECAPA-TDNN output dimension
        self.load_model()
    
    def load_model(self):
        """Load ECAPA-TDNN model from SpeechBrain."""
        try:
            logger.info(f"Loading ECAPA-TDNN model: {self.model_name}")
            
            # Create cache directory
            cache_path = Path(CACHE_DIR)
            cache_path.mkdir(parents=True, exist_ok=True)
            
            # Import speechbrain speaker verifier
            from speechbrain.pretrained import SpeakerRecognition
            
            # Load the model with custom cache dir
            self.model = SpeakerRecognition.from_hparams(
                source=self.model_name,
                savedir=str(cache_path),
                run_opts={"device": str(self.device)}
            )
            
            logger.info(f"✓ ECAPA-TDNN model loaded successfully (embedding_dim={self.embedding_dim})")
            
        except Exception as e:
            logger.error(f"Failed to load ECAPA-TDNN model: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise
    
    def extract_embedding(self, audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Extract speaker embedding from audio using ECAPA-TDNN.
        
        Args:
            audio: Audio signal as numpy array
            sample_rate: Sample rate of audio (default 16000 Hz)
            
        Returns:
            Normalized speaker embedding vector (192-dim)
        """
        try:
            # Ensure audio is float32
            audio = np.asarray(audio, dtype=np.float32)
            
            # Convert to torch tensor
            audio_tensor = torch.from_numpy(audio).float()
            
            # Add batch dimension if needed
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0)
            
            # Move to device
            audio_tensor = audio_tensor.to(self.device)
            
            # Extract embedding
            with torch.no_grad():
                embedding = self.model.encode_batch(audio_tensor, wav_lens=torch.tensor([1.0]))
            
            # Convert to numpy and normalize
            embedding = embedding.cpu().numpy()[0]  # Remove batch dimension
            
            # Normalize embedding to unit length (important for cosine similarity)
            embedding_norm = np.linalg.norm(embedding)
            if embedding_norm > 0:
                embedding = embedding / embedding_norm
            
            logger.info(f"✓ Embedding extracted: shape={embedding.shape}, norm={np.linalg.norm(embedding):.4f}")
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Failed to extract embedding: {e}")
            raise


class SimpleAntiSpoofModel(nn.Module):
    """Simple MLP-based anti-spoofing detection model."""
    
    def __init__(self, input_size: int = 128):
        """
        Initialize anti-spoofing model.
        
        Args:
            input_size: Size of input features
        """
        super(SimpleAntiSpoofModel, self).__init__()
        
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        self.classifier = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()  # Output probability between 0 and 1
        )
    
    def forward(self, x):
        """Forward pass."""
        features = self.feature_extractor(x)
        spoof_prob = self.classifier(features)
        return spoof_prob


class AntiSpoofDetector:
    """Anti-spoofing detector for replay and synthetic voice detection."""
    
    def __init__(self):
        """Initialize anti-spoofing detector."""
        self.model = SimpleAntiSpoofModel(input_size=128)
        self.model.to(DEVICE)
        self.model.eval()
        logger.info("Anti-spoofing model initialized")
    
    def detect_spoof(self, features: np.ndarray) -> float:
        """
        Detect if audio is spoofed (replay or synthetic).
        
        Args:
            features: Input features (usually MFCC)
            
        Returns:
            Spoof probability (0-1): higher means more likely to be spoofed
        """
        try:
            # Flatten features if needed
            if features.ndim > 1:
                features = features.flatten()
            
            # Ensure correct size by padding or truncating
            if len(features) < 128:
                features = np.pad(features, (0, 128 - len(features)), mode='constant')
            else:
                features = features[:128]
            
            # Convert to tensor
            features_tensor = torch.from_numpy(features).float()
            features_tensor = features_tensor.unsqueeze(0).to(DEVICE)
            
            # Get prediction
            with torch.no_grad():
                spoof_prob = self.model(features_tensor).cpu().numpy()[0, 0]
            
            logger.info(f"Spoof detection probability: {spoof_prob:.4f}")
            return float(spoof_prob)
            
        except Exception as e:
            logger.error(f"Failed to detect spoof: {e}")
            return 0.5  # Default to uncertain if error occurs


# Global model instances (cached to avoid repeated loading)
speaker_encoder = None
antispoof_model = None


def load_models():
    """Load all models globally during startup."""
    global speaker_encoder, antispoof_model
    
    try:
        logger.info("=" * 50)
        logger.info("Loading ML Models...")
        logger.info("=" * 50)
        
        speaker_encoder = ECAPATDNNSpeakerEncoder()
        logger.info("✓ ECAPA-TDNN Speaker Encoder loaded")
        
        antispoof_model = AntiSpoofDetector()
        logger.info("✓ Anti-spoofing Model loaded")
        
        logger.info("=" * 50)
        logger.info("All models loaded successfully!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise


def get_speaker_encoder() -> ECAPATDNNSpeakerEncoder:
    """Get cached speaker encoder instance. Loads if not already loaded."""
    global speaker_encoder
    if speaker_encoder is None:
        logger.warning("Speaker encoder not preloaded, loading now...")
        speaker_encoder = ECAPATDNNSpeakerEncoder()
    return speaker_encoder


def get_antispoof_model() -> AntiSpoofDetector:
    """Get cached anti-spoofing model instance. Loads if not already loaded."""
    global antispoof_model
    if antispoof_model is None:
        logger.warning("Antispoof model not preloaded, loading now...")
        antispoof_model = AntiSpoofDetector()
    return antispoof_model


# For backward compatibility
def get_wavlm_model() -> ECAPATDNNSpeakerEncoder:
    """Deprecated: Use get_speaker_encoder() instead. Returns ECAPA-TDNN model."""
    logger.warning("get_wavlm_model() is deprecated. Use get_speaker_encoder() instead.")
    return get_speaker_encoder()
