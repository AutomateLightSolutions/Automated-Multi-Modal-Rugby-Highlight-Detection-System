"""
Runs inference on a video chunk and returns a highlight confidence dict.
Placeholder — replace with real model inference (e.g. TimeSformer, VideoMAE).
"""


def run_inference(
    video_path: str,
    global_start_sec: float,
    global_end_sec: float,
) -> dict:
    """
    Returns:
        confidence      — overall highlight probability [0, 1]
        event_type      — detected rugby event label or None
        event_confidence — confidence of the event classification [0, 1] or None
        extra_data      — arbitrary metadata dict for debugging
    """
    return {
        "confidence": 0.0,
        "event_type": None,
        "event_confidence": None,
        "extra_data": {"video_path": video_path, "start": global_start_sec, "end": global_end_sec},
    }
