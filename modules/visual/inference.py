"""
Visual module inference interface.

STUB BEHAVIOUR (current):
- Reads frame count from video using ffprobe
- Generates random excitement scores per frame using Beta(2,5) distribution
- Randomly assigns event_type weighted toward "none"
- Returns peak excitement as confidence

HOW TO REPLACE WITH REAL MODEL:
1. Load model once at module level (singleton pattern below)
2. In run_inference(), extract frames with OpenCV
3. Preprocess: resize to model input size, normalize, stack into tensor
4. Run model forward pass with torch.no_grad()
5. Aggregate frame-level scores with temporal max pooling
6. Apply softmax to event_logits → event_confidence
7. Replace the stub return values with real model outputs
"""

import random
import logging
import subprocess
import json
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model singleton — loaded once when the Celery worker starts
# Uncomment when replacing stub with real model:
#
# import torch
# from config import settings
# from modules.visual.model import EVENT_CLASSES, RugbyVisualClassifier
# _model = None
#
# def _get_model():
#     global _model
#     if _model is None:
#         weights_path = settings.MODEL_WEIGHTS_PATH / "visual" / "rugby_action_classifier.pth"
#         _model = RugbyVisualClassifier(num_classes=len(EVENT_CLASSES))
#         _model.load_state_dict(torch.load(weights_path, map_location="cpu"))
#         _model.eval()
#         logger.info(f"Visual model loaded from {weights_path}")
#     return _model
# ---------------------------------------------------------------------------


def _get_frame_count(video_path: str) -> int:
    """Use ffprobe to count frames without decoding the entire video."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "v:0",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 25 * 30  # fallback: assume 25fps × 30sec
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if streams:
        nb_frames = streams[0].get("nb_frames")
        if nb_frames:
            return int(nb_frames)
    return 25 * 30


def run_inference(video_path: str, global_start_sec: float,
                  global_end_sec: float) -> dict:
    """
    Run visual analysis on a video chunk.

    Args:
        video_path: path to the video chunk file
        global_start_sec: absolute start time in the full match (seconds)
        global_end_sec: absolute end time in the full match (seconds)

    Returns:
        Module output dict conforming to the system contract.
    """
    # --- STUB IMPLEMENTATION ---
    # Replace everything below with real model inference.

    num_frames = _get_frame_count(video_path)

    # Simulate per-frame excitement scores
    rng = np.random.default_rng()
    frame_scores = rng.beta(a=2, b=5, size=num_frames).astype(float)
    # Beta(2,5) gives realistic distribution: mostly low scores,
    # occasional spikes — more realistic than uniform random.

    peak_confidence = float(np.max(frame_scores))
    mean_confidence = float(np.mean(frame_scores))

    # Simulate event detection (weighted toward "none")
    event_weights = {
        "none": 0.70, "scrum": 0.07, "try": 0.04,
        "lineout": 0.05, "tackle": 0.05, "penalty": 0.03,
        "conversion": 0.02, "kick": 0.02,
        "breakdown": 0.01, "ruck": 0.01
    }
    event_type = random.choices(
        list(event_weights.keys()),
        weights=list(event_weights.values())
    )[0]

    if event_type == "none":
        event_type = None
        event_confidence = None
    else:
        event_confidence = round(random.uniform(0.55, 0.95), 4)

    return {
        "segment_id": None,  # set by the calling task
        "module": "visual",
        "global_start_sec": global_start_sec,
        "global_end_sec": global_end_sec,
        "confidence": round(peak_confidence, 4),
        "event_type": event_type,
        "event_confidence": event_confidence,
        "extra_data": {
            "mean_confidence": round(mean_confidence, 4),
            "num_frames_processed": num_frames
        }
    }
