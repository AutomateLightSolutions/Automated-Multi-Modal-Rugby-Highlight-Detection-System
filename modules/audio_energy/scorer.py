"""
Audio energy excitement scorer.
confidence = energy excitement level of this segment (0.0 to 1.0)
event_type = None (audio energy cannot classify specific events)
event_confidence = None (audio energy does not classify events)
"""

import numpy as np
import logging
from modules.audio_energy.extractor import extract_rms_energy

logger = logging.getLogger(__name__)


def run_inference(audio_path: str, global_start_sec: float,
                  global_end_sec: float) -> dict:
    """
    Score audio energy excitement for a single audio chunk.
    Uses 90th percentile RMS energy as the confidence score
    (more robust than mean — avoids being dragged down by silence).
    """
    rms = extract_rms_energy(audio_path)

    if len(rms) == 0 or rms.max() == 0:
        confidence = 0.0
        peak_rms = 0.0
        peak_time_global = global_start_sec
    else:
        # Normalize to [0, 1]
        rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-8)

        # 90th percentile — more robust than peak for noisy audio
        confidence = float(np.percentile(rms_norm, 90))

        peak_frame = int(np.argmax(rms_norm))
        segment_duration = global_end_sec - global_start_sec
        peak_offset = (peak_frame / len(rms_norm)) * segment_duration
        peak_time_global = global_start_sec + peak_offset
        peak_rms = float(rms[peak_frame])

    return {
        "segment_id": None,
        "module": "audio_energy",
        "global_start_sec": global_start_sec,
        "global_end_sec": global_end_sec,
        "confidence": round(confidence, 4),
        "event_type": None,            # audio energy never sets this
        "event_confidence": None,      # audio energy never sets this
        "extra_data": {
            "peak_rms": round(peak_rms, 6),
            "peak_time_global_sec": round(peak_time_global, 3),
            "num_frames_analysed": len(rms)
        }
    }
