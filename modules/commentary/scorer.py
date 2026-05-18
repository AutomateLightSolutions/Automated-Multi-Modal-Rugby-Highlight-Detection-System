"""
Transcribes audio and scores commentary for highlight relevance.
Placeholder — replace with real ASR + keyword/sentiment scoring.
"""


def run_inference(
    audio_path: str,
    global_start_sec: float,
    global_end_sec: float,
) -> dict:
    """
    Returns:
        confidence  — highlight probability derived from commentary [0, 1]
        event_type  — inferred event type from transcript or None
        extra_data  — transcript text and intermediate scores
    """
    return {
        "confidence": 0.0,
        "event_type": None,
        "extra_data": {"audio_path": audio_path, "start": global_start_sec, "end": global_end_sec},
    }
