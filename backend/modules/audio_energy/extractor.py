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
    rms, _ = extract_rms_energy_with_times(audio_path, target_sr, frame_duration_ms)
    return rms


def extract_rms_energy_with_times(audio_path: str,
                                   target_sr: int = 22050,
                                   frame_duration_ms: int = 23) -> tuple[np.ndarray, np.ndarray]:
    """
    Same as extract_rms_energy, but also returns each frame's centre
    timestamp (seconds, absolute match time) — needed to bucket frames into
    the 4s/2s analysis windows in modules/audio_energy/scorer.py.

    Returns:
        (rms, times): both 1D numpy arrays of equal length.
    """
    try:
        audio, _ = librosa.load(audio_path, sr=target_sr, mono=True)
    except Exception:
        logger.exception("Failed to load audio %s", audio_path)
        return np.zeros(100, dtype=np.float32), np.zeros(100, dtype=np.float64)

    # Convert frame duration from ms to samples
    frame_length = int(target_sr * frame_duration_ms / 1000)
    hop_length = frame_length // 2   # 50% overlap

    rms = librosa.feature.rms(
        y=audio,
        frame_length=frame_length,
        hop_length=hop_length
    )[0]   # shape: (num_frames,)

    times = librosa.frames_to_time(
        np.arange(len(rms)), sr=target_sr, hop_length=hop_length
    )

    return rms.astype(np.float32), times
