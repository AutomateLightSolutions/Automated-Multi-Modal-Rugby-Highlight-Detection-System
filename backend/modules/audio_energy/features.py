"""
78-dimensional feature extraction for the audio_energy event/highlight
models. Exact feature order (and the shared-STFT computation) matches the
models' training pipeline — both are load-bearing: the models take a plain
positional vector, not named features, and reordering silently produces
garbage predictions.

Feature order:
    1.  rms_mean, rms_std                              (2)
    2.  zcr_mean, zcr_std                               (2)
    3.  spectral_centroid_mean, spectral_centroid_std   (2)
    4.  spectral_bandwidth_mean, spectral_bandwidth_std (2)
    5.  spectral_rolloff_mean, spectral_rolloff_std     (2)
    6.  spectral_contrast_band{0..6}_mean               (7)
    7.  spectral_contrast_band{0..6}_std                (7)
    8.  spectral_flatness_mean, spectral_flatness_std   (2)
    9.  mfcc{1..13}_mean                                (13)
    10. mfcc{1..13}_std                                 (13)
    11. delta_mfcc{1..13}_mean                          (13)
    12. delta_mfcc{1..13}_std                           (13)
                                                  Total = 78
"""
import logging

import librosa
import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 22050
N_FFT = 2048
HOP_LENGTH = 512
N_MFCC = 13

FEATURE_DIM = 78


def _mean_std(x: np.ndarray) -> tuple[float, float]:
    return float(np.mean(x)), float(np.std(x))


def extract_features(y: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray | None:
    """
    Extract the 78-dim feature vector for one audio chunk.

    Returns None — never a zero vector — if the chunk is empty/silent or
    extraction raises; callers must skip such chunks rather than feed zeros
    to the model.
    """
    if y is None or len(y) == 0 or not np.any(y):
        return None

    try:
        # Magnitude spectrogram, shared by every spectral feature below —
        # computing it once instead of per-feature is the main cost saving.
        S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH))

        values: list[float] = []

        rms = librosa.feature.rms(S=S)[0]
        values.extend(_mean_std(rms))

        zcr = librosa.feature.zero_crossing_rate(y=y, frame_length=N_FFT, hop_length=HOP_LENGTH)[0]
        values.extend(_mean_std(zcr))

        centroid = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
        values.extend(_mean_std(centroid))

        bandwidth = librosa.feature.spectral_bandwidth(S=S, sr=sr)[0]
        values.extend(_mean_std(bandwidth))

        rolloff = librosa.feature.spectral_rolloff(S=S, sr=sr)[0]
        values.extend(_mean_std(rolloff))

        contrast = librosa.feature.spectral_contrast(S=S, sr=sr)  # (7, n_frames): bands 0..6
        for band in contrast:
            values.append(float(np.mean(band)))
        for band in contrast:
            values.append(float(np.std(band)))

        flatness = librosa.feature.spectral_flatness(S=S)[0]
        values.extend(_mean_std(flatness))

        mel_power = librosa.feature.melspectrogram(S=S ** 2, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
        mfcc = librosa.feature.mfcc(S=librosa.power_to_db(mel_power), sr=sr, n_mfcc=N_MFCC)
        delta_mfcc = librosa.feature.delta(mfcc)

        for coeff in mfcc:
            values.append(float(np.mean(coeff)))
        for coeff in mfcc:
            values.append(float(np.std(coeff)))
        for coeff in delta_mfcc:
            values.append(float(np.mean(coeff)))
        for coeff in delta_mfcc:
            values.append(float(np.std(coeff)))

        vector = np.nan_to_num(np.array(values, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)

        if vector.shape[0] != FEATURE_DIM:
            logger.error("Feature vector has %d dims, expected %d", vector.shape[0], FEATURE_DIM)
            return None

        return vector
    except Exception:
        logger.exception("Feature extraction failed for a chunk")
        return None
