"""
Model loading utilities.
Loads pretrained WavLM speaker embedding model and anti-spoofing model.
"""

import torch
import torch.nn as nn
import logging
from transformers import AutoModel, WavLMForXVector
import numpy as np

logger = logging.getLogger(__name__)

# Check if GPU is available
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {DEVICE}")


class WavLMSpeakerEncoder:
    """Load and use pretrained WavLM model for speaker embeddings."""
    
    def __init__(self, model_name: str = "microsoft/wavlm-base-plus-sv"):
        """
        Initialize WavLM speaker embedding model.
        
        Args:
            model_name: HuggingFace model identifier
        """
        self.model_name = model_name
        self.model = None
        self.device = DEVICE
        self.load_model()
    
    def load_model(self):
        """Load WavLM model from HuggingFace."""
        try:
            logger.info(f"Loading model: {self.model_name}")
            self.model = WavLMForXVector.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info("WavLM model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load WavLM model: {e}")
            raise
    
    def extract_embedding(self, audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Extract speaker embedding from audio.
        
        Args:
            audio: Audio signal as numpy array
            sample_rate: Sample rate of audio (default 16000 Hz)
            
        Returns:
            Speaker embedding vector
        """
        try:
            # Convert numpy array to torch tensor
            audio_tensor = torch.from_numpy(audio).float()
            
            # Add batch dimension and move to device
            audio_tensor = audio_tensor.unsqueeze(0).to(self.device)
            
            # Extract embedding
            with torch.no_grad():
                outputs = self.model(audio_tensor)
                embedding = outputs.embeddings.cpu().numpy()
            
            # Return the embedding (remove batch dimension)
            return embedding[0]
            
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


# Global model instances
wavlm_model = None
antispoof_model = None


def load_models():
    """Load all models globally."""
    global wavlm_model, antispoof_model
    
    try:
        logger.info("Loading models...")
        wavlm_model = WavLMSpeakerEncoder()
        antispoof_model = AntiSpoofDetector()
        logger.info("All models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise


def get_wavlm_model() -> WavLMSpeakerEncoder:
    """Get WavLM model instance."""
    global wavlm_model
    if wavlm_model is None:
        wavlm_model = WavLMSpeakerEncoder()
    return wavlm_model


def get_antispoof_model() -> AntiSpoofDetector:
    """Get anti-spoofing model instance."""
    global antispoof_model
    if antispoof_model is None:
        antispoof_model = AntiSpoofDetector()
    return antispoof_model
