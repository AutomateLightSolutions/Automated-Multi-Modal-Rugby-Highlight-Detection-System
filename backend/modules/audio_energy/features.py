"""
78-dimensional feature extraction for the audio_energy event/highlight
models — ported line-for-line from the training pipeline's
feature_extraction.py so inference features match training exactly (the
models are extremely sensitive to this: e.g. computing RMS/MFCC from the
shared STFT instead of the raw waveform, or skipping the per-frame
nan_to_num on spectral_contrast before averaging, silently produces
features tens of standard deviations outside the trained scaler's range and
collapses the classifier to one constant prediction).

Only the entry point differs from the training pipeline: this project has
no on-disk per-chunk WAV files (each match has one full audio track), so
extract_features() takes an already-loaded waveform slice instead of a
chunk path.

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


def compute_spectrum(y: np.ndarray) -> np.ndarray:
    """Magnitude STFT — shared by the spectral (not time-domain/cepstral) features below."""
    return np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH))


def _extract_rms(y: np.ndarray) -> np.ndarray:
    rms = librosa.feature.rms(y=y, hop_length=HOP_LENGTH)[0]
    return np.array([np.mean(rms), np.std(rms)])


def _extract_zcr(y: np.ndarray) -> np.ndarray:
    zcr = librosa.feature.zero_crossing_rate(y, hop_length=HOP_LENGTH)[0]
    return np.array([np.mean(zcr), np.std(zcr)])


def _extract_spectral_centroid(S: np.ndarray, sr: int) -> np.ndarray:
    centroid = librosa.feature.spectral_centroid(S=S, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)[0]
    return np.array([np.mean(centroid), np.std(centroid)])


def _extract_spectral_bandwidth(S: np.ndarray, sr: int) -> np.ndarray:
    bandwidth = librosa.feature.spectral_bandwidth(S=S, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)[0]
    return np.array([np.mean(bandwidth), np.std(bandwidth)])


def _extract_spectral_rolloff(S: np.ndarray, sr: int) -> np.ndarray:
    rolloff = librosa.feature.spectral_rolloff(S=S, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)[0]
    return np.array([np.mean(rolloff), np.std(rolloff)])


def _extract_spectral_contrast(S: np.ndarray, sr: int) -> np.ndarray:
    contrast = librosa.feature.spectral_contrast(S=S, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
    contrast = np.nan_to_num(contrast)  # must happen before averaging, not just at the end
    return np.concatenate([np.mean(contrast, axis=1), np.std(contrast, axis=1)])


def _extract_spectral_flatness(S: np.ndarray) -> np.ndarray:
    flatness = librosa.feature.spectral_flatness(S=S, n_fft=N_FFT, hop_length=HOP_LENGTH)[0]
    return np.array([np.mean(flatness), np.std(flatness)])


def _delta_width(n_frames: int) -> int:
    """Largest odd window <= 9 that librosa.feature.delta can use for n_frames."""
    width = min(9, n_frames if n_frames % 2 == 1 else n_frames - 1)
    return max(width, 3)


def _extract_mfccs(mfccs: np.ndarray) -> np.ndarray:
    return np.concatenate([np.mean(mfccs, axis=1), np.std(mfccs, axis=1)])


def _extract_delta_mfccs(mfccs: np.ndarray) -> np.ndarray:
    n_frames = mfccs.shape[1]
    if n_frames < 3:
        delta = np.zeros_like(mfccs)
    else:
        delta = librosa.feature.delta(mfccs, width=_delta_width(n_frames))
    return np.concatenate([np.mean(delta, axis=1), np.std(delta, axis=1)])


def extract_features(y: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray | None:
    """
    Extract the 78-dim feature vector for one audio chunk (an in-memory
    waveform slice — this pipeline has no on-disk per-chunk files).

    Returns None — never a zero vector — if the chunk is empty/silent or
    extraction raises; callers must skip such chunks rather than feed zeros
    to the model.
    """
    if y is None or len(y) == 0 or not np.any(y):
        return None

    try:
        S = compute_spectrum(y)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC, n_fft=N_FFT, hop_length=HOP_LENGTH)

        feature_vector = np.concatenate([
            _extract_rms(y),
            _extract_zcr(y),
            _extract_spectral_centroid(S, sr),
            _extract_spectral_bandwidth(S, sr),
            _extract_spectral_rolloff(S, sr),
            _extract_spectral_contrast(S, sr),
            _extract_spectral_flatness(S),
            _extract_mfccs(mfccs),
            _extract_delta_mfccs(mfccs),
        ])

        feature_vector = np.nan_to_num(feature_vector, nan=0.0, posinf=0.0, neginf=0.0)

        if feature_vector.shape[0] != FEATURE_DIM:
            logger.error("Feature vector has %d dims, expected %d", feature_vector.shape[0], FEATURE_DIM)
            return None

        return feature_vector
    except Exception:
        logger.exception("Feature extraction failed for a chunk")
        return None
