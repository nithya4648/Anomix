import numpy as np
from typing import Optional, Tuple
from app.core.logging import get_logger

logger = get_logger(__name__)


class PyTorchLSTMAutoencoder:
    """
    A lightweight PyTorch-like / pure NumPy implementation of an LSTM Autoencoder
    for sequence anomaly detection. Calculates reconstruction error over a sequence window.
    """

    def __init__(self, sequence_length: int = 10, hidden_dim: int = 16, threshold_quantile: float = 0.95):
        self.sequence_length = sequence_length
        self.hidden_dim = hidden_dim
        self.threshold_quantile = threshold_quantile
        # Random initial weights simulating an trained autoencoder model
        np.random.seed(42)
        self.W_encoder = np.random.randn(1, hidden_dim) * 0.1
        self.W_decoder = np.random.randn(hidden_dim, 1) * 0.1
        self.threshold = 0.5

    def fit(self, sequences: np.ndarray):
        """Fit / baseline calibration on historical sequences"""
        if len(sequences) == 0:
            return
        reconstruction_errors = []
        for seq in sequences:
            reconstructed = self.predict_sequence(seq)
            mse = np.mean((seq - reconstructed) ** 2)
            reconstruction_errors.append(mse)
        
        self.threshold = np.quantile(reconstruction_errors, self.threshold_quantile)
        logger.info(f"LSTM Autoencoder fitted. Dynamic threshold set to {self.threshold:.4f}")

    def predict_sequence(self, sequence: np.ndarray) -> np.ndarray:
        """Reconstruct sequence using encoder-decoder architecture"""
        # Encoder pass (simulated recurrent feature extraction)
        latent = np.tanh(np.dot(sequence.reshape(-1, 1), self.W_encoder))
        latent_summary = np.mean(latent, axis=0, keepdims=True)
        
        # Decoder pass (reconstruction)
        reconstructed = np.dot(np.tile(latent_summary, (len(sequence), 1)), self.W_decoder).flatten()
        return reconstructed

    def detect_sequence_anomaly(self, sequence: list[float]) -> Tuple[bool, float, float]:
        """
        Calculates reconstruction MSE over sequence and returns (is_anomaly, confidence, mse).
        """
        if len(sequence) < self.sequence_length:
            return False, 0.0, 0.0

        seq_arr = np.array(sequence[-self.sequence_length:])
        reconstructed = self.predict_sequence(seq_arr)
        mse = float(np.mean((seq_arr - reconstructed) ** 2))

        # Compare MSE against dynamic threshold
        is_anomaly = bool(mse > self.threshold)
        confidence = min(1.0, mse / (self.threshold * 2.0 if self.threshold > 0 else 1.0))

        return is_anomaly, confidence, mse
