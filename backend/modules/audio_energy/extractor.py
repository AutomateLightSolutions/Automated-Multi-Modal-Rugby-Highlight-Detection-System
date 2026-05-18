"""
RMS energy extraction from audio using librosa.
Pure signal processing — no trained model needed.
"""

import numpy as np
import librosa
import logging

logger = logging.getLogger(__name__)


def extract_rms_energy(audio_path: str,
                       target_sr: int = 22050,
                       frame_duration_ms: int = 23) -> np.ndarray:
    """
    Load audio and compute per-frame RMS energy.

    Args:
        audio_path: path to WAV file
        target_sr: sample rate to load at (22050 for librosa default)
        frame_duration_ms: duration of each analysis frame in milliseconds

    Returns:
        1D numpy array of RMS values, one per frame.
    """
    try:
        audio, _ = librosa.load(audio_path, sr=target_sr, mono=True)
    except Exception:
        logger.exception("Failed to load audio %s", audio_path)
        return np.zeros(100)

    # Convert frame duration from ms to samples
    frame_length = int(target_sr * frame_duration_ms / 1000)
    hop_length = frame_length // 2   # 50% overlap

    rms = librosa.feature.rms(
        y=audio,
        frame_length=frame_length,
        hop_length=hop_length
    )[0]   # shape: (num_frames,)

    return rms.astype(np.float32)
