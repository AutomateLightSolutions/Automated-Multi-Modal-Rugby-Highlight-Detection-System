"""
Converts audio energy / crowd-noise features into a highlight score per chunk.
Placeholder — replace with real signal-processing / spectral feature extraction.
"""


def run_inference(
    audio_path: str,
    global_start_sec: float,
    global_end_sec: float,
) -> dict:
    """
    Returns:
        confidence  — highlight probability derived from audio energy [0, 1]
        extra_data  — RMS, spectral centroid, or other extracted features
    """
    return {
        "confidence": 0.0,
        "extra_data": {"audio_path": audio_path, "start": global_start_sec, "end": global_end_sec},
    }
